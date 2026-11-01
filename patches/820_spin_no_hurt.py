NAME = "spin-no-hurt"
DESCRIPTION = "A kicked, spinning enemy no longer hurts the hero after it bounces off a wall"

# Jumping on an enemy kicks it away spinning (0x46B06). It runs SPIN_CODE with state 4 (+0x400F), which the hero's
# touch test ignores. When it bounces off a wall (0x46C28) its state becomes 5, and the touch test (HURT_TEST, where
# states 0 and 5 hurt) treats it as a live enemy. A spinning enemy stuck bouncing in a ditch could hurt the hero
# forever (sta/aes/spin_ditch.sta).
#
# A state-5 enemy still running SPIN_CODE is now ignored too. Other objects that use state 5 still hurt.
HURT_TEST = 0x42B54            # cmpi.b #5,d7 ; beq 0x42B9A (hurt), with d7 = state, a0 = the enemy
HURT = 0x42B9A
SPIN_CODE = 0x46B42


def apply(rom):
    code = rom.place_code("""
    cmpi.b #5,%%d7
    bne 9f
    cmpi.l #0x%(spin)X,4(%%a0)          | a kicked, spinning enemy doesn't hurt
    beq 1f
    addq.l #4,%%sp
    jmp 0x%(hurt)X
1:  moveq #9,%%d7
9:  rts
""" % {"spin": SPIN_CODE, "hurt": HURT}, why="spinning enemies: no hurt")
    rom.write(HURT_TEST, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("0C0700056740"),
              why="the hero's touch of an enemy: a kicked, spinning one doesn't hurt")
