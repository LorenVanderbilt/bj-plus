NAME = "no-idle-bird"
DESCRIPTION = "Remove the bird that flies in and nudges the hero after standing idle for a while"

# An idle counter (word at 0x1030BA) counts up every frame while nobody moves; the routine at 0x11888
# checks it. At 960 frames it spawns a blinking hint object (0x1198A, left alone here). At 1280 frames
# (0x1191A) it spawns the bird for each player that is in the game and not powered up (P1 object code
# 0x1EBEC, P2 0x1EC74), then zeroes the counter. Found by write-tapping the bird's object slot in MAME.
# The 1280-frame case now branches straight to the routine's existing "zero the counter and return"
# (0x11984), so the counter still restarts exactly as before, just without spawning the birds.
BIRD_CASE = 0x1191A
RESET_AND_RETURN = 0x11984


def apply(rom):
    offset = RESET_AND_RETURN - (BIRD_CASE + 2)
    rom.write(BIRD_CASE, bytes([0x60, offset]), expect=bytes.fromhex("082E"),
              why="bra.s to the counter reset instead of spawning the idle bird")
