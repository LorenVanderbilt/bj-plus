NAME = "lottery-no-attack"
DESCRIPTION = "The lottery after a boss: A does nothing (no leaf, boomerang or acorn thrown in front of the host)"

# The user, 2026-11-11: in the lottery, a leaf thrown (and gone, often as a rope is grabbed) tore the top of the
# picture for a frame or two, on the TV and in MAME (leaf_static, leaf_rope): the leaf's object going away moves every
# later hardware sprite down a slot, the host's picture among them, and the game rewrites them while the top of the
# picture is drawn. There's nothing to hit in the lottery, so A is switched off there instead.
#
# A press reaches ATTACKS through the hero states' button tables (0x3E794 picks the A column): one on the ground, one
# in the air, each starting the same way. In the lottery (lottery-no-idle's test: a boss stage with a lottery routine in its object slot) it returns as an
# empty table slot does (NOTHING: d0 = 0, no action); anywhere else it goes on as before. Only a press of A runs it.
ATTACKS = [0x3CDEA, 0x3CFDC]  # on the ground, in the air: movea.l 0x6804(a6),a4 ; tst.b 4(a4) (carrying?) ; beq ...


def apply(rom):
    lot = rom.other_patch("lottery-no-idle")
    for at in ATTACKS:
        code = rom.place_code("""
    cmpi.b #%(first)d,0x%(stage)X
    bcs 9f
    cmpi.b #%(last)d,0x%(stage)X
    bhi 9f
    cmpi.l #0x%(lo)X,0x%(slot)X+4         | (registers as they were for the attack, if it goes on)
    bcs 9f
    cmpi.l #0x%(hi)X,0x%(slot)X+4
    bcc 9f
    moveq #0,%%d0                       | the lottery: no attack (as an empty table slot)
    rts
9:  movea.l 0x106804,%%a4
    tst.b 4(%%a4)
    jmp 0x%(rest)X
""" % {"first": lot.STAGES[0], "last": lot.STAGES[1], "stage": lot.STAGE, "slot": lot.LOTTERY_SLOT,
           "lo": lot.LOTTERY_CODE[0], "hi": lot.LOTTERY_CODE[1], "rest": at + 8}, why="the lottery: A does nothing")
        rom.write(at, bytes.fromhex("4EF9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex("286E68044A2C0004"), why="Blue's attack: not in the lottery")
