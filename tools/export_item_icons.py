"""Write art/item_<name>.png for BLUE'S ITEMS screen 3's icons (patches/210_item_text.py: ICONS, ART) - the icon
as drawn now (its level tile at 2x), 32x32, in its colours - the starting point for redrawing it. Leaves an
existing file alone unless --force.

    python3 tools/export_item_icons.py catfish [bamboo flower ...] [--force]
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

spec = importlib.util.spec_from_file_location("item_text", os.path.join(ROOT, "patches", "210_item_text.py"))
it = importlib.util.module_from_spec(spec)
spec.loader.exec_module(it)


def main():
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not names or any(n not in it.ICONS for n in names):
        raise SystemExit("usage: export_item_icons.py %s [--force]" % " ".join(it.ICONS))
    z = zipfile.ZipFile(h.ORIG_ZIP)
    entries = [(i, z.read(i)) for i in z.infolist()]
    p1 = next(d for i, d in entries if i.filename == h.P1_NAME)
    s1 = next(d for i, d in entries if i.filename == h.S1_NAME)
    rom = h.Rom(h.swap_pairs(p1), s1, {i.filename: d for i, d in entries if i.filename in h.C_NAMES})
    for name in names:
        out = os.path.join(ROOT, it.ART % name)
        if os.path.exists(out) and "--force" not in sys.argv:
            print("%s exists (--force to overwrite)" % (it.ART % name))
            continue
        tile, colors, slot = it.ICONS[name]
        palette = [int(c, 16) for c in colors.split()]
        src = rom.sprite_tile(tile)
        rows = [[src[y // 2][x // 2] for x in range(32)] for y in range(32)]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        write_indexed(out, rows, [neo_to_rgb(w) for w in palette])
        print("wrote", it.ART % name)


if __name__ == "__main__":
    main()
