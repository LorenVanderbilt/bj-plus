NAME = "spin-no-hurt"
DESCRIPTION = "A kicked, spinning enemy no longer hurts the hero after it bounces off a wall"

# Jump on an enemy and off again and it's kicked away spinning (0x46B06: code SPIN_CODE, its state - +0x400F - 4,
# which the hero's touch test passes over). When it bounces off a wall (0x46C28) its state becomes 5, which the test
# (HURT_TEST, the hero's touch of each enemy: state 0 or 5 hurts) treats as a live enemy - so a spinning enemy stuck
# in a ditch, bouncing wall to wall, hurt the hero forever (sta/aes/spin_ditch.sta). Now a state-5 enemy still on
# SPIN_CODE is passed over too (as any other state but 0, 1 and 5); state 5 elsewhere (other objects set it) still
# hurts. (Its own patch, last, so its code moves nothing.)
HURT_TEST = 0x42B54            # cmpi.b #5,d7 ; beq 0x42B9A (the hurt) - d7 the enemy's state, a0 the enemy
HURT = 0x42B9A
SPIN_CODE = 0x46B42


def apply(rom):
    code = rom.place_code("""
    cmpi.b #5,%%d7
    bne 9f
    cmpi.l #0x%(spin)X,4(%%a0)          | a kicked enemy, spinning: passed over (d7: no hurt below)
    beq 1f
    addq.l #4,%%sp
    jmp 0x%(hurt)X
1:  moveq #9,%%d7
9:  rts
""" % {"spin": SPIN_CODE, "hurt": HURT}, why="spinning enemies: no hurt")
    rom.write(HURT_TEST, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("0C0700056740"),
              why="the hero's touch of an enemy: a kicked, spinning one doesn't hurt")
