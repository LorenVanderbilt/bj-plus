NAME = "lottery-no-idle"
DESCRIPTION = "The lottery after a boss: Blue doesn't go into his idle fidget while it's on (the ocarina tune stays)"

# The user, 2026-11-06: standing through the gnomes' lines, Blue went into his idle fidget (bending down to pick
# something up), which looks odd in the middle of the lottery.
#
# Standing still, a hero counts down his idle timer (+0x7A, at 0x3C1C4); when it runs out IDLE_START picks the
# fidget (animation 0x2D), or the ocarina tune (0x2B) if he has the ocarina (OCARINA, in the block 0x106804 points
# to). In the lottery the fidget is skipped: the timer is set to run out again next frame and the hero goes on
# standing (STANDING, the path taken while it counts). The tune isn't: it's how Blue plays the song the lottery's
# host asks for when he has the ocarina (the lottery_song clip).
#
# The lottery is told by its objects: in a boss stage (STAGES) its scene's object sits in LOTTERY_SLOT with its code
# in LOTTERY_CODE (the lottery's routines, the ropes' among them: 0x29336, 0x29496 ... in every lottery's saves). Only
# looked at when the timer runs out, so ordinary frames cost nothing.
IDLE_START = 0x3C1CC          # moveq #45,d0 ; movea.l 0x6804(a6),a4
STANDING = 0x3C214            # the timer still counting: blinks and the rest of standing
IDLE_TIMER = 0x7A
STAGES = (33, 40)             # the boss stages (stage byte 0x103005)
STAGE = 0x103005
LOTTERY_SLOT = 0x104480       # object slot 9
LOTTERY_CODE = (0x29000, 0x2A000)
OCARINA = 0x2A                # byte in the block 0x106804 points to: the ocarina held


def apply(rom):
    code = rom.place_code("""
    cmpi.b #%(first)d,0x%(stage)X
    bcs 9f
    cmpi.b #%(last)d,0x%(stage)X
    bhi 9f
    move.l 0x%(slot)X+4,%%d0
    cmpi.l #0x%(lo)X,%%d0
    bcs 9f
    cmpi.l #0x%(hi)X,%%d0
    bcc 9f
    movea.l 0x106804,%%a4
    tst.b %(ocarina)d(%%a4)
    bne 9f                              | the ocarina: its tune, as before
    move.w #1,%(timer)d(%%a5)           | the lottery: no fidget, ask again next frame
    addq.l #4,%%sp
    jmp 0x%(standing)X
9:  moveq #45,%%d0
    movea.l 0x106804,%%a4
    rts
""" % {"first": STAGES[0], "last": STAGES[1], "stage": STAGE, "slot": LOTTERY_SLOT, "lo": LOTTERY_CODE[0],
       "hi": LOTTERY_CODE[1], "timer": IDLE_TIMER, "ocarina": OCARINA, "standing": STANDING},
        why="the lottery: no idle fidget")
    rom.write(IDLE_START, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("702D286E6804"),
              why="idle fidget: not in the lottery")
