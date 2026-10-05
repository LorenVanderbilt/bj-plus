NAME = "shorter-spawn-blink"
DESCRIPTION = "The hero blinks (can't be hurt) for 2 s after appearing at a stage's start or after dying, not 2.7 s"

# Appearing (a stage's start, a restart after a death) sets the hero's invincibility timer, +9 of the player's
# data (0x107009 / 0x107409, counted down a frame at a time; the hero blinks meanwhile), to 160 frames - in three
# places: the general set-up (9(a4)) and player 1's and player 2's. Now SPAWN_BLINK.
SPAWN_BLINK = 120
SITES = [(0x3BAA8, "197C00A00009"), (0x3BB12, "1D7C00A07009"), (0x3BC08, "1D7C00A07409")]


def apply(rom):
    for at, old in SITES:
        rom.write(at + 3, bytes([SPAWN_BLINK]), expect=bytes.fromhex(old)[3:4],
                  why="hero appearing: blinks %d frames (was 160)" % SPAWN_BLINK)
