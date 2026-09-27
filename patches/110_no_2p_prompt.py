NAME = "no-2p-prompt"
DESCRIPTION = "Remove the blinking 2P \"PUSH START\" / \"INSERT COIN\" prompt in the top right of the HUD"

# While player 2 is not in the game, the HUD code at 0x11CBA redraws the top-right corner every 32 frames
# (fix layer 0x7323-0x7325), alternating on bit 5 of the frame counter between blanks (0x11CE6) and
# "2P" + "PUSH START" or "INSERT COIN" (0x11D50) - the blink. The branch to the text half now never
# happens, so the corner stays blank. Player 2 can still join with their Start button as before.
BLINK_BRANCH = 0x11CE2   # bne 0x11D50


def apply(rom):
    rom.write(BLINK_BRANCH, bytes.fromhex("4E714E71"), expect=bytes.fromhex("6600006C"),
              why="2P prompt: always draw the blank half of the blink")
