#!/usr/bin/env python3
"""Find colour writes made while the picture is drawn: replay the recorded tests and list who writes palette RAM on
the picture's lines.

    python3 tools/palette_timing.py                 build, then replay every test in tests/clips.txt
    python3 tools/palette_timing.py round_clear     just those tests
    python3 tools/palette_timing.py --no-build      use the build that's there

On the real Neo Geo the CPU has priority over the video chip for palette RAM, so a colour written while a line is
drawn puts that colour on screen for a pixel or more: short 1-pixel streaks that jump about from frame to frame.
MAME doesn't show them. Colours should be written in the vblank (lines -24 to 15 here; the picture is 16-239).

Each writer is listed by its PC with what it is: the build log's description of the patch code it's in, or "the
game" for the original code. Only writers seen on the picture's lines are listed.
"""
import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "palette_timing"
ORIGINAL_END = 0xB69A0           # new code starts here (see tools/hackbuild.py)


def build():
    """Build the hack; its new code blocks come back as (start, size, what it is)."""
    run = subprocess.run([sys.executable, "tools/hackbuild.py"], cwd=ROOT, capture_output=True, text=True)
    log = run.stdout + run.stderr
    if run.returncode or "Built build/aes/" not in log:
        print(log[-2000:])
        sys.exit("build failed")
    (OUT / "build.log").write_text(log)


def code_blocks():
    blocks = []
    for line in (OUT / "build.log").read_text().splitlines():
        m = re.match(r"\s+0x([0-9A-F]{6})\s+(\d+) byte\(s\) of new code\s+(.*)", line)
        if m:
            blocks.append((int(m.group(1), 16), int(m.group(2)), m.group(3).strip()))
    return blocks


def play(name, save):
    out = OUT / (name + ".txt")
    out.unlink(missing_ok=True)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PALETTE_TIMING_OUT=str(out))
    subprocess.run(["mame", "aes", "-hash", "build/aes", "-rompath", "build/aes", "-cart", "bjourney", "-state", save,
                    "-window", "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-noautosave",
                    "-cfg_directory", str(OUT / "cfg"), "-nvram_directory", str(OUT / "nvram"),
                    "-input_directory", "tests/clips", "-playback", name + ".inp", "-exit_after_playback",
                    "-autoboot_script", "tools/palette_timing.lua"], cwd=ROOT, env=env, capture_output=True)
    return name, out.read_text().splitlines() if out.exists() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="tests' names (default: all of them)")
    ap.add_argument("--no-build", action="store_true", help="don't rebuild first")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    args = ap.parse_args()

    tests = {}
    for line in (ROOT / "tests" / "clips.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, save = line.split()[:2]
            if (ROOT / "tests" / "clips" / (name + ".inp")).exists():
                tests[name] = save
    names = args.names or sorted(tests)
    missing = [n for n in names if n not in tests]
    if missing:
        sys.exit("no such test: " + ", ".join(missing))
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.no_build or not (OUT / "build.log").exists():
        build()
    blocks = code_blocks()

    writers, failed = {}, []
    with ThreadPoolExecutor(args.jobs) as pool:
        for name, lines in pool.map(lambda n: play(n, tests[n]), names):
            if lines is None:
                failed.append(name)
                continue
            for line in lines:
                pc, n, seen, first, last = (int(v, 16) if i == 0 else int(v) for i, v in enumerate(line.split()))
                w = writers.setdefault(pc, [0, 0, first, last, set()])
                w[0] += n
                w[1] += seen
                w[2], w[3] = min(w[2], first), max(w[3], last)
                if seen:
                    w[4].add(name)

    shown = [pc for pc in sorted(writers) if writers[pc][1]]
    for pc in shown:
        n, seen, first, last, where = writers[pc]
        what = "the game" if pc < ORIGINAL_END else next(
            (why for at, size, why in blocks if at <= pc < at + size), "?")
        print("%06X  %6d of %6d on the picture, lines %4d to %3d  %s" % (pc, seen, n, first, last, what))
        print("        in: " + ", ".join(sorted(where)))
    print("%d tests, %d writers on the picture's lines%s" % (
        len(names) - len(failed), len(shown), "; no log from: " + ", ".join(failed) if failed else ""))
    return 1 if shown or failed else 0


if __name__ == "__main__":
    sys.exit(main())
