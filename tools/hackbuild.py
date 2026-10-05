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
blank in the original and never drawn by the game (0x2FC-0x31F, 0x360-0x3FF) and returns its tile number.
rom.add_sprite_tile() does the same for a 16x16 sprite tile in the sprite (C) ROMs (free run 0x2F9C-0x2FFF), and
rom.add_frame() adds a sprite frame (the definition the game draws an object's +8 frame number from) built
from such tiles, in a free frame number (0x3F00-0x3FFC), and returns that frame number.
"""
import argparse, glob, hashlib, importlib.util, os, shutil, subprocess, sys, tempfile, zipfile, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_ZIP = os.path.join(ROOT, "roms", "bjourney.zip")
OUT_DIR = os.path.join(ROOT, "build", "roms")
AES_DIR = os.path.join(ROOT, "build", "aes")
P1_NAME = "022-p1.p1"
S1_NAME = "022-s1.s1"
C_NAMES = ["022-c1.c1", "022-c2.c2", "022-c3.c3", "022-c4.c4"]
# The program ROM ends in ~300KB of unused 0xFF bytes starting at 0xB69A0; new code goes here.
FREE_START = 0xB6A00
# Fix tiles 0x2FC-0x3FF are the S ROM's only run of blank tiles; new fix tiles go here (watching every fix-layer
# write through the attract cycle - both BIOSes -, gameplay, the shop and NPC rooms, continue, game over and the
# memory card screens, the original game draws only 0x320 from it).
FIX_FREE_START, FIX_FREE_END = 0x2FC, 0x3FF
# ... except that the game's inline text routine (0x9FE6) draws character c as tile 0x300 + c until a string sets
# another base, so those "blank" tiles are drawn: 0x320 (a space) clears the continue screen's speech bubble.
# 0x320-0x35F (space, punctuation, digits, capitals at that base) stay untouched; new tiles use the rest.
FIX_FREE_RANGES = [(0x2FC, 0x31F), (0x360, 0x3FF)]
# Sprite tiles 0x2F9C-0x2FFF are blank in the C ROMs (the end of a bank), no frame definition uses them, and the
# game never writes them to the sprite tables (checked through the attract cycle and several levels).
SPRITE_FREE_START, SPRITE_FREE_END = 0x2F9C, 0x2FFF
# The sprite frame table (frame number / 4 -> definition address) ends in filler: frames 0x34D0-0x3FFC all point at
# one definition and nothing uses them. New frames go at the very end.
FRAME_TABLE = 0x60772
FRAME_FREE_START, FRAME_FREE_END = 0x3F00, 0x3FFC
AS, LD, OBJCOPY = "m68k-neogeo-elf-as", "m68k-neogeo-elf-ld", "m68k-neogeo-elf-objcopy"


def swap_pairs(b):
    """The .p1 file stores every 16-bit word byte-swapped; this converts either direction."""
    out = bytearray(len(b))
    out[0::2], out[1::2] = b[1::2], b[0::2]
    return bytes(out)


class Rom:
    def __init__(self, data, fix=b"", sprites=None):
        self.data = bytearray(data)
        self.orig = bytes(data)
        self.fix = bytearray(fix)          # the fix-layer ROM (S ROM): 32 bytes per 8x8 tile, 4 bits per pixel
        self.fix_orig = bytes(fix)
        # the sprite ROMs, {file name: contents}: c1/c2 hold tiles 0-0x3FFF, c3/c4 the rest
        self.sprites = {n: bytearray(d) for n, d in (sprites or {}).items()}
        self.sprites_orig = {n: bytes(d) for n, d in (sprites or {}).items()}
        self.next_free = FREE_START
        self.free_fix_tiles = [t for a, b in FIX_FREE_RANGES for t in range(a, b + 1)]
        self.next_sprite_tile = SPRITE_FREE_START
        self.tile_pool = []          # more free sprite tiles (tile-pool frees them), used after the range above
        self.next_frame = FRAME_FREE_START
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
        # 4-byte aligned: the linker aligns the code to 4 and would pad a 2-aligned start with a NOP,
        # shifting every label by 2 from what the caller expects.
        addr = (self.next_free + 3) & ~3
        code = self._assemble(source, addr)
        size = len(code)
        assert self.alloc(size, align=4) == addr
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
        if not self.free_fix_tiles:
            raise SystemExit("out of free fix tiles (%s)" % ", ".join("0x%X-0x%X" % r for r in FIX_FREE_RANGES))
        n = self.free_fix_tiles.pop(0)
        self.put_fix_tile(n, pixels, why)
        return n

    # A 16x16 sprite tile is 128 bytes, 64 in each ROM of its pair (c1/c2 for tiles 0-0x3FFF, c3/c4 above), in four
    # 8x8 blocks of 16 bytes: x 8-15 y 0-7, x 8-15 y 8-15, x 0-7 y 0-7, x 0-7 y 8-15. Each block row is 2 bytes in
    # each ROM - bitplanes 0 and 1 in the first ROM, 2 and 3 in the second - with bit x of a plane = pixel x.
    SPRITE_TILES_PER_PAIR = 0x4000

    def _sprite_at(self, index):
        if index < self.SPRITE_TILES_PER_PAIR:
            return C_NAMES[0], C_NAMES[1], index * 64
        return C_NAMES[2], C_NAMES[3], (index - self.SPRITE_TILES_PER_PAIR) * 64

    def sprite_tile(self, index):
        """The original 16x16 sprite tile at tile number index, as pixels[y][x] (color indices)."""
        a, b, at = self._sprite_at(index)
        A, B = self.sprites_orig[a], self.sprites_orig[b]
        px = [[0] * 16 for _ in range(16)]
        for blk in range(4):
            bx, by = (8 if blk < 2 else 0), (0 if blk % 2 == 0 else 8)
            for y in range(8):
                o = at + blk * 16 + y * 2
                p = (A[o], A[o + 1], B[o], B[o + 1])
                for x in range(8):
                    px[by + y][bx + x] = sum(((p[k] >> x) & 1) << k for k in range(4))
        return px

    def put_sprite_tile(self, index, pixels, why=""):
        """Store a 16x16 sprite tile (pixels[y][x] = color index 0-15, 0 = transparent) at tile number index.
        The slot must be blank in the original C ROMs."""
        a, b, at = self._sprite_at(index)
        if index not in getattr(self, "pooled", ()) and (any(self.sprites_orig[a][at:at + 64]) or
                                                         any(self.sprites_orig[b][at:at + 64])):
            raise SystemExit("sprite tile 0x%X is not blank in the original C ROMs" % index)
        for blk in range(4):
            bx, by = (8 if blk < 2 else 0), (0 if blk % 2 == 0 else 8)
            for y in range(8):
                planes = [0, 0, 0, 0]
                for x in range(8):
                    v = pixels[by + y][bx + x] & 15
                    for p in range(4):
                        planes[p] |= ((v >> p) & 1) << x
                o = at + blk * 16 + y * 2
                self.sprites[a][o:o + 2] = bytes(planes[0:2])
                self.sprites[b][o:o + 2] = bytes(planes[2:4])
        self.log.append("  sprite 0x%04X  tile  %s" % (index, why))

    def add_sprite_tile(self, pixels, why=""):
        """Store a 16x16 sprite tile in the next free slot and return its tile number."""
        n = self.next_sprite_tile
        if n > SPRITE_FREE_END:
            if not self.tile_pool:
                raise SystemExit("out of free sprite tiles (0x%X-0x%X, and the tile pool)" % (SPRITE_FREE_START,
                                                                                              SPRITE_FREE_END))
            n = self.tile_pool.pop(0)
            self.put_sprite_tile(n, pixels, why)
            return n
        self.put_sprite_tile(n, pixels, why)
        self.next_sprite_tile = n + 1
        return n

    def _frame_definition(self, tiles, palette):
        """The bytes of a frame definition in the per-tile form (see 0xA996): columns-1, rows-1, 0, palette, the tile
        number's high byte; then for each column top to bottom a byte: 0 = blank, else the tile number's low byte -
        or, when the high byte changes (or the low byte is 0 or 1), 1, 0x20, the new high byte, the low byte."""
        rows, cols = len(tiles), len(tiles[0])
        first = next(t for row in tiles for t in row if t is not None)
        if any(t is not None and t > 0xFFFF for row in tiles for t in row):
            raise SystemExit("frame definitions: tiles above 0xFFFF need the attribute bits")
        hi = first >> 8
        body = bytearray([cols - 1, rows - 1, 0, palette, hi])
        for c in range(cols):
            for r in range(rows):
                t = tiles[r][c]
                if t is None:
                    body.append(0)
                elif t >> 8 == hi and (t & 0xFF) > 1:
                    body.append(t & 0xFF)
                else:
                    hi = t >> 8
                    body += bytes([1, 0x20, hi, t & 0xFF])
        body.append(0xFF)
        return bytes(body)

    def frame_tiles(self, frame):
        """(tiles[row][col] or None, palette) of an original frame whose definition uses one palette and no flips."""
        p = self.u32(FRAME_TABLE + frame)
        cols, rows, mode, attr, hi = self.data[p:p + 5]
        cols, rows = cols + 1, rows + 1
        tiles = [[None] * cols for _ in range(rows)]
        q = p + 5
        for c in range(cols):
            for r in range(rows):
                b = self.data[q]
                q += 1
                if b == 0:
                    continue
                if b == 1:                   # 1, attribute, high byte, low byte: a new high byte (plain only)
                    if self.data[q] != 0x20:
                        raise SystemExit("frame_tiles: frame 0x%X uses per-tile attributes" % frame)
                    hi, b = self.data[q + 1], self.data[q + 2]
                    q += 3
                tiles[r][c] = (hi << 8) | b
        return tiles, attr

    def add_frame(self, tiles, palette, why=""):
        """Add a sprite frame: tiles[row][col] = a tile number or None (blank), drawn with palette (0-255) unless the
        object overrides it. Returns the new frame number (what the game stores in an object's +8)."""
        body = self._frame_definition(tiles, palette)
        addr = self.alloc(len(body))
        self.data[addr:addr + len(body)] = body
        n = self.next_frame
        if n > FRAME_FREE_END:
            raise SystemExit("out of free frame numbers")
        self.next_frame = n + 4
        self.write(FRAME_TABLE + n, addr.to_bytes(4, "big"), why="frame 0x%X -> new definition (%s)" % (n, why))
        self.log.append("  0x%06X  %d byte(s)  frame 0x%X definition: %s" % (addr, len(body), n, why))
        return n

    def replace_frame(self, frame, tiles, palette, why=""):
        """Point an existing frame number at a new definition built from tiles (as add_frame)."""
        body = self._frame_definition(tiles, palette)
        addr = self.alloc(len(body))
        self.data[addr:addr + len(body)] = body
        self.write(FRAME_TABLE + frame, addr.to_bytes(4, "big"), why="frame 0x%X -> new definition (%s)" % (frame, why))
        self.log.append("  0x%06X  %d byte(s)  frame 0x%X definition: %s" % (addr, len(body), frame, why))

    def patched_p1_file(self):
        return swap_pairs(bytes(self.data))

    def patched_files(self):
        """The ROM files this build changes: {file name: new contents}."""
        files = {P1_NAME: self.patched_p1_file()}
        if bytes(self.fix) != self.fix_orig:
            files[S1_NAME] = bytes(self.fix)
        for name, d in self.sprites.items():
            if bytes(d) != self.sprites_orig[name]:
                files[name] = bytes(d)
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
    rom = Rom(swap_pairs(p1), s1, {i.filename: d for i, d in entries if i.filename in C_NAMES})

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
