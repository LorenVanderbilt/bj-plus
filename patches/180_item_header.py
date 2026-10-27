NAME = "item-header"
DESCRIPTION = "Item screens' header: BLUE'S ITEMS (was BLUE'S ITEM), the apostrophe snug against the letters"

# The attract mode's two item screens (0x35CE0 and 0x35E9E) draw their "BLUE'S ITEM" header with
# `lea table,a0 ; move.w #0x7126,d0 ; jsr 0x36034`: a table of 2x2-tile letters from the 16x16 silver font
# (tile n / n+1 on top, n+0x10 / n+0x11 below, palette 5), one letter per 16-pixel cell from fix column 9,
# row 6. The apostrophe (tile 0xAE4) is a small mark in the middle of its own 16-pixel cell, so it floats
# between E and S with a gap on each side.
#
# Both header calls now draw a copy laid out pixel by pixel instead - reading BLUE'S ITEMS, plural: the letters
# on their usual 16-pixel spacing, the apostrophe trimmed to its ink plus a pixel either side, the whole line
# re-centered on the screen, cut into new fix tiles (rom.add_fix_tile).
#
# The font's S fills its cell to the right edge on three rows, so its black outline is missing there (a notch in
# the S's lower right). Its outline goes back in the column just past the cell (blank: a space or the line's end).
SITES = [(0x35CE0, "41F900035D4E303C71264EBA0348"), (0x35E9E, "41F900035FC0303C71264EBA018A")]
TEXT = "BLUE'S ITEMS"             # the original says ITEM
FONT = {"B": 0x904, "L": 0x928, "U": 0x94A, "E": 0x90A, "'": 0xAE4, "S": 0x946, "I": 0x922, "T": 0x948,
        "M": 0x92A}
APOSTROPHE_COLUMNS = (4, 12)      # pixel columns of the apostrophe's 16-pixel cell that are kept
# The font's letters fill their 16-pixel cells, outline to outline - but the I is narrow (ink in columns 3-12), so
# it stood 3 px off the T. It's drawn this many px right, a pixel short of touching (3 was too tight); its cell,
# and the rest of the line, stay where they were.
NUDGE = {"I": 2}
FIRST_COLUMN, COLUMNS, ROW, PALETTE = 8, 24, 6, 5
SCREEN_CENTER_X = 160
BLANK = 0x0520
OUTLINE = 15


def apply(rom):
    pieces = []
    for ch in TEXT:
        if ch == " ":
            pieces.append([[0] * 16 for _ in range(16)])
        elif ch == "'":
            a, b = APOSTROPHE_COLUMNS
            pieces.append([row[a:b] for row in rom.fix_glyph16(FONT[ch])])
        else:
            pieces.append(rom.fix_glyph16(FONT[ch]))
    width = sum(len(p[0]) for p in pieces)
    canvas = [[0] * (COLUMNS * 8) for _ in range(16)]
    x = SCREEN_CENTER_X - width // 2 - FIRST_COLUMN * 8
    for ch, piece in zip(TEXT, pieces):
        dx = NUDGE.get(ch, 0)
        for y in range(16):
            for i, v in enumerate(piece[y]):
                if v:
                    canvas[y][x + dx + i] = v
            if ch == "S" and piece[y][15] not in (0, OUTLINE) and not canvas[y][x + 16]:
                canvas[y][x + 16] = OUTLINE
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
