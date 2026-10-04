NAME = "no-house-timer"
DESCRIPTION = "No answer countdown in the NPC houses (the travel agent, the drinker, the magician ...): take your time"

# Each NPC question screen (and the card game) starts a countdown in the counter at 0x10783F - BCD seconds, 5 to 16
# - and draws it with 0x218D4; the per-frame tick 0x218A0 counts it down a second at a time and, on expiry, sets
# the time-up flag 0x107868, which picks an answer for you. (no-shop-timer stopped it on the shop and three screens
# by changing their start-ups; there are dozens more.) Now the tick and the digit drawing both just return the
# time-up flag (never set): no screen counts down or shows digits. Only the shop and the NPC screens use these
# two; the duel mini-game and the ending's timed scene have their own copies (0x28474, 0x245C8) and keep theirs.
#
# The empty box the digits sat in (top right, part of the brick-wall background every NPC screen shares) is painted
# over with bricks just before each screen fades in, as no-shop-timer does for its three - here only when the box
# is there (its top tile 0x535D at sprite 17 row 10), since some of these fade-ins are other screens.
TICK = 0x218A0               # cmpi.b #0x99,0x783F(a6) ...
DRAW = 0x218D4               # move.w #1,0x3C0004 ...
FLAG_RTS = 0x21926           # tst.b 0x7868(a6) ; rts
FADE_IN = 0x1572C
FADE_SITES = [0x1F7C2, 0x22EAE, 0x2340A, 0x236EE, 0x238EE, 0x23BB4, 0x26790, 0x27016, 0x27AAE, 0x285EE,
              0x2BABA, 0x2C024, 0x2C488, 0x2D33C, 0x2DDCA, 0x2F076]   # (no-shop-timer has 0x21AA4, 0x228B0, 0x25A0C)
BOX_TOP = (17 * 64 + 10 * 2, 0x535D)
COVER = [   # as no-shop-timer: (VRAM address of the first tile word, tiles going down)
    (16 * 64 + 10 * 2, [0x535E, 0x5343, 0x5343]),
    (17 * 64 + 10 * 2, [0x533D] * 3),
    (18 * 64 + 10 * 2, [0x533D] * 3),
]


def apply(rom):
    rom.write(TICK, bytes.fromhex("4EF9") + FLAG_RTS.to_bytes(4, "big"), expect=bytes.fromhex("0C2E0099783F"),
              why="NPC screens: the answer countdown never ticks")
    rom.write(DRAW, bytes.fromhex("4EF9") + FLAG_RTS.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("33FC0001003C0004"), why="NPC screens: no countdown digits")
    writes = "".join(
        "    move.w #0x%X,0x3C0000\n" % addr + "".join("    move.w #0x%X,0x3C0002\n" % t for t in tiles)
        for addr, tiles in COVER)
    cover = rom.place_code(
        "    move.w %%sr,-(%%sp)\n"
        "    or.w #0x0700,%%sr\n"
        "    move.w #0x%X,0x3C0000\n"
        "    cmp.w #0x%X,0x3C0002\n"          # (the box there?)
        "    bne.s 1f\n"
        "    move.w #2,0x3C0004\n"
        "%s"
        "    move.w #1,0x3C0004\n"
        "1:  move.w (%%sp)+,%%sr\n"
        "    jmp 0x%X\n" % (BOX_TOP[0], BOX_TOP[1], writes, FADE_IN),
        why="NPC screens: bricks over the empty timer box, then fade in")
    for site in FADE_SITES:
        rom.write(site, bytes.fromhex("4EB9") + cover.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + FADE_IN.to_bytes(4, "big"), why="cover the timer box if there, fade in")
