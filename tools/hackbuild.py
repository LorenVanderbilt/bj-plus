#!/usr/bin/env python3
"""Build a patched Blue's Journey ROM set for MAME from roms/bjourney.zip plus patches/*.py.

    tools/hackbuild.py                     apply every patch in patches/
    tools/hackbuild.py --only anim-speed   apply just the named patch(es)
    tools/hackbuild.py --skip anim-speed   apply everything except the named patch(es)
    tools/hackbuild.py --list              list the available patches

Output goes to build/roms/ (the arcade/MVS machine: bjourney.zip = the patched game, neogeo.zip =
the BIOS) and build/aes/ (the home-console machine: the game as a cartridge plus a software-list
file, and roms/aes.zip as the BIOS), which run.sh points MAME at. roms/ is never modified.

roms/aes.zip is ngdevkit's open-source AES BIOS (copied from any ngdevkit example's build/rom/aes.zip);
the official AES BIOS is not needed. Without it only the arcade build is produced.

A patch is a Python file in patches/ defining NAME, DESCRIPTION and apply(rom). `rom` is a Rom
(below) holding the program ROM in normal 68000 byte order; patches change it with rom.write(),
and add new code with rom.place_code(), which assembles it into unused space at the end of the ROM.
rom.add_fix_tile() adds an 8x8 tile to the fix-layer ROM (022-s1.s1) in the next free slot of a run that is
blank in the original and never drawn by the game (0x2FC-0x3FF) and returns its tile number.
"""
import argparse, glob, hashlib, importlib.util, os, shutil, subprocess, sys, tempfile, zipfile, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_ZIP = os.path.join(ROOT, "roms", "bjourney.zip")
OUT_DIR = os.path.join(ROOT, "build", "roms")
AES_DIR = os.path.join(ROOT, "build", "aes")
P1_NAME = "022-p1.p1"
S1_NAME = "022-s1.s1"
# The program ROM ends in ~300KB of unused 0xFF bytes starting at 0xB69A0; new code goes here.
FREE_START = 0xB6A00
# Fix tiles 0x2FC-0x3FF are blank in the S ROM and never drawn by the game (checked by watching every fix-layer
# write through the attract cycle, gameplay and the shop); new fix tiles go here.
FIX_FREE_START, FIX_FREE_END = 0x2FC, 0x3FF
AS, LD, OBJCOPY = "m68k-neogeo-elf-as", "m68k-neogeo-elf-ld", "m68k-neogeo-elf-objcopy"


def swap_pairs(b):
    """The .p1 file stores every 16-bit word byte-swapped; this converts either direction."""
    out = bytearray(len(b))
    out[0::2], out[1::2] = b[1::2], b[0::2]
    return bytes(out)


class Rom:
    def __init__(self, data, fix=b""):
        self.data = bytearray(data)
        self.orig = bytes(data)
        self.fix = bytearray(fix)          # the fix-layer ROM (S ROM): 32 bytes per 8x8 tile, 4 bits per pixel
        self.fix_orig = bytes(fix)
        self.next_free = FREE_START
        self.next_fix_tile = FIX_FREE_START
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

    # Byte and nibble holding fix-tile pixel (x, y): columns 0-1 are in bytes 16-23, 2-3 in 24-31, 4-5 in
    # 0-7, 6-7 in 8-15 (one byte per row); the even column is the low nibble.
    FIX_COLUMN_BYTE = (16, 16, 24, 24, 0, 0, 8, 8)

    def put_fix_tile(self, index, pixels, why=""):
        """Store an 8x8 fix-layer tile (pixels[y][x] = color index 0-15, 0 = transparent) at tile number
        index. The slot must be blank (all zero) in the original S ROM."""
        at = index * 32
        if any(self.fix_orig[at:at + 32]):
            raise SystemExit("fix tile 0x%X is not blank in the original S ROM" % index)
        tile = bytearray(32)
        for y in range(8):
            for x in range(8):
                b = self.FIX_COLUMN_BYTE[x] + y
                tile[b] |= (pixels[y][x] & 15) << (0 if x % 2 == 0 else 4)
        self.fix[at:at + 32] = tile
        self.log.append("  fix 0x%03X  tile  %s" % (index, why))

    def add_fix_tile(self, pixels, why=""):
        """Store an 8x8 fix tile in the next free slot and return its tile number."""
        n = self.next_fix_tile
        if n > FIX_FREE_END:
            raise SystemExit("out of free fix tiles (0x%X-0x%X)" % (FIX_FREE_START, FIX_FREE_END))
        self.put_fix_tile(n, pixels, why)
        self.next_fix_tile = n + 1
        return n

    def patched_p1_file(self):
        return swap_pairs(bytes(self.data))

    def patched_files(self):
        """The ROM files this build changes: {file name: new contents}."""
        files = {P1_NAME: self.patched_p1_file()}
        if bytes(self.fix) != self.fix_orig:
            files[S1_NAME] = bytes(self.fix)
        return files


