NAME = "geyser-foam"
DESCRIPTION = "Empire Marsh 1's geysers: churning foam where each meets the water, so the join isn't a flat edge"

# Each geyser column (object code 0x300FA) is drawn behind the water and bobs up and down (its height, +0, between
# about 0x5900 and 0x7100; x, +2, fixed), so where it meets the water is a flat, moving edge. When a geyser starts
# (its first run: `move.b #1,41(a5)` at 0x30106) it now also spawns a foam object in the front group (0xFFEC, like
# the idle GO sign), at the water's surface (FOAM_HEIGHT - where the game puts a drowning splash in this level) under
# the geyser: it loops the drowning splash's animation (262: 0x4346C starts it, 0x434A8 steps it, minus at its end)
# and goes (its draw byte cleared) when its geyser does.
GEYSER_FIRST_RUN = 0x30106    # move.b #1,41(a5)
GEYSER_CODE = 0x300FA
ALLOC_FRONT = 0xFFEC          # -> a1, ne = none free
ANIM_START, ANIM_STEP = 0x4346C, 0x434A8
SPLASH_ANIM = 262
FOAM_HEIGHT = 0x5868 + 0x500 # (a little above where the game puts a drowning splash in this level)
FOAM_X = 0x0800               # right of the geyser's x (its sprites start left of it): under its middle
FOAM_DRAW = 0x80              # as the drowning splash


def apply(rom):
    foam = rom.place_code(
        "foam:\n"
        "    move.l 0x70(%%a5),%%a0           | its geyser still there?\n"
        "    cmp.l #0x%X,4(%%a0)\n"
        "    bne.s 2f\n"
        "    tst.b 0x28(%%a0)\n"
        "    beq.s 2f\n"
        "    jsr 0x%X                        | step the splash animation\n"
        "    bpl.s 1f\n"
        "    move.w #%d,%%d0                 | (ended: again)\n"
        "    jsr 0x%X\n"
        "1:  rts\n"
        "2:  clr.b 0x28(%%a5)                | (gone)\n"
        "    rts\n" % (GEYSER_CODE, ANIM_STEP, SPLASH_ANIM, ANIM_START),
        why="geyser foam: loop the splash animation under its geyser")
    spawn = rom.place_code(
        "    move.b #1,41(%%a5)\n"
        "    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)\n"
        "    jsr 0x%X\n"
        "    bne.s 1f\n"
        "    move.l #0x%X,4(%%a1)\n"
        "    move.w #0x%X,0(%%a1)\n"
        "    move.w 2(%%a5),%%d0\n"
        "    add.w #0x%X,%%d0\n"
        "    move.w %%d0,2(%%a1)\n"
        "    move.b #0x%X,0x28(%%a1)\n"
        "    move.l %%a5,0x70(%%a1)\n"
        "    move.b #8,0x60(%%a1)\n"
        "    move.l %%a1,%%a5\n"
        "    move.w #%d,%%d0\n"
        "    jsr 0x%X\n"
        "1:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6\n"
        "    rts\n" % (ALLOC_FRONT, foam, FOAM_HEIGHT, FOAM_X, FOAM_DRAW, SPLASH_ANIM, ANIM_START),
        why="geyser foam: spawned when a geyser starts")
    rom.write(GEYSER_FIRST_RUN, bytes.fromhex("4EB9") + spawn.to_bytes(4, "big"), expect=bytes.fromhex("1B7C00010029"),
              why="geyser: spawn its foam on its first run")
