NAME = "three-hearts"
DESCRIPTION = "Start with 3 hearts instead of 2 on the easiest three difficulty levels"

# At boot the difficulty soft-DIP (0x10FD8C, 0-7) picks the starting number of hearts from the table at
# 0x13500 (0x134E2), stored in 0x103C03; a new game (and a player joining, 0x3B942/0x3B948) copies it
# into the player's maximum hearts (player block +0x20), and the current hearts (+0x11) are filled from
# that. The table held 2 hearts for difficulties 0-4 and 1 for the hardest three (5-7); LEVEL 1-3 (0-2) now
# get one more, 3 - the rest are as in the original. The heart-container item still raises the maximum up to
# the game's cap of 5, which the HUD can show. (The identical table at 0x134F8, stored in 0x103C02, is never
# read.) The difficulty can be chosen in the title menu's options (`title-menu`).
START_HEARTS = 0x13500


def apply(rom):
    rom.write(START_HEARTS, bytes([3, 3, 3, 2, 2, 1, 1, 1]), expect=bytes([2, 2, 2, 2, 2, 1, 1, 1]),
              why="starting hearts per difficulty: 3 on LEVEL 1-3 (was 2), the rest as in the original")
