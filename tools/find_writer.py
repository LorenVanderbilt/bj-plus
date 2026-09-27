#!/usr/bin/env python3
"""Find the instruction that makes a RAM byte reach a given value while replaying a recording.

    tools/find_writer.py ADDR VALUE [--recording powerup.inp] [--context 40]

ADDR is a hex RAM address (e.g. 104022), VALUE the byte value it takes (decimal or 0x..).
It replays recordings/<name> in MAME with its GDB server enabled and drives the m68k gdb:
  pass 1 counts the game's vertical-blank handler (0x99A0) hits until the byte first equals VALUE,
  pass 2 replays again, stops one frame before, and single-steps until the byte changes,
  then prints the registers, the code around the writing instruction and the stack.
It takes a few minutes (MAME runs slowly with the debugger attached). Use the ORIGINAL rom
(./run.sh --skip <every patch>) so the recording stays in sync.
"""
import argparse, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GDB = "m68k-neogeo-elf-gdb"
PORT = 23946
VBLANK = 0x99A0   # the game's vertical-blank handler (see patches/010_anim_speed.py)


def start_mame(recording):
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    return subprocess.Popen(
        ["mame", "bjourney", "-rompath", os.path.join(ROOT, "build", "roms"), "-input_directory",
         os.path.join(ROOT, "recordings"), "-playback", recording, "-debug", "-debugger", "gdbstub",
         "-debugger_port", str(PORT), "-video", "none", "-sound", "none", "-nothrottle",
         "-seconds_to_run", "600", "-skip_gameinfo", "-noautosave"],
        env=env, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_gdb(script, done_marker, timeout=1500):
    path = "/tmp/find_writer_gdb.txt"
    open(path, "w").write("set pagination off\nset confirm off\nset architecture m68k\n"
                          "target remote localhost:%d\n%s\necho %s\\n\n" % (PORT, script, done_marker))
    out = open("/tmp/find_writer_out.txt", "w")
    g = subprocess.Popen([GDB, "-batch", "-x", path], stdout=out, stderr=subprocess.STDOUT)
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(3)
        text = open("/tmp/find_writer_out.txt").read()
        if done_marker in text or "Error in sourced" in text:
            break
    g.kill()
    return open("/tmp/find_writer_out.txt").read()


def session(recording, script, marker, timeout=1500):
    subprocess.run(["pkill", "-f", "mame bjourney"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    m = start_mame(recording)
    time.sleep(5)
    try:
        return run_gdb(script, marker, timeout)
    finally:
        m.kill()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("addr"); ap.add_argument("value")
    ap.add_argument("--recording", default="powerup.inp")
    ap.add_argument("--context", type=int, default=40, help="bytes of code to show before the write")
    a = ap.parse_args()
    addr, val = int(a.addr, 16), int(a.value, 0)
    cond = "*(unsigned char*)0x%x == %d" % (addr, val)

    print("Pass 1: counting frames until byte 0x%X == %d ..." % (addr, val))
    out = session(a.recording, """set $n = 0
break *0x%x
commands 1
  silent
  set $n = $n + 1
  if %s
    printf "FIRSTHIT %%d\\n", $n
  else
    continue
  end
end
continue""" % (VBLANK, cond), "DONE1")
    m = re.search(r"FIRSTHIT (\d+)", out)
    if not m:
        sys.exit("value never reached during the recording:\n" + out[-600:])
    n = int(m.group(1))
    print("  first seen at vblank #%d; single-stepping the frame before it ..." % n)

    out = session(a.recording, """break *0x%x
ignore 1 %d
continue
set $i = 0
set $prev = $pc
while !(%s) && $i < 800000
  set $prev = $pc
  stepi
  set $i = $i + 1
end
printf "\\n=== byte became %d after %%d steps; writing instruction at 0x%%x ===\\n", $i, $prev
info registers
echo \\n=== code before/at the write ===\\n
x/16i $prev-%d
echo \\n=== stack (return addresses) ===\\n
x/16xw $sp""" % (VBLANK, n - 3, cond, val, a.context), "DONE2", timeout=2400)
    i = out.find("=== byte became")
    print(out[i:] if i >= 0 else "did not find the write:\n" + out[-800:])


if __name__ == "__main__":
    main()
