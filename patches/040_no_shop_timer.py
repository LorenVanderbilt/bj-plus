NAME = "no-shop-timer"
DESCRIPTION = "Remove the 15-second countdown in the shops (all six shop versions)"

# Each shop start-up stores BCD 0x15 (15 seconds) in the counter at 0x10783F and calls a routine that
# draws the digits. A per-frame tick routine (0x218A0, with copies at 0x245C8 and 0x28474) counts it
# down and, on expiry, sets the time-up flag at 0x107868. The tick routines return early ("no expiry")
# when the counter holds 0x99, so each shop now starts at 0x99 and the digit-drawing call is removed.
# The 0x218A0 tick has other callers, so it is left untouched; only these six start-ups change.
SHOPS = [
    # (address of `move.b #0x15,0x783F(a6)`, address of the call that draws the digits, its bytes)
    (0x1F7E0, 0x1F7F4, "4EBA20DE"),        # jsr 0x218D4 (pc-relative)
    (0x21AD2, 0x21AE6, "4EB9000218D4"),    # jsr 0x218D4
    (0x228B6, 0x228CA, "4EB9000218D4"),
    (0x24536, 0x24546, "4EBA00B4"),        # jsr 0x245FC (this shop's own digit drawing)
    (0x25A12, 0x25A26, "4EB9000218D4"),
    (0x283E2, 0x283F2, "4EBA00B4"),        # jsr 0x284A8
]


def apply(rom):
    for start, draw, draw_bytes in SHOPS:
        rom.write(start + 2, bytes.fromhex("0099"), expect=bytes.fromhex("0015"),
                  why="shop timer starts at 0x99 = never runs (was 0x15 = 15 seconds)")
        n = len(draw_bytes) // 2
        rom.write(draw, bytes.fromhex("4E71") * (n // 2), expect=bytes.fromhex(draw_bytes),
                  why="no countdown digits drawn")
