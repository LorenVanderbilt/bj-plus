NAME = "shorter-spawn-blink"
DESCRIPTION = "The hero blinks (can't be hurt) for 2 s after appearing at a stage's start or after dying, not 2.7 s; none in a boss room"

# Appearing (a stage's start, a restart after a death) sets the hero's invincibility timer, +9 of the player's
# data (0x107009 / 0x107409, counted down a frame at a time; the hero blinks meanwhile), to 160 frames - in three
# places: the general set-up (9(a4)) and player 1's and player 2's. Now SPAWN_BLINK - and none in a boss room
# (stages 33-40: you walk in from the cave, the boss isn't upon you). After a title card stage-wipe clears it: the
# blink is only after a death.
SPAWN_BLINK = 120
BOSS_STAGES = (33, 40)
STAGE = 0x103005
SITES = [(0x3BAA8, "197C00A00009", "0x9(%a4)"), (0x3BB12, "1D7C00A07009", "0x7009(%a6)"),
         (0x3BC08, "1D7C00A07409", "0x7409(%a6)")]


def apply(rom):
    for at, old, dest in SITES:
        code = rom.place_code(
            "    move.b #%d,%s\n"
            "    cmpi.b #%d,0x%X\n"
            "    bcs 1f\n"
            "    cmpi.b #%d,0x%X\n"
            "    bhi 1f\n"
            "    clr.b %s\n"
            "1:  rts\n" % (SPAWN_BLINK, dest, BOSS_STAGES[0], STAGE, BOSS_STAGES[1], STAGE, dest),
            why="hero appearing: blinks %d frames, none in a boss room" % SPAWN_BLINK)
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex(old),
                  why="hero appearing: the blink (none in a boss room)")
