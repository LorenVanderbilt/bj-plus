"""Write art/title_sky.png: the title sky's columns that title-clouds lets you redraw (patches/410_title_clouds.py,
ART / ART_COLUMNS), as an indexed PNG in the title's palette - the starting point for editing. Leaves an existing
file alone unless --force. --preview instead writes art/title_sky_preview.png from the (edited) art: it beside its
mirror image, the way the drifting sky joins them.

    python3 tools/export_title_sky.py [--force | --preview]
"""
import importlib.util
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import hackbuild as h  # noqa: E402
from png_tiles import write_indexed  # noqa: E402

spec = importlib.util.spec_from_file_location("title_clouds", os.path.join(ROOT, "patches", "410_title_clouds.py"))
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)


def rgb(word):
    """A Neo Geo colour word as 8-bit r, g, b (5 bits each: the low bit in bits 14-12)."""
    return tuple((((word >> shift) & 15) << 1 | (word >> low) & 1) * 255 // 31
                 for shift, low in ((8, 14), (4, 13), (0, 12)))


def preview():
    from png_tiles import read_indices
    palette = [rgb(w) for w in tc.PALETTE]
    art = read_indices(os.path.join(ROOT, tc.ART), palette)
    rows = [r + r[::-1] for r in art]
    out = os.path.join(ROOT, "art", "title_sky_preview.png")
    write_indexed(out, rows, palette)
    print("wrote", os.path.relpath(out, ROOT))


def main():
    if "--preview" in sys.argv:
        return preview()
    out = os.path.join(ROOT, tc.ART)
    if os.path.exists(out) and "--force" not in sys.argv:
        raise SystemExit("%s exists (--force to overwrite)" % tc.ART)
    z = zipfile.ZipFile(h.ORIG_ZIP)
    entries = [(i, z.read(i)) for i in z.infolist()]
    p1 = next(d for i, d in entries if i.filename == h.P1_NAME)
    s1 = next(d for i, d in entries if i.filename == h.S1_NAME)
    rom = h.Rom(h.swap_pairs(p1), s1, {i.filename: d for i, d in entries if i.filename in h.C_NAMES})
    cols = list(tc.ART_COLUMNS)
    rows = [[0] * (16 * len(cols)) for _ in range(16 * tc.ROWS)]
    for r in range(tc.ROWS):
        for k, c in enumerate(cols):
            px = rom.sprite_tile(tc.shown(r, c))
            for y in range(16):
                rows[r * 16 + y][k * 16:k * 16 + 16] = px[y]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write_indexed(out, rows, [rgb(w) for w in tc.PALETTE])
    print("wrote", tc.ART)


if __name__ == "__main__":
    main()
