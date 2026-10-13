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
