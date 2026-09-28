NAME = "no-stage-title-quotes"
DESCRIPTION = "Stage title cards: no quotation marks around the act number, each name centered (e.g. JUNGLE ZONE 1), STRANGE SPACE spelled right"

# Each stage's English title card (e.g. ` JUNGLE ZONE  "1"`) is a plain ASCII string in the program ROM, one
# per zone/act (6 zones x 4 acts = 24), printed by a small per-act routine: `lea string,a0 ; move.w #pos,d0 ;
# ... jsr 0x4DEA0`. The printer draws one 8-pixel fix-layer tile per character, moving one column right each
# time, so the text's screen position is the start column (pos / 32) plus the string's leading spaces. The
# original strings padded the zone names so the quoted number lined up; with the quotes gone that padding
# left most names off center (JUNGLE ZONE by 2.5 columns).
#
# These strings sit inline in the code at a fixed stride, so their length can't change. Each one is rewritten
# in place, same length: the zone name and act number separated by single spaces, with enough leading spaces
# to center it on the 40-column screen (an odd-length name sits half a column left) and the rest blank.
ROUTINES = [0x147A8 + 0x26 * i for i in range(4)] + [   # JUNGLE ZONE (acts 3-4 are unused by the game)
    0x14840, 0x14876, 0x148AC, 0x148E2,                   # THE LOWER EARTH EMPIRE
    0x14918, 0x14940, 0x14968, 0x14990,                   # EMPIRE MARSH
    0x14A60, 0x14A8A, 0x14AB4, 0x14ADE,                   # MECHANICAL CITY
    0x14BB0, 0x14BD8, 0x14C00, 0x14C28,                   # STARGE SPACE (sic)
    0x14C50, 0x14C78, 0x14CA0, 0x14CC8,                   # DARUMA EMPIRE
]
SCREEN_COLUMNS = 40
# The English version misspells one zone: its Japanese name, 不思議空間 ("mysterious space"), was meant as
# STRANGE SPACE.
RENAMES = {"STARGE SPACE": "STRANGE SPACE"}


def apply(rom):
    for r in ROUTINES:
        # lea (pc),a0 = 41FA dddd ; move.w #pos,d0 = 303C pppp
        if rom.u16(r) != 0x41FA or rom.u16(r + 4) != 0x303C:
            raise SystemExit("title card routine not found at 0x%X" % r)
        text_at = r + 2 + int.from_bytes(rom.data[r + 2:r + 4], "big", signed=True)
        start_col = rom.u16(r + 6) // 32
        old = bytes(rom.data[text_at:rom.data.index(0xFF, text_at)])
        name = " ".join(old.decode("ascii").replace('"', " ").split())
        for a, b in RENAMES.items():
            name = name.replace(a, b)
        lead = (SCREEN_COLUMNS - len(name)) // 2 - start_col
        if lead < 0 or lead + len(name) > len(old):
            raise SystemExit("can't center %r in its %d-byte string" % (name, len(old)))
        new = (" " * lead + name).ljust(len(old)).encode("ascii")
        rom.write(text_at, new, expect=old, why="title card %r: no quotes, centered" % name)
