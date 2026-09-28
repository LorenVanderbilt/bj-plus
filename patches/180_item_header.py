NAME = "item-header"
DESCRIPTION = "BLUE'S ITEM screens: the apostrophe sits snug against the letters (was a full-width gap: BLUE ' S)"

# The attract mode's two item screens (0x35CE0 and 0x35E9E) draw their "BLUE'S ITEM" header with
# `lea table,a0 ; move.w #0x7126,d0 ; jsr 0x36034`: a table of 2x2-tile letters from the 16x16 silver font
# (tile n / n+1 on top, n+0x10 / n+0x11 below, palette 5), one letter per 16-pixel cell from fix column 9,
# row 6. The apostrophe (tile 0xAE4) is a small mark in the middle of its own 16-pixel cell, so it floats
# between E and S with a gap on each side.
#
# Both header calls now draw a copy laid out pixel by pixel instead: the letters on their usual 16-pixel
# spacing, the apostrophe trimmed to its ink plus a pixel either side, the whole line re-centered on the
# screen, cut into new fix tiles (rom.add_fix_tile).
SITES = [(0x35CE0, "41F900035D4E303C71264EBA0348"), (0x35E9E, "41F900035FC0303C71264EBA018A")]
TEXT = "BLUE'S ITEM"
FONT = {"B": 0x904, "L": 0x928, "U": 0x94A, "E": 0x90A, "'": 0xAE4, "S": 0x946, "I": 0x922, "T": 0x948,
        "M": 0x92A}
APOSTROPHE_COLUMNS = (4, 12)      # pixel columns of the apostrophe's 16-pixel cell that are kept
FIRST_COLUMN, COLUMNS, ROW, PALETTE = 9, 22, 6, 5
SCREEN_CENTER_X = 160
BLANK = 0x0520
FIX_COLUMN_BYTE = (16, 16, 24, 24, 0, 0, 8, 8)   # see tools/hackbuild.py


def glyph_pixel(s1, tile, x, y):
    b = s1[tile * 32 + FIX_COLUMN_BYTE[x] + y]
    return b & 15 if x % 2 == 0 else b >> 4


def glyph(s1, top):
    """16x16 pixels of a 2x2-tile letter."""
    return [[glyph_pixel(s1, top + (0x10 if y >= 8 else 0) + (1 if x >= 8 else 0), x % 8, y % 8)
             for x in range(16)] for y in range(16)]


def apply(rom):
    pieces = []
    for ch in TEXT:
        if ch == " ":
            pieces.append([[0] * 16 for _ in range(16)])
        elif ch == "'":
            a, b = APOSTROPHE_COLUMNS
            pieces.append([row[a:b] for row in glyph(rom.fix_orig, FONT[ch])])
        else:
            pieces.append(glyph(rom.fix_orig, FONT[ch]))
    width = sum(len(p[0]) for p in pieces)
    canvas = [[0] * (COLUMNS * 8) for _ in range(16)]
    x = SCREEN_CENTER_X - width // 2 - FIRST_COLUMN * 8
    for piece in pieces:
        for y in range(16):
            for i, v in enumerate(piece[y]):
                if v:
                    canvas[y][x + i] = v
        x += len(piece[0])
    writes = ""
    for col in range(COLUMNS):
        for row in range(2):
            pixels = [canvas[row * 8 + y][col * 8:col * 8 + 8] for y in range(8)]
            word = PALETTE << 12 | rom.add_fix_tile(pixels, why="BLUE'S ITEM header piece") \
                if any(any(r) for r in pixels) else BLANK
            writes += "    move.w #0x%04X,0x3C0000\n    move.w #0x%04X,0x3C0002\n" % (
                0x7000 + (FIRST_COLUMN + col) * 32 + ROW + row, word)
    code = rom.place_code(
        "    move.w %%sr,-(%%sp)\n"
        "    or.w #0x0700,%%sr\n"
        "%s"
        "    move.w (%%sp)+,%%sr\n"
        "    rts\n" % writes,
        why="BLUE'S ITEM header with a snug apostrophe")
    for site, orig in SITES:
        rom.write(site, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71") * 4,
                  expect=bytes.fromhex(orig), why="item screen: draw the re-spaced header")
