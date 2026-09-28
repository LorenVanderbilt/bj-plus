NAME = "item-text"
DESCRIPTION = "BLUE'S ITEM screens: new English item names and descriptions"

# The attract mode's two item screens draw their English text (non-Japanese consoles; 0x10FD83 != 0) with
# `lea string,a0 ; move.w #position,d0 ; jsr 0x4DBB8` per line: an ASCII string ending in FF, drawn from fix
# address 0x7000 + position (column * 32 + row). Each item is a line at column 11 holding the name, padded to
# column 19 where the description starts (the "..." between them is part of the box artwork, as is the "x"
# in SILVERx5), or the name alone with two description lines at column 19, a row above and below.
# The descriptions have room for 16 characters before the box edge.
#
# Both screens' text calls are replaced by a call to new code drawing the new lines (so a line can be longer
# than the original string, or split in two), followed by a branch over the old calls.
SCREENS = [
    # (first old call, end of the old calls, [(column, row, text)])
    (0x35DCA, 0x35DFA, [
        (11, 10, "CLOVER  REVEAL SHOP"),
        (11, 16, "KEY"), (19, 15, "UNLOCK"), (19, 17, "BONUS ROOM"),
        (11, 22, "LEAF    ATTACK UP"),
    ]),
    (0x35EF0, 0x35F40, [
        (11, 10, "COCOON"), (19, 9, "GOLD 1UP"), (19, 11, "SILVER 5 1UP"),
        (11, 16, "NECTAR  RESTORE 1 HEALTH"),
        (11, 22, "FERN    SPEED UP"),
    ]),
]
DRAW_TEXT = 0x4DBB8
BOX_LAST_COLUMN = 34              # a description may not run past this column


def apply(rom):
    for first, end, lines in SCREENS:
        if rom.u16(first) != 0x41F9:
            raise SystemExit("item-text: unexpected code at 0x%X" % first)
        src = ""
        for n, (col, row, text) in enumerate(lines):
            if col + len(text) - 1 > BOX_LAST_COLUMN:
                raise SystemExit("item-text: %r runs past the box" % text)
            src += ("    lea str%d(%%pc),%%a0\n    move.w #0x%X,%%d0\n    jsr 0x%X\n"
                    % (n, col * 32 + row, DRAW_TEXT))
        src += "    rts\n"
        for n, (col, row, text) in enumerate(lines):
            src += "str%d:\n    .byte %s,0xFF\n" % (n, ",".join("0x%02X" % ord(c) for c in text))
        code = rom.place_code(src, why="item screen text")
        skip = end - (first + 6) - 2
        assert 0 < skip < 128
        rom.write(first, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes([0x60, skip]),
                  expect=bytes(rom.data[first:first + 8]), why="item screen: draw the new text instead")
