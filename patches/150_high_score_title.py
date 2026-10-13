NAME = "high-score-title"
DESCRIPTION = "High score screen: title reads \"TODAY'S BEST 5\" with a snug apostrophe (was \"TODAY' S BEST5\")"

# The high score title is printed at 0x54A0E (`lea "TODAY'S BEST5",a0 ; move.w #pos,d0 ; ... jsr 0x4DED6`)
# with the big title font, where every character takes a 2x2-tile (16-pixel) cell. The apostrophe is the
# font's one special character (code 1 in the table at 0x4E00E): it draws a single tile in the top-left of its
# cell and leaves the right half blank, so it looks detached - "TODAY' S". The string itself has no space
# before the 5 and can't grow in place (the rank labels follow it).
#
# - The printer's apostrophe branch (0x4DF36) now draws the same glyph and moves on one column instead of
#   two, so the apostrophe takes half a cell. Only two screens use this printer: this title and the
#   how-to-play header, which has no apostrophe.
# - The title's `lea`/`move.w` pair becomes a call that points it at "TODAY'S BEST 5" in free space. With
#   the half-width apostrophe it is 27 columns wide, so it starts at column 6 (half a column left of center,
#   like the odd-length stage titles); same row as before (4).
TITLE_SETUP = 0x54A0E        # lea (pc),a0 = 41FA 01D4 ; move.w #0xE4,d0 = 303C 00E4
APOSTROPHE = 0x4DF36         # the whole apostrophe branch, up to its bra back into the loop
PRINTER = 0x4DED6
DRAW_2X2 = 0x4E8CC
APOSTROPHE_GLYPH = 0x4DF4E   # the branch's 4 tile words (apostrophe, 3 blanks)
TEXT = "TODAY'S BEST 5"
COLUMN, ROW = 6, 4
# The font's S fills its cell to the right edge on three rows, so its black outline is missing there (a notch in its
# lower right; item-header fixes the same in BLUE'S ITEMS). After the title's printed, and the 1ST below it (S_LINES),
# the cell after each S gets its left tiles redrawn with the outline back in their first column (copies: a space's
# blank, the T's).
S_LINES = [   # (the print call, its printer, text, column, row, palette)
    (0x54A1A, 0x4DED6, TEXT, COLUMN, ROW, 6),            # (the title: palette 6, from d2)
    (0x54A5A, 0x4DF88, "1ST", 4, 8, 5),                  # (the first rank: the font's own palette)
]
FONT_TABLE = 0x4E00E         # a word per character from ' ': its top-left tile (n, n+1 above n+0x10, n+0x11)
OUTLINE = 15
FIX_COLUMN_BYTE = (16, 16, 24, 24, 0, 0, 8, 8)   # see tools/hackbuild.py


def glyph(rom, ch):
    """16x16 pixels of a character in the big title font (blank for a space)."""
    if ch == " ":
        return [[0] * 16 for _ in range(16)]
    top = rom.u16(FONT_TABLE + 2 * (ord(ch) - 32)) & 0xFFF
    def pixel(tile, x, y):
        b = rom.fix_orig[tile * 32 + FIX_COLUMN_BYTE[x] + y]
        return b & 15 if x % 2 == 0 else b >> 4
    return [[pixel(top + (0x10 if y >= 8 else 0) + (1 if x >= 8 else 0), x % 8, y % 8) for x in range(16)]
            for y in range(16)]


def s_outlines(rom, text, col, row, palette):
    """68000 source writing the cells after each S of `text` (printed from column `col`) with its outline back."""
    writes = ""
    for i, ch in enumerate(text):
        width = 1 if ch == "'" else 2
        if ch == "S" and i + 1 < len(text):
            s, nxt = glyph(rom, "S"), glyph(rom, text[i + 1])
            for half in range(2):
                pixels = [row[:8] for row in nxt[half * 8:half * 8 + 8]]
                for y in range(8):
                    if s[half * 8 + y][15] not in (0, OUTLINE) and not pixels[y][0]:
                        pixels[y][0] = OUTLINE
                if pixels != [row[:8] for row in nxt[half * 8:half * 8 + 8]]:
                    tile = rom.add_fix_tile(pixels, why="TODAY'S BEST 5: an S's outline (%s)" % text, share=True)
                    writes += "    move.w #0x%04X,0x3C0000\n    move.w #0x%04X,0x3C0002\n" % (
                        0x7000 + (col + 2) * 32 + row + 2 + half, palette << 12 | tile)
        col += width
    return writes


def apply(rom):
    half = rom.place_code(
        "    movem.l %%d0/%%a0,-(%%sp)\n"
        "    addi.w #0x7002,%%d0\n"
        "    lea 0x%X,%%a0\n"
        "    jsr 0x%X\n"
        "    movem.l (%%sp)+,%%d0/%%a0\n"
        "    addi.w #32,%%d0\n"            # one column on, not two
        "    jmp 0x%X\n" % (APOSTROPHE_GLYPH, DRAW_2X2, PRINTER),
        why="big-font apostrophe takes half a cell")
    rom.write(APOSTROPHE, bytes.fromhex("4EF9") + half.to_bytes(4, "big"), expect=bytes.fromhex("48E780800640"),
              why="big-font printer: apostrophe goes through the half-cell version")
    setup = rom.place_code(
        "    lea text(%%pc),%%a0\n"
        "    move.w #%d,%%d0\n"
        "    rts\n"
        "text:\n"
        "    .ascii \"%s\"\n"
        "    .byte 0xFF\n"
        "    .even\n" % (COLUMN * 32 + ROW, TEXT),
        why="high score title text and position")
    rom.write(TITLE_SETUP, bytes.fromhex("4EB9") + setup.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("41FA01D4303C00E4"), why="high score title: new text, centered")
    for call, printer, text, col, row, palette in S_LINES:
        fix = rom.place_code("    jsr 0x%X\n%s    rts\n" % (printer, s_outlines(rom, text, col, row, palette)),
                             why="TODAY'S BEST 5: the S's outlines (%s)" % text)
        rom.write(call, bytes.fromhex("4EB9") + fix.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + printer.to_bytes(4, "big"), why="%s: the S's outlines after it" % text)
