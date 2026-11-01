NAME = "tile-pool"
DESCRIPTION = "Free sprite tiles for new art: frames using blank or duplicate tiles share one copy, the rest go to a pool"

# New art needs free 16x16 sprite tiles; the C ROMs have only 100 blank ones nothing uses (hackbuild's range).
# Many frame definitions use a blank tile for an empty spot, or one of several identical tiles. Those frames are
# written again (an empty spot instead of the blank tile, the first of the identical tiles instead of the others),
# which leaves the other tiles unused: they go to rom.tile_pool, which add_sprite_tile uses after its range.
# A tile is only freed if:
#   * every frame using it is a plain one (no per-tile attributes, and mode 0: a mode 1 frame - the hero's -
#     has no "1, attribute, bank, tile" entries, so one can't be rewritten to use a tile in another bank);
#   * its number never appears as a word in the code (below 0x60000), nor - with the rest of its group of 8, the
#     hardware's tile animation - in the data after it, outside the frame definitions (level maps name tiles);
#   * no patch names it (a 0x.... number in their source - e.g. the text box tiles drawn by story-last-line).
import glob
import os
import re

TILES = 0x6000


def decode(rom, p):
    """(cols, rows, mode, attr, tiles[row][col] or None, plain) of the frame definition at p."""
    cols, rows, mode, attr, hi = rom.orig[p:p + 5]
    tiles = [[None] * (cols + 1) for _ in range(rows + 1)]
    q, plain = p + 5, True
    for c in range(cols + 1):
        for r in range(rows + 1):
            v = rom.orig[q]
            q += 1
            if v == 0:
                continue
            if v == 1:                # 1, attribute, [palette,] [high byte,] low byte (bits 6 / 5 of the attribute)
                a = rom.orig[q]
                q += 1
                if a != 0x20:
                    plain = False
                if a & 0x80:          # unknown: the frame is left alone, its tiles kept
                    return cols, rows, mode, attr, tiles, False, q
                if a & 0x40:
                    q += 1
                if a & 0x20:
                    hi, q = rom.orig[q], q + 1
                v, q = rom.orig[q], q + 1
            tiles[r][c] = (hi << 8) | v
    while rom.orig[q] != 0xFF:        # extra one-column pieces (see 0xAF1C): kept as they are, so never rewritten
        plain = False
        n, hi = rom.orig[q], rom.orig[q + 4]
        q += 5
        for r in range(n + 1):
            v = rom.orig[q]
            q += 1
            if v == 0:
                continue
            if v == 1:
                a = rom.orig[q]
                q += 1
                if a & 0x80:
                    return cols, rows, mode, attr, tiles, False, q
                if a & 0x40:
                    q += 1
                if a & 0x20:
                    hi, q = rom.orig[q], q + 1
                v, q = rom.orig[q], q + 1
            tiles.append([None] * c + [(hi << 8) | v])   # counted as used, as a row of its own
    return cols, rows, mode, attr, tiles, plain, q


def encode(cols, rows, mode, attr, tiles):
    first = next((t for row in tiles for t in row if t is not None), 0)
    hi = first >> 8
    out = bytearray([cols, rows, mode, attr, hi])
    for c in range(cols + 1):
        for r in range(rows + 1):
            t = tiles[r][c]
            if t is None:
                out.append(0)
            elif t >> 8 == hi and (t & 0xFF) > 1:
                out.append(t & 0xFF)
            else:
                hi = t >> 8
                out += bytes([1, 0x20, hi, t & 0xFF])
    return bytes(out) + b"\xff"


def apply(rom):
    import hackbuild as H
    table = H.FRAME_TABLE
    frames, defs_bytes = {}, set()
    for fr in range(0, 0x4000, 4):
        p = rom.u32(table + fr)
        if not 0x60000 <= p < len(rom.orig):
            continue
        cols, rows, mode, attr, tiles, plain, end = decode(rom, p)
        if mode != 0:             # mode 1 - the hero's frames - has no bank-switch entries: never rewritten
            plain = False
        frames[fr] = (cols, rows, mode, attr, tiles, plain)
        defs_bytes.update(range(p, end + 1))
    refs, fixed = {}, set()
    for fr, (cols, rows, mode, attr, tiles, plain) in frames.items():
        for row in tiles:
            for t in row:
                if t is not None:
                    refs.setdefault(t, set()).add(fr)
                    if not plain:
                        fixed.add(t)
    named = set()
    b = rom.orig
    for i in range(0, len(b) - 1, 2):
        if i not in defs_bytes:
            w = b[i] << 8 | b[i + 1]
            if w < TILES:
                if i < 0x60000:
                    named.add(w)                                  # code names a tile exactly
                else:
                    named.update(range(w & ~7, (w & ~7) + 8))     # a map tile may animate through its group of 8
    here = os.path.dirname(os.path.abspath(__file__))
    for path in glob.glob(os.path.join(here, "*.py")):
        if os.path.basename(path) != os.path.basename(__file__):
            named.update(int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{4})\b", open(path).read())
                         if int(x, 16) < TILES)

    def pixels(t):
        a, c, at = rom._sprite_at(t)
        return bytes(rom.sprites_orig[a][at:at + 64]) + bytes(rom.sprites_orig[c][at:at + 64])
    groups = {}
    for t in sorted(refs):
        groups.setdefault(pixels(t), []).append(t)
    blank = bytes(128)
    to = {}                       # freed tile -> its replacement (None = an empty spot)
    for px, ts in groups.items():
        movable = [t for t in ts if t not in fixed and t not in named]
        if px == blank:
            for t in movable:
                to[t] = None
        else:
            keep = next((t for t in ts if t not in movable), movable[0] if movable else None)
            for t in movable:
                if t != keep:
                    to[t] = keep
    rewritten = 0
    for fr, (cols, rows, mode, attr, tiles, plain) in frames.items():
        if not plain or not any(t in to for row in tiles for t in row):
            continue
        new = [[to.get(t, t) if t in to else t for t in row] for row in tiles]
        body = encode(cols, rows, mode, attr, new)
        addr = rom.alloc(len(body))
        rom.data[addr:addr + len(body)] = body
        rom.data[table + fr:table + fr + 4] = addr.to_bytes(4, "big")
        rewritten += 1
    rom.pooled = set(to)
    rom.tile_pool = sorted(to)
    rom.log.append("  tile-pool: %d frames rewritten, %d tiles freed" % (rewritten, len(to)))
