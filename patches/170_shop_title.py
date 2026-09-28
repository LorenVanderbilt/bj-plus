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
# plate, and the canvas is cut into new fix tiles (0x3E0-0x3FF, blank in the original S ROM).
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
FIRST_TILE = 0x3E0
BLANK = 0x0520
FIX_COLUMN_BYTE = (16, 16, 24, 24, 0, 0, 8, 8)   # see tools/hackbuild.py


def glyph_pixel(s1, tile, x, y):
    b = s1[tile * 32 + FIX_COLUMN_BYTE[x] + y]
    return b & 15 if x % 2 == 0 else b >> 4


def apply(rom):
    width = COLUMNS * 8
    canvas = [[0] * width for _ in range(16)]
    text_width = 16 * len(TEXT) + LETTER_GAP * (len(TEXT) - 1)
    left = PLATE_CENTER_X - text_width // 2 - FIRST_COLUMN * 8
    for i, ch in enumerate(TEXT):
        top = LETTERS[ch]
        for ty, tx, tile in ((0, 0, top), (0, 1, top + 1), (1, 0, top + 0x10), (1, 1, top + 0x11)):
            for y in range(8):
                for x in range(8):
                    v = glyph_pixel(rom.fix_orig, tile, x, y)
                    if v:
                        canvas[ty * 8 + y][left + i * (16 + LETTER_GAP) + tx * 8 + x] = v
    writes, n = "", FIRST_TILE
    for col in range(COLUMNS):
        for row in range(2):
            pixels = [canvas[row * 8 + y][col * 8:col * 8 + 8] for y in range(8)]
            addr = 0x7000 + (FIRST_COLUMN + col) * 32 + ROW + row
            if any(any(r) for r in pixels):
                rom.put_fix_tile(n, pixels, why="shop title piece")
                word, n = PALETTE << 12 | n, n + 1
            else:
                word = BLANK
            writes += "    move.w #0x%04X,0x3C0000\n    move.w #0x%04X,0x3C0002\n" % (addr, word)
    if n > 0x400:
        raise SystemExit("shop title needs more than fix tiles 0x3E0-0x3FF")
    code = rom.place_code(
        "    move.w %%sr,-(%%sp)\n"
        "    or.w #0x0700,%%sr\n"
        "%s"
        "    move.w (%%sp)+,%%sr\n"
        "    rts\n" % writes,
        why="shop title SHOP on the top plate")
    if bytes(rom.data[SITE:SITE + 8]) != bytes.fromhex("303C71C24E714E71"):
        raise SystemExit("shop-title needs no-shop-timer (the countdown digit call at 0x1F7F4 must be gone)")
    rom.write(SITE, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("303C71C24E714E71"), why="shop set-up: draw SHOP where the countdown was")
