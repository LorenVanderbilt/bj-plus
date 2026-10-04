NAME = "geyser-foam"
DESCRIPTION = "Empire Marsh 1's geysers: the lakes' surface bubbles where each one meets the water"

# drown-in-front draws Empire Marsh 1's geysers (object 0x300FA) in front of the water, with the water drawn again
# over their foot. Where they meet it, this adds the bubbles the level's lakes have along their surface: those are
# objects (0x3004C, 0x30052 ... - each loads its first picture into d7 and runs 0x30062: draw mode 0xA0, on odd
# frames one of four pictures by the frame counter, on even frames none - a shimmer - then 0x1922A, which hides it
# off screen). When a geyser starts (its first run: `move.b #1,41(a5)` at 0x30106) it spawns two of them across its
# foot, in the behind group (0x10070); drown-in-front keeps the game from drawing them there and draws them itself,
# last - over the geyser and its water. They run through a small routine of their own (so drown-in-front can tell
# them from the lakes'), which also clears them (their draw byte) when their geyser goes.
# Positions scroll with the screen (y = 352 - height / 128, x = x / 128 - 128): the bubbles go at the water's
# surface, 0x2600 below where the geyser started (the lakes' own sit at height 0x5000, the geysers start at 0x7600).
GEYSER_FIRST_RUN = 0x30106    # move.b #1,41(a5)
GEYSER_CODE = 0x300FA
ALLOC_BEHIND = 0x10070        # -> a1, ne = none free
BUBBLES = 0x30062             # d7 = first picture
FOAM_DY = -0x2600             # from the geyser's first height: the water's surface
PIECES = [(-0x400, 0x2300), (0xC00, 0x2310)]   # (x from the geyser's (its left edge), first picture)


def apply(rom):
    foam = rom.place_code(
        "    move.l 0x70(%%a5),%%a0           | its geyser still there?\n"
        "    cmp.l #0x%X,4(%%a0)\n"
        "    bne.s 9f\n"
        "    tst.b 0x28(%%a0)\n"
        "    beq.s 9f\n"
        "    move.w 0x74(%%a5),%%d7\n"
        "    jmp 0x%X\n"
        "9:  clr.b 0x28(%%a5)\n"
        "    rts\n" % (GEYSER_CODE, BUBBLES),
        why="geyser foam: the lakes' bubbles at a geyser's foot")
    rom.geyser_foam_code = foam
    pieces = ""
    for dx, picture in PIECES:
        pieces += (
            "    jsr 0x%X\n"
            "    bne 1f\n"
            "    move.l #0x%X,4(%%a1)\n"
            "    move.w (%%a5),%%d0\n"
            "    add.w #%d,%%d0\n"
            "    move.w %%d0,(%%a1)\n"
            "    move.w 2(%%a5),%%d0\n"
            "    add.w #%d,%%d0\n"
            "    move.w %%d0,2(%%a1)\n"
            "    move.b #0xA0,0x28(%%a1)\n"
            "    move.w #-1,0x2C(%%a1)\n"
            "    move.l %%a5,0x70(%%a1)\n"
            "    move.w #0x%X,0x74(%%a1)\n" % (ALLOC_BEHIND, foam, FOAM_DY, dx, picture))
    spawn = rom.place_code(
        "    move.b #1,41(%%a5)\n"
        "    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)\n"
        "%s"
        "1:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6\n"
        "    rts\n" % pieces,
        why="geyser foam: bubbles spawned when a geyser starts")
    rom.write(GEYSER_FIRST_RUN, bytes.fromhex("4EB9") + spawn.to_bytes(4, "big"), expect=bytes.fromhex("1B7C00010029"),
              why="geyser: spawn its bubbles on its first run")