def write_aes_set(entries, patched):
    """Write build/aes/: the game as an AES cartridge (a MAME software-list entry) plus the BIOS."""
    src_bios = os.path.join(ROOT, "roms", "aes.zip")
    if not os.path.exists(src_bios):
        print("(no roms/aes.zip - skipping the AES build; copy one from an ngdevkit example's build/rom/)")
        return
    os.makedirs(AES_DIR, exist_ok=True)
    game = {}
    for info, data in entries:
        if info.filename.startswith("022-"):
            game[info.filename] = patched.get(info.filename, data)
    with zipfile.ZipFile(os.path.join(AES_DIR, "bjourney.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(game.items()):
            z.writestr(name, data)

    def rom(name, offset, flag=None):
        d = game[name]
        fl = ' loadflag="%s"' % flag if flag else ""
        return ('\t\t\t\t<rom%s name="%s" offset="%s" size="0x%06x" crc="%08x" sha1="%s" />'
                % (fl, name, offset, len(d), zlib.crc32(d) & 0xFFFFFFFF, hashlib.sha1(d).hexdigest()))
    xml = """<?xml version="1.0"?>
<!DOCTYPE softwarelist SYSTEM "softwarelist.dtd">
<softwarelist name="neogeo" description="Neo-Geo cartridges">
\t<software name="bjourney">
\t\t<description>Blue's Journey / Raguy (hack)</description>
\t\t<year>1990</year>
\t\t<sharedfeat name="release" value="MVS,AES" />
\t\t<sharedfeat name="compatibility" value="MVS,AES" />
\t\t<publisher>Alpha Denshi</publisher>
\t\t<part name="cart" interface="neo_cart">
\t\t\t<dataarea name="maincpu" width="16" endianness="big" size="0x100000">
%s
\t\t\t</dataarea>
\t\t\t<dataarea name="fixed" size="0x20000">
%s
\t\t\t</dataarea>
\t\t\t<dataarea name="audiocpu" size="0x20000">
%s
\t\t\t</dataarea>
\t\t\t<dataarea name="ymsnd:adpcma" size="0x200000">
%s
%s
\t\t\t</dataarea>
\t\t\t<dataarea name="sprites" size="0x300000">
%s
%s
%s
%s
\t\t\t</dataarea>
\t\t</part>
\t</software>
</softwarelist>
""" % (rom("022-p1.p1", "0x000000", "load16_word_swap"), rom("022-s1.s1", "0x000000"), rom("022-m1.m1", "0x000000"),
       rom("022-v11.v11", "0x000000"), rom("022-v22.v22", "0x100000"),
       rom("022-c1.c1", "0x000000", "load16_byte"), rom("022-c2.c2", "0x000001", "load16_byte"),
       rom("022-c3.c3", "0x200000", "load16_byte"), rom("022-c4.c4", "0x200001", "load16_byte"))
    open(os.path.join(AES_DIR, "neogeo.xml"), "w").write(xml)
    shutil.copy(src_bios, os.path.join(AES_DIR, "aes.zip"))
    shutil.copy(os.path.join(ROOT, "roms", "neogeo.zip"), os.path.join(AES_DIR, "neogeo.zip"))
    print("Built build/aes/ (home-console set)")


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
    s1 = next(d for i, d in entries if i.filename == S1_NAME)
    rom = Rom(swap_pairs(p1), s1)

    print("Applying %d patch(es): %s" % (len(chosen), ", ".join(chosen) or "(none)"))
    for n in chosen:
        print("* %s - %s" % (n, patches[n].DESCRIPTION))
        patches[n].apply(rom)
    for line in rom.log:
        print(line)

    patched = rom.patched_files()
    os.makedirs(OUT_DIR, exist_ok=True)
    with zipfile.ZipFile(os.path.join(OUT_DIR, "bjourney.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in entries:
            z.writestr(info.filename, patched.get(info.filename, data))
    shutil.copy(os.path.join(ROOT, "roms", "neogeo.zip"), os.path.join(OUT_DIR, "neogeo.zip"))
    print("Built build/roms/bjourney.zip")
    write_aes_set(entries, patched)


if __name__ == "__main__":
    main()
