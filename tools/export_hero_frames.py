"""Write art/hero_big/<frame>.png for the big hero's 1.5x copies (patches/020_hero_big_art.py: the idle fidget, the
ocarina, burning in lava; the throws, which until there's a PNG use stand-in poses) - the copy as drawn now, with MARGIN pixels round its main block, in its palette's
colours - the starting point for redrawing it. Leaves an existing file alone unless --force.

    python3 tools/export_hero_frames.py [134 188 ...] [--force]      (no frames: all of them)

References - a big animation's frames as they are (never read by the build), as art/hero_big/ref_<name>_<frame>.png:

    python3 tools/export_hero_frames.py --ref stand 0       (the small hero's animation number: 0 standing,
                                                             0x10 ducking, 0x33 knocked out)
"""
import importlib.util
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import hackbuild as h  # noqa: E402
from png_tiles import neo_to_rgb, write_indexed  # noqa: E402

spec = importlib.util.spec_from_file_location("hero_big_art", os.path.join(ROOT, "patches", "020_hero_big_art.py"))
hb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hb)


def frames(rom):
    """The frames drawn as 1.5x copies, by animation."""
    out, q = [], rom.u32(hb.ANIM_TABLE + 4 * hb.FIDGET_ANIM)
    while rom.u16(q) < 0xFFFE:
        w = rom.u16(q)
        if w < 0x8000 and (w & 0x3FFC) < hb.NORMAL_FRAMES and (w & 0x3FFC) not in out:
            out.append(w & 0x3FFC)
        q += 4 if w >= 0x8000 else 2
    out += hb.OCARINA_FRAMES
    out += sorted(set(hb.THROW_ART.values())) + [hb.THROW_MID]   # (the throws' drawings and the in-between)
    for n in hb.BURN_ANIMS:
        p, i = rom.u32(hb.ANIM_TABLE + 4 * n), 0
        while rom.u16(p + 2 * i) < 0xFFFE:
            if rom.u16(p + 2 * i) not in out:
                out.append(rom.u16(p + 2 * i))
            i += 1
    return out


def write(out, src, palette, cols, rows):
    m = hb.MARGIN
    px = [[0] * (cols * 16 + 2 * m) for _ in range(rows * 16 + 2 * m)]
    for (x, y), v in src.items():
        if 0 <= x + m < cols * 16 + 2 * m and 0 <= y + m < rows * 16 + 2 * m:
            px[y + m][x + m] = v
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write_indexed(out, px, [neo_to_rgb(int(w, 16)) for w in hb.PALETTE_COLOURS.get(palette, hb.PALETTE_COLOURS[0x10])
                            .split()])
    print("wrote %s (%dx%d)" % (os.path.relpath(out, ROOT), len(px[0]), len(px)))


def references(rom, name, anim):
    """The big form's version of small animation `anim`, each frame as it is."""
    p, i, done = rom.u32(hb.ANIM_TABLE + 4 * (anim + hb.BIG_SET)), 0, []
    while rom.u16(p + 2 * i) < 0xFFFE:
        w = rom.u16(p + 2 * i)
        i += 1 if w < 0x8000 else 2
        if w >= 0x8000 or (w & 0x3FFC) in done:
            continue
        frame = w & 0x3FFC
        done.append(frame)
        src, palette = hb.frame_pixels(rom, frame)
        q = rom.u32(h.FRAME_TABLE + frame)
        write(os.path.join(ROOT, "art/hero_big/ref_%s_%03X.png" % (name, frame)), src, palette, rom.data[q] + 1,
              rom.data[q + 1] + 1)


def main():
    z = zipfile.ZipFile(h.ORIG_ZIP)
    entries = [(i, z.read(i)) for i in z.infolist()]
    p1 = next(d for i, d in entries if i.filename == h.P1_NAME)
    s1 = next(d for i, d in entries if i.filename == h.S1_NAME)
    rom = h.Rom(h.swap_pairs(p1), s1, {i.filename: d for i, d in entries if i.filename in h.C_NAMES})
    if "--ref" in sys.argv:
        k = sys.argv.index("--ref")
        return references(rom, sys.argv[k + 1], int(sys.argv[k + 2], 0))
    wanted = [int(a, 16) for a in sys.argv[1:] if not a.startswith("--")] or frames(rom)
    for frame in wanted:
        out = os.path.join(ROOT, hb.ART % frame)
        if os.path.exists(out) and "--force" not in sys.argv:
            print("%s exists (--force to overwrite)" % (hb.ART % frame))
            continue
        # (the in-between: no art of its own - it starts as the wind-up)
        write(out, *hb.upscaled_pixels(rom, hb.THROW_ART[0xB0] if frame == hb.THROW_MID else frame))


if __name__ == "__main__":
    main()
