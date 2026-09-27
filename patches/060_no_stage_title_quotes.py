NAME = "no-stage-title-quotes"
DESCRIPTION = "Remove the quotation marks around the act number on the stage title card (e.g. JUNGLE ZONE \"1\")"

# Each stage's title card text (e.g. "JUNGLE ZONE  \"1\"") is a plain ASCII string in the program ROM,
# one per zone/act combination (6 zones x 4 acts = 24 strings), drawn with a monospace fix-layer font
# where every glyph - including the quote marks and a plain space - takes the same tile width. The
# original designers padded shorter zone names with extra spaces before the quotes so the number lands
# in the same column for every zone: JUNGLE ZONE has 2 padding spaces before the quotes, the other five
# zones have 1. Simply blanking the quote marks to spaces (an earlier version of this patch) left that
# padding in place, so the gap in front of the number grew to 2-3 blank tiles instead of a normal 1.
#
# These 24 strings sit inline in the code at a fixed stride (each entry is part of a per-act subroutine
# spaced exactly 0x26 bytes apart), so nothing here can be shortened or lengthened without corrupting
# the next entry. Instead, each site's [padding spaces][quote][digit][quote] run is reordered in place,
# byte-for-byte, into [one space][digit][the rest of the padding as trailing spaces] - a normal single
# gap before the number, with the leftover blanks pushed after it where they're not visible.
# (region start, number of original padding spaces, the digit character)
SITES = [
    (0x147C8, 2, b"1"), (0x147EE, 2, b"2"), (0x14814, 2, b"3"), (0x1483A, 2, b"4"),   # JUNGLE ZONE
    (0x1486E, 1, b"1"), (0x148A4, 1, b"2"), (0x148DA, 1, b"3"), (0x14910, 1, b"4"),   # THE LOWER EARTH EMPIRE
    (0x1493A, 1, b"1"), (0x14962, 1, b"2"), (0x1498A, 1, b"3"), (0x149B2, 1, b"4"),   # EMPIRE MARSH
    (0x14A84, 1, b"1"), (0x14AAE, 1, b"2"), (0x14AD8, 1, b"3"), (0x14B02, 1, b"4"),   # MECHANICAL CITY
    (0x14BD2, 1, b"1"), (0x14BFA, 1, b"2"), (0x14C22, 1, b"3"), (0x14C4A, 1, b"4"),   # STARGE SPACE
    (0x14C73, 1, b"1"), (0x14C9B, 1, b"2"), (0x14CC3, 1, b"3"), (0x14CEB, 1, b"4"),   # DARUMA EMPIRE
]


def apply(rom):
    for start, num_spaces, digit in SITES:
        old = b" " * num_spaces + b'"' + digit + b'"'
        new = b" " + digit + b" " * (num_spaces + 1)
        rom.write(start, new, expect=old, why="single space before the act number, no quotes")
