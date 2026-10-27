NAME = "shop-title"
DESCRIPTION = "Fairy shop: \"SHOP\" on the plate at the top (where the countdown used to be), in the BLUE'S ITEM font"

# The plate above the fairy shop's item grid used to say TIME with the countdown under it; no-shop-timer and
# no-shop-time-label left it blank. It sits at screen x 32-159, y 0-15 (fix columns 4-19, rows 2-3).
#
# The "BLUE'S ITEM" header of the attract item screens is fix-layer text in palette 5 (the grey/white text
# palette) from a 16x16 font in the S ROM: each letter is 2x2 tiles, tile n / n+1 on top and n+0x10 / n+0x11
# below, eight letters per band of 0x20 tiles starting at 0x900 (A = 0x902 ... G = 0x90E, H = 0x920 ...,
# P = 0x940 ...). Set on the font's own 16-pixel grid the letters of SHOP looked cramped, so the four glyphs
# are copied out of the S ROM onto a pixel canvas with LETTER_GAP extra pixels between them, centered on the
# plate, and the canvas is cut into new fix tiles (rom.add_fix_tile).
#
# The font's S fills its cell to the right edge on three rows, leaving its black outline off there (a notch in its
# lower right); the outline goes back in the column just past the cell (in the gap before the H).
#
# It is drawn during the shop's set-up, before the fade-in, at the spot where the countdown digits used to be
# drawn: `move.w #0x71C2,d0` (their position) followed by the call no-shop-timer turned into NOPs - so this
# needs no-shop-timer (the digits would land on the same spot anyway).
SITE = 0x1F7F0                    # move.w #0x71C2,d0 ; nop ; nop
LETTERS = {"S": 0x946, "H": 0x920, "O": 0x92E, "P": 0x940}
TEXT, PALETTE = "SHOP", 5
LETTER_GAP = 3                    # extra pixels between letters
PLATE_CENTER_X = 96               # screen x
FIRST_COLUMN, COLUMNS, ROW = 7, 10, 2
BLANK = 0x0520
OUTLINE = 15


def apply(rom):
    width = COLUMNS * 8
    canvas = [[0] * width for _ in range(16)]
    text_width = 16 * len(TEXT) + LETTER_GAP * (len(TEXT) - 1)
    left = PLATE_CENTER_X - text_width // 2 - FIRST_COLUMN * 8
    for i, ch in enumerate(TEXT):
        for y, row in enumerate(rom.fix_glyph16(LETTERS[ch])):
            for x, v in enumerate(row):
                if v:
                    canvas[y][left + i * (16 + LETTER_GAP) + x] = v
        if ch == "S":
            x0 = left + i * (16 + LETTER_GAP)
            for y in range(16):
                if canvas[y][x0 + 15] not in (0, OUTLINE) and not canvas[y][x0 + 16]:
                    canvas[y][x0 + 16] = OUTLINE
    writes = ""
    for col in range(COLUMNS):
        for row in range(2):
            pixels = [canvas[row * 8 + y][col * 8:col * 8 + 8] for y in range(8)]
            addr = 0x7000 + (FIRST_COLUMN + col) * 32 + ROW + row
            if any(any(r) for r in pixels):
                word = PALETTE << 12 | rom.add_fix_tile(pixels, why="shop title piece")
            else:
                word = BLANK
            writes += "    move.w #0x%04X,0x3C0000\n    move.w #0x%04X,0x3C0002\n" % (addr, word)
    code = rom.place_code("""
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr                   | (no interrupt between the VRAM address and its writes)
%(writes)s    move.w (%%sp)+,%%sr
    rts
""" % {"writes": writes}, why="shop title SHOP on the top plate")
    if bytes(rom.data[SITE:SITE + 8]) != bytes.fromhex("303C71C24E714E71"):
        raise SystemExit("shop-title needs no-shop-timer (the countdown digit call at 0x1F7F4 must be gone)")
    rom.write(SITE, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("303C71C24E714E71"), why="shop set-up: draw SHOP where the countdown was")
