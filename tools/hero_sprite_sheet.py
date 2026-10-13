"""Write docs/hero_sprites.png: every frame of the normal hero (0x000-0x18C, the numbers the animations use), as the
big hero draws it - the redrawn art (art/hero_big/<frame>.png) if there is one, else the big form's frame paired with
it (patches/020_hero_big_art.py's table), else the original small frame - its label red (no big version) or yellow (its big frame's definition can't be read
here). Labels are the frame numbers in hex.

    python3 tools/hero_sprite_sheet.py [--scale N]      (default 2)
"""
import importlib.util
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import hackbuild as h  # noqa: E402
from png_tiles import neo_to_rgb, read_rgba, write_indexed  # noqa: E402

spec = importlib.util.spec_from_file_location("hero_big_art", os.path.join(ROOT, "patches", "020_hero_big_art.py"))
hb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hb)

FONT = {c: rows for c, rows in zip("0123456789ABCDEF", [
    "111101101101111", "010110010010111", "111001111100111", "111001111001111", "101101111001001",
    "111100111001111", "111100111101111", "111001010010010", "111101111101111", "111101111001111",
    "010101111101101", "110101110101110", "111100100100111", "110101101101110", "111100110100111",
    "111100110100100"])}
COLS, PAD, LABEL_H = 10, 6, 8
BACK, GRID, WHITE, RED, YELLOW = (40, 40, 48), (70, 70, 80), (255, 255, 255), (255, 80, 80), (255, 220, 60)


def pixels_from_png(path):
    """{(x, y): (r, g, b)} of the opaque pixels."""
    return {(x, y): rgb for y, row in enumerate(read_rgba(path)) for x, (rgb, a) in enumerate(row) if a}


def pixels_from_frame(rom, frame):
    """As drawn (None if frame_pixels can't read its definition)."""
    try:
        src, palette = hb.frame_pixels(rom, frame)
    except SystemExit:
        return None
    colours = [neo_to_rgb(int(w, 16)) for w in hb.PALETTE_COLOURS.get(palette, hb.PALETTE_COLOURS[0x10]).split()]
    return {xy: colours[v] for xy, v in src.items() if v}


def trimmed(px):
    xs, ys = [x for x, _ in px], [y for _, y in px]
    return {(x - min(xs), y - min(ys)): c for (x, y), c in px.items()} if px else {}


def main():
    scale = int(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 2
    z = zipfile.ZipFile(h.ORIG_ZIP)
    entries = [(i, z.read(i)) for i in z.infolist()]
    p1 = next(d for i, d in entries if i.filename == h.P1_NAME)
    s1 = next(d for i, d in entries if i.filename == h.S1_NAME)
    rom = h.Rom(h.swap_pairs(p1), s1, {i.filename: d for i, d in entries if i.filename in h.C_NAMES})
    hb.ROW_OVERRIDES[hb.STANDING_ANIM] = [hb.spread_antennas(rom, f) for f in hb.BREATHE]   # (as the patch)
    _, frame_map = hb.big_frame_tables(rom)
    spec = importlib.util.spec_from_file_location("export", os.path.join(HERE, "export_hero_frames.py"))
    export = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export)
    copies = set(export.frames(rom))            # (drawn as 1.5x copies unless redrawn)

    cells = []                                  # (frame, pixels, label colour)
    for frame in range(0, hb.NORMAL_FRAMES, 4):
        art = os.path.join(ROOT, hb.ART % hb.THROW_ART.get(frame, frame))
        if os.path.exists(art):
            px, label = pixels_from_png(art), WHITE
        elif frame in copies:
            big, palette, _, _ = hb.upscaled_pixels(rom, frame)
            colours = [neo_to_rgb(int(w, 16)) for w in hb.PALETTE_COLOURS.get(palette, hb.PALETTE_COLOURS[0x10]).split()]
            px, label = {xy: colours[v] for xy, v in big.items()}, WHITE
        elif frame_map.get(frame) and pixels_from_frame(rom, frame_map[frame]) is not None:
            px, label = pixels_from_frame(rom, frame_map[frame]), WHITE
        else:
            px = pixels_from_frame(rom, frame) or {}
            label = YELLOW if frame_map.get(frame) else RED
        cells.append((frame, trimmed(px), label))

    cw = max(max((x for x, _ in px), default=0) for _, px, _ in cells) + 1 + 2 * PAD
    ch = max(max((y for _, y in px), default=0) for _, px, _ in cells) + 1 + 2 * PAD + LABEL_H
    rows = (len(cells) + COLS - 1) // COLS
    img = [[BACK] * (cw * COLS) for _ in range(ch * rows)]
    for n, (frame, px, label) in enumerate(cells):
        ox, oy = (n % COLS) * cw, (n // COLS) * ch
        for i in range(cw):
            img[oy][ox + i] = GRID
        for j in range(ch):
            img[oy + j][ox] = GRID
        w = max((x for x, _ in px), default=0) + 1
        hgt = max((y for _, y in px), default=0) + 1
        bx, by = ox + (cw - w) // 2, oy + LABEL_H + PAD + (ch - LABEL_H - 2 * PAD - hgt)   # (feet on the cell's floor)
        for (x, y), c in px.items():
            img[by + y][bx + x] = c
        for k, ch_ in enumerate("%03X" % frame):
            for b, bit in enumerate(FONT[ch_]):
                if bit == "1":
                    img[oy + 2 + b // 3][ox + 3 + k * 4 + b % 3] = label

    colours = [(255, 0, 255)] + sorted(set(c for row in img for c in row))   # (index 0 is transparent: unused)
    if len(colours) > 256:
        raise SystemExit("too many colours for an indexed PNG")
    index = {c: i for i, c in enumerate(colours)}
    out = [[index[c] for c in row for _ in range(scale)] for row in img for _ in range(scale)]
    path = os.path.join(ROOT, "docs", "hero_sprites.png")
    write_indexed(path, out, colours)
    print("wrote %s (%d frames; small: %d with no big version, %d whose big one can't be read here)" %
          (os.path.relpath(path, ROOT), len(cells), sum(1 for c in cells if c[2] == RED),
           sum(1 for c in cells if c[2] == YELLOW)))


if __name__ == "__main__":
    main()
