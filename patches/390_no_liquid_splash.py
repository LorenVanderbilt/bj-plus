NAME = "liquid-sink"
DESCRIPTION = "Daruma Empire 1's yellow liquid: no splash when Blue falls in; sinking (in it or water) he keeps his size"

# Falling into the yellow liquid (hero state 0x25; in sta/aes/liquid_fall.sta, walk right off the ledge) hides the
# hero and makes two objects: a splash at the surface (palette 0x54) and a sinking Blue (animation 0x33). The sinker
# isn't a hero object, so the big art doesn't cover it and it used the small art's frames 0x100-0x10C: Blue shrank
# as he went in. Normal and big Blue run 0x3DED0 (water, state 0x24, runs the same at 0x3DDCE without the palette);
# mini Blue runs 0x4033E.
#
# The yellow liquid's splash is now skipped by branching straight to the sinker's set-up. The sinker (0x3DE76) plays
# the big form's animation (art set BIG_SET: frames 0x3C0 / 0x3C4) unless the player is mini.
SPLASHES = [(0x3DEF4, 0x3DF1E), (0x40362, 0x4038C)]   # the splash's jsr 0x10070 (new object), the sinker's
SINK_ANIM = 0x3DE7E          # moveq #0x33,d0 ; jsr 0x43480
SET_ANIM = 0x43480
PLAYER = 0x106804            # long: the current player's data; +1 is the form, 0 = mini
BIG_SET = 0x80


def apply(rom):
    for at, to in SPLASHES:
        rom.write(at, bytes([0x60, to - (at + 2)]), expect=bytes.fromhex("4EB9"), why="yellow liquid: no splash")
    code = rom.place_code(r"""
    moveq #0x33,%%d0
    jsr 0x%(set_anim)X
    move.l %%a0,-(%%sp)
    movea.l 0x%(player)X,%%a0
    tst.b 1(%%a0)
    beq 1f
    move.w #0x%(big)X,0x62(%%a5)        | not mini: the big form's sinking
1:  movea.l (%%sp)+,%%a0
    rts
""" % {"set_anim": SET_ANIM, "player": PLAYER, "big": BIG_SET}, why="sinking: Blue keeps his size")
    rom.write(SINK_ANIM, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("70334EB900043480"), why="sinking: the big form's animation unless mini")
