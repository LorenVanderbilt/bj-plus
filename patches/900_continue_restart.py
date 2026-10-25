NAME = "continue-restart"
DESCRIPTION = "A continue starts the level again from its beginning (not the last checkpoint) - boss fights excepted"

# The continue screen's YES (CONTINUE_YES: its last call before returning 1 - screen-blackout's cont_out) leads back
# into the stage through mode 0 (the stage's start, 0x113BC), which puts the hero at a restart point if there is one:
# RESTART_POINTS (each player's checkpoint, the way back out of a cave - longs, 0 = none). Now, unless the stage is a
# boss fight (BOSS_STAGES), they're cleared first - as pause-menu's RESTART LEVEL and the game's own stage select do -
# so the stage starts again from its beginning. A boss fight keeps them: the continue goes back to the boss.
# (Its own patch, last, so its code moves nothing.)
CONTINUE_YES = 0x34816         # jsr <screen-blackout's cont_out> ; ... moveq #1,d0 ; rts
RESTART_POINTS = [0x107100, 0x107500, 0x103024]
STAGE = 0x103005
BOSS_STAGES = (33, 40)         # (first, last)


def apply(rom):
    assert rom.u16(CONTINUE_YES) == 0x4EB9
    before = rom.u32(CONTINUE_YES + 2)
    clears = "".join("    clr.l 0x%X\n" % a for a in RESTART_POINTS)
    code = rom.place_code("""
    cmpi.b #%(first)d,0x%(stage)X
    bcs 1f
    cmpi.b #%(last)d,0x%(stage)X
    bls 2f                              | (a boss fight: back to the boss)
1:
%(clears)s2:  jmp 0x%(before)X
""" % {"first": BOSS_STAGES[0], "last": BOSS_STAGES[1], "stage": STAGE, "clears": clears, "before": before},
        why="continue: back to the stage's beginning (not a boss fight)")
    rom.write(CONTINUE_YES + 2, code.to_bytes(4, "big"), expect=before.to_bytes(4, "big"),
              why="continue YES: the restart points forgotten first")
