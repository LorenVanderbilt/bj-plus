NAME = "no-shop-timer"
DESCRIPTION = "Remove the 15-second countdown in the shops (all six shop versions) and the empty box it leaves behind"

# Each shop start-up stores BCD 0x15 (15 seconds) in the counter at 0x10783F and calls a routine that
# draws the digits. A per-frame tick routine (0x218A0, with copies at 0x245C8 and 0x28474) counts it
# down and, on expiry, sets the time-up flag at 0x107868. The tick routines return early ("no expiry")
# when the counter holds 0x99, so each shop now starts at 0x99 and the digit-drawing call is removed.
# The 0x218A0 tick has other callers, so it is left untouched; only these six start-ups change.
# (Despite the name, only the first is the fairy shop; three are NPC yes/no screens - see BOX_SITES.)
SHOPS = [
    # (address of `move.b #0x15,0x783F(a6)`, address of the call that draws the digits, its bytes)
    (0x1F7E0, 0x1F7F4, "4EBA20DE"),        # jsr 0x218D4 (pc-relative)
    (0x21AD2, 0x21AE6, "4EB9000218D4"),    # jsr 0x218D4
    (0x228B6, 0x228CA, "4EB9000218D4"),
    (0x24536, 0x24546, "4EBA00B4"),        # jsr 0x245FC (this shop's own digit drawing)
    (0x25A12, 0x25A26, "4EB9000218D4"),
    (0x283E2, 0x283F2, "4EBA00B4"),        # jsr 0x284A8
]

# Three of these are NPC yes/no screens ("SEE THE LARGE RIVER AHEAD?", "AREN'T YOU BLUE...", the quiz man)
# whose digits went in a small box at the top right (fix-layer 0x7404). The box is part of the brick-wall
# background map that every NPC screen shares - the ones that still count down need it - so instead of
# editing the map, these screens paint bricks over it just before their fade-in (`jsr 0x1572C`), right
# after the wall has been decoded - painting it later, where the digits used to be drawn, left the box on
# screen for the ~1 s fade. The wall is drawn into full-height background sprite strips; the box covers
# sprite 16 rows 10-12 (shared with the portrait frame's right edge: 0x5343 as below the box, and for the
# frame's top-right corner 0x535E, which is the corner tile 0x533C without the box's corner pixels) and
# sprites 17-18 rows 10-12 (plain brick, 0x533D).
BOX_SITES = [0x21AA4, 0x228B0, 0x25A0C]   # each screen's `jsr 0x1572C` (fade in)
FADE_IN = 0x1572C
COVER = [
    # (VRAM address of the first tile word = sprite * 64 + row * 2, tiles going down)
    (16 * 64 + 10 * 2, [0x535E, 0x5343, 0x5343]),
    (17 * 64 + 10 * 2, [0x533D] * 3),
    (18 * 64 + 10 * 2, [0x533D] * 3),
]


def apply(rom):
    writes = "".join(
        "    move.w #0x%X,0x3C0000\n" % addr + "".join("    move.w #0x%X,0x3C0002\n" % t for t in tiles)
        for addr, tiles in COVER)
    cover = rom.place_code(
        "    move.w %%sr,-(%%sp)\n"
        "    or.w #0x0700,%%sr\n"          # no interrupt may move the VRAM address mid-way
        "    move.w #2,0x3C0004\n"         # step 2: the next tile word down the strip (skip the attribute word)
        "%s"
        "    move.w #1,0x3C0004\n"
        "    move.w (%%sp)+,%%sr\n"
        "    jmp 0x%X\n" % (writes, FADE_IN),
        why="paints bricks over the empty timer box on the NPC screens without a countdown, then fades in")
    for start, draw, draw_bytes in SHOPS:
        rom.write(start + 2, bytes.fromhex("0099"), expect=bytes.fromhex("0015"),
                  why="shop timer starts at 0x99 = never runs (was 0x15 = 15 seconds)")
        n = len(draw_bytes) // 2
        rom.write(draw, bytes.fromhex("4E71") * (n // 2), expect=bytes.fromhex(draw_bytes),
                  why="no countdown digits drawn")
    for site in BOX_SITES:
        rom.write(site, bytes.fromhex("4EB9") + cover.to_bytes(4, "big"), expect=bytes.fromhex("4EB9") + FADE_IN.to_bytes(4, "big"),
                  why="cover the empty timer box with bricks, then fade in as before")
