NAME = "wheel-smooth"
DESCRIPTION = "Mechanical City's turning wheels (platforms, hub) and the sunken wheel's gondolas move every frame, not in 2-3 pixel steps every other"

# 0x5E4F2 places an object around its parent (d0, d1 = the parent's position) at its radius (+0x38, a byte) and
# angle (+0x3A, a word with 256 steps a turn in its top byte), then turns it (+0x3A += +0x3E, +0x38 += +0x3C). The
# position only uses the angle's top byte (0x5E55C: a sine table times the radius, added to d0 / d1), and the wheel
# turns half a step a frame, so its platforms moved 2-3 pixels every other frame. The routine also skipped the sum
# when the step hadn't changed (+0x47).
#
# SMOOTH works out the positions at this step and the next and interpolates between them by the angle's low byte:
# the same circle at the same speed, moving a little every frame. Only the wheels' calls (CALLS) go through it, out
# of 0x5E4F2's 36 callers, which include the goal's vine.
CALLS = [0x50904, 0x5096A,          # jsr 0x5E4F2: Mechanical City's turning wheels, hub pieces and platforms
         0x316BA]                   # the sunken wheel's gondolas (object 0x3164A, by the water)
PLACE, SINE_SUM = 0x5E4F2, 0x5E55C


def apply(rom):
    smooth = rom.place_code("""
    movem.l %%d2-%%d7,-(%%sp)
    bclr #0,0x47(%%a5)                  | the old routine's skip flag, no longer needed
    move.w %%d0,%%d4                     | the parent's position
    move.w %%d1,%%d5
    move.b 0x38(%%a5),%%d2
    ext.w %%d2
    moveq #0,%%d3
    move.b 0x3A(%%a5),%%d3              | this step
    jsr 0x%(sum)X
    move.w %%d0,-(%%sp)
    move.w %%d1,-(%%sp)
    move.w %%d4,%%d0
    move.w %%d5,%%d1
    move.b 0x38(%%a5),%%d2
    ext.w %%d2
    moveq #0,%%d3
    move.b 0x3A(%%a5),%%d3
    addq.b #1,%%d3                      | the next step
    jsr 0x%(sum)X
    move.w (%%sp)+,%%d5                  | this step's position
    move.w (%%sp)+,%%d4
    moveq #0,%%d2
    move.b 0x3B(%%a5),%%d2              | how far between them, in 256ths
    sub.w %%d4,%%d0
    muls.w %%d2,%%d0
    asr.l #8,%%d0
    add.w %%d4,%%d0
    sub.w %%d5,%%d1
    muls.w %%d2,%%d1
    asr.l #8,%%d1
    add.w %%d5,%%d1
    move.w %%d0,(%%a5)
    move.w %%d1,2(%%a5)
    move.w 0x3C(%%a5),%%d0              | turn, as before
    add.w %%d0,0x38(%%a5)
    move.w 0x3E(%%a5),%%d1
    beq 1f
    add.w %%d1,0x3A(%%a5)
1:  movem.l (%%sp)+,%%d2-%%d7
    rts
""" % {"sum": SINE_SUM}, why="wheel: places between the angle's steps")
    for at in CALLS:
        rom.write(at, bytes.fromhex("4EB9") + smooth.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + PLACE.to_bytes(4, "big"), why="wheel: placed smoothly")
