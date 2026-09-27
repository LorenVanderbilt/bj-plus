NAME = "no-join-prompts"
DESCRIPTION = "Remove the blinking 1P / 2P \"PUSH START\" / \"INSERT COIN\" prompts in the top corners of the HUD"

# While a player is not in the game, the HUD code at 0x11B3C (player 1, top left, fix layer 0x7023-0x7025)
# and 0x11CBA (player 2, top right, 0x7323-0x7325) redraws that corner every 32 frames, alternating on bit 5
# of the frame counter between blanks and "1P"/"2P" + "PUSH START" or "INSERT COIN" - the blink. The branch
# to the text half now never happens, so the corner stays blank. Either player can still join with their
# Start button as before.
BLINK_BRANCHES = [
    (0x11B64, "66000070", "1P"),   # bne 0x11BD6
    (0x11CE2, "6600006C", "2P"),   # bne 0x11D50
]


def apply(rom):
    for addr, orig, who in BLINK_BRANCHES:
        rom.write(addr, bytes.fromhex("4E714E71"), expect=bytes.fromhex(orig),
                  why="%s prompt: always draw the blank half of the blink" % who)
