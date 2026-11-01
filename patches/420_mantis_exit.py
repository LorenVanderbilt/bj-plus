NAME = "mantis-exit"
DESCRIPTION = "Last level mini boss: after his farewell the mantis sinks all the way out of sight, then the scene fades out by itself"

# Beating the last level's mini boss (see sta/aes/boss_mantis.sta) runs a scene (mode 15) whose loop (0x2F0BA) runs
# until the text's done flag (0x107861) is set. The farewell line's callback (0x2F470) sends the mantis's portrait
# down at half a pixel a frame (object 0x104480, code 0x2F484), with the rest of the portrait (0x104500) and the
# sparks (0x105380) following it. But the flag ends the loop about 110 frames later, which stops the objects, and the
# scene then waited 30 frames (made a wait for a button by npc-wait) with his head still showing.
#
# Now, after the loop, the scene's objects are moved by hand (PARTS, SINK a frame) and drawn (0xA3A6) a frame at a
# time until the portrait is below GONE_Y, then for HOLD frames more, and then the scene fades out (0x15724) as
# before.
AFTER_LOOP = 0x2F0F6         # move.w #30,d0 ; jsr 0xE858
PORTRAIT = 0x104480
PARTS = [0x104480, 0x104500, 0x105380]
SINKING = 0x2F484
SINK = 64                    # y field per frame (half a pixel), as the callback set it
GONE_Y = 0x7400              # y field with his antennae below the top of the text box
HOLD = 20
MAX_FRAMES = 300
WAIT_FRAME, DRAW = 0xE856, 0xA3A6


def apply(rom):
    moves = "".join("    subi.w #%d,0x%X\n" % (SINK, a) for a in PARTS)
    code = rom.place_code(r"""
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    cmpi.l #0x%(sinking)X,0x%(portrait)X+4
    bne 2f
    move.w #%(max)d,%%d7
1:  cmpi.w #0x%(gone)X,0x%(portrait)X
    bls 2f
%(moves)s
    jsr 0x%(draw)X
    jsr 0x%(wait)X
    dbf %%d7,1b
2:  move.w #%(hold)d,%%d0
    jsr 0xE858
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
    rts
""" % {"max": MAX_FRAMES, "sinking": SINKING, "portrait": PORTRAIT, "gone": GONE_Y, "moves": moves,
       "hold": HOLD, "draw": DRAW, "wait": WAIT_FRAME},
        why="mantis farewell: he sinks out of sight before the fade")
    rom.write(AFTER_LOOP, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("303C001E4EB90000E858"), why="mantis farewell: run on until he's gone")
