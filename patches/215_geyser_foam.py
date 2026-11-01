NAME = "geyser-foam"
DESCRIPTION = "Empire Marsh 1's geysers: the lakes' surface bubbles where each one meets the water"

# drown-in-front draws Empire Marsh 1's geysers (object 0x300FA) in front of the water, with the water drawn again
# over their foot. This adds the bubbles the lakes have along their surface where each geyser meets the water.
#
# The lakes' bubbles are objects (0x3004C, 0x30052 and so on). Each loads its first picture into d7 and runs 0x30062:
# draw mode 0xA0, one of four pictures by the frame counter on odd frames and nothing on even frames, for a shimmer,
# then 0x1922A, which hides it off screen. The geyser's bubbles show every frame instead, so the line under them
# stays hidden.
#
# When a geyser starts (its first run, move.b #1,41(a5) at 0x30106), it spawns two of them across its foot, in the
# behind group (0x10070). drown-in-front stops the game drawing them there and draws them itself, last, over the
# geyser and its water. They run through their own small routine, so drown-in-front can tell them apart from the
# lakes' bubbles, and it also clears their draw byte when their geyser goes.
#
# A geyser that leaves the screen and comes back is created again, often in the same slot. Its first run clears any
# bubbles still pointing at that slot before spawning new ones; otherwise they piled up into wider rows and slowdown.
#
# Positions scroll with the screen (y = 352 - height / 128, x = x / 128 - 128). The bubbles sit at the water's
# surface, 0x2600 below where the geyser started; the lakes' own bubbles are at height 0x5000, and geysers start at
# 0x7600.
GEYSER_FIRST_RUN = 0x30106    # move.b #1,41(a5)
GEYSER_CODE = 0x300FA
ALLOC_BEHIND = 0x10070        # returns a1; ne if none is free
FRAME_COUNT = 0x6902          # from a6
OFF_SCREEN = 0x1922A
FOAM_DY = -0x2A00             # from the geyser's first height, straddling the line the water covers it from (a
                              # row below the surface: drown-in-front's GEYSER_ROWS)
PIECES = [(0x800, 0x2300)]     # x from the geyser's left edge, over its stalk; first picture, 3 tiles


def apply(rom):
    foam = rom.place_code("""
    move.l 0x70(%%a5),%%a0              | is its geyser still there?
    cmp.l #0x%(geyser)X,4(%%a0)
    bne.s 9f
    tst.b 0x28(%%a0)
    beq.s 9f
    move.b #0xA0,0x28(%%a5)             | its picture every frame (the lakes' show on odd frames only, a
    move.w 0x%(frame)X(%%a6),%%d0       | shimmer, but these have to hide the line under them)
    and.w #12,%%d0
    add.w 0x74(%%a5),%%d0
    move.w %%d0,8(%%a5)
    jmp 0x%(off_screen)X
9:  clr.b 0x28(%%a5)
    rts
""" % {"geyser": GEYSER_CODE, "frame": FRAME_COUNT, "off_screen": OFF_SCREEN},
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
    spawn = rom.place_code("""
    move.b #1,41(%%a5)
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    lea 0x104000,%%a0                   | clear its old bubbles, if any
2:  cmp.l #0x%(foam)X,4(%%a0)
    bne.s 3f
    cmp.l 0x70(%%a0),%%a5
    bne.s 3f
    clr.b 0x28(%%a0)
    clr.l 0x70(%%a0)
3:  lea 0x80(%%a0),%%a0
    cmp.l #0x107000,%%a0
    bcs.s 2b
%(pieces)s1:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
    rts
""" % {"foam": foam, "pieces": pieces}, why="geyser foam: bubbles spawned when a geyser starts")
    rom.write(GEYSER_FIRST_RUN, bytes.fromhex("4EB9") + spawn.to_bytes(4, "big"), expect=bytes.fromhex("1B7C00010029"),
              why="geyser: spawn its bubbles on its first run")
