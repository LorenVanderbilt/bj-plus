#!/usr/bin/env python3
"""Build a patched Blue's Journey ROM set for MAME from roms/bjourney.zip plus patches/*.py.

    tools/hackbuild.py                     apply every patch in patches/
    tools/hackbuild.py --only anim-speed   apply just the named patch(es)
    tools/hackbuild.py --skip anim-speed   apply everything except the named patch(es)
    tools/hackbuild.py --list              list the available patches

Output goes to build/roms/ (bjourney.zip = the patched game, neogeo.zip = the BIOS), which
run.sh points MAME at. The original roms/ folder is never modified.

A patch is a Python file in patches/ defining NAME, DESCRIPTION and apply(rom). `rom` is a Rom
(below) holding the program ROM in normal 68000 byte order; patches change it with rom.write(),
and add new code with rom.place_code(), which assembles it into unused space at the end of the ROM.
"""
import argparse, glob, importlib.util, os, shutil, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_ZIP = os.path.join(ROOT, "roms", "bjourney.zip")
OUT_DIR = os.path.join(ROOT, "build", "roms")
P1_NAME = "022-p1.p1"
# The program ROM ends in ~300KB of unused 0xFF bytes starting at 0xB69A0; new code goes here.
FREE_START = 0xB6A00
AS, LD, OBJCOPY = "m68k-neogeo-elf-as", "m68k-neogeo-elf-ld", "m68k-neogeo-elf-objcopy"


def swap_pairs(b):
    """The .p1 file stores every 16-bit word byte-swapped; this converts either direction."""
    out = bytearray(len(b))
    out[0::2], out[1::2] = b[1::2], b[0::2]
    return bytes(out)


class Rom:
    def __init__(self, data):
        self.data = bytearray(data)
        self.orig = bytes(data)
        self.next_free = FREE_START
        self.log = []

    def u16(self, addr): return int.from_bytes(self.data[addr:addr + 2], "big")
    def u32(self, addr): return int.from_bytes(self.data[addr:addr + 4], "big")

    def write(self, addr, new, expect=None, why=""):
        """Overwrite bytes at addr. expect= is the bytes that must be there now, so a patch
        that no longer matches the ROM fails loudly instead of corrupting it."""
        new = bytes(new)
        if expect is not None and bytes(self.data[addr:addr + len(expect)]) != bytes(expect):
            raise SystemExit("patch mismatch at 0x%X: expected %s, found %s" % (
                addr, bytes(expect).hex(), bytes(self.data[addr:addr + len(expect)]).hex()))
        self.data[addr:addr + len(new)] = new
        self.log.append("  0x%06X  %d byte(s)  %s" % (addr, len(new), why))

    def alloc(self, size, align=2):
        addr = (self.next_free + align - 1) & ~(align - 1)
        end = addr + size
        if end > len(self.data) or any(b != 0xFF for b in self.orig[addr:end]):
            raise SystemExit("out of free space in the program ROM")
        self.next_free = end
        return addr

    def _assemble(self, source, origin):
        with tempfile.TemporaryDirectory() as d:
            s, o, e, b = (os.path.join(d, n) for n in ("a.s", "a.o", "a.elf", "a.bin"))
            open(s, "w").write(source + "\n")
            subprocess.run([AS, "-m68000", "-o", o, s], check=True)
            subprocess.run([LD, "-e", "0", "-Ttext=0x%X" % origin, "-o", e, o], check=True)
            subprocess.run([OBJCOPY, "-O", "binary", "-j", ".text", e, b], check=True)
            return open(b, "rb").read()

    def place_code(self, source, why=""):
        """Assemble 68000 source into free space and return the address it was placed at."""
        # Assemble at the address it will actually live at: the assembler's output size can differ
        # with the address (branch/immediate sizes), so sizing it at address 0 is not reliable.
        addr = (self.next_free + 1) & ~1
        code = self._assemble(source, addr)
        size = len(code)
        assert self.alloc(size) == addr
        self.data[addr:addr + size] = code
        self.log.append("  0x%06X  %d byte(s) of new code  %s" % (addr, size, why))
        return addr

    def patched_p1_file(self):
        return swap_pairs(bytes(self.data))


def load_patches():
    found = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "patches", "*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        found[mod.NAME] = mod
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", metavar="NAME", help="apply only these patches")
    ap.add_argument("--skip", nargs="+", metavar="NAME", default=[], help="apply all but these patches")
    ap.add_argument("--list", action="store_true", help="list available patches and exit")
    args = ap.parse_args()

    patches = load_patches()
    if args.list:
        for name, m in patches.items():
            print("%-16s %s" % (name, m.DESCRIPTION))
        return
    for n in (args.only or []) + args.skip:
        if n not in patches:
            raise SystemExit("unknown patch %r (see --list)" % n)
    chosen = [n for n in patches if (not args.only or n in args.only) and n not in args.skip]

    if not os.path.exists(ORIG_ZIP):
        raise SystemExit("missing %s - put your bjourney.zip in roms/" % ORIG_ZIP)
    with zipfile.ZipFile(ORIG_ZIP) as z:
        entries = [(i, z.read(i)) for i in z.infolist()]
    p1 = next(d for i, d in entries if i.filename == P1_NAME)
    rom = Rom(swap_pairs(p1))

    print("Applying %d patch(es): %s" % (len(chosen), ", ".join(chosen) or "(none)"))
    for n in chosen:
        print("* %s - %s" % (n, patches[n].DESCRIPTION))
        patches[n].apply(rom)
    for line in rom.log:
        print(line)

    os.makedirs(OUT_DIR, exist_ok=True)
    with zipfile.ZipFile(os.path.join(OUT_DIR, "bjourney.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in entries:
            z.writestr(info.filename, rom.patched_p1_file() if info.filename == P1_NAME else data)
    shutil.copy(os.path.join(ROOT, "roms", "neogeo.zip"), os.path.join(OUT_DIR, "neogeo.zip"))
    print("Built build/roms/bjourney.zip")


if __name__ == "__main__":
    main()
