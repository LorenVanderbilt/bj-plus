NAME = "no-lotto-prompt-timer"
DESCRIPTION = "Lottery after a boss: no time limit on LET'S PLAY! / NO THANKS. (the next stage's still sends you off)"

# The lottery's countdown is the word at 0x1078BC, ticked by an object (0x29F70) that, at 0, cancels the choice and
# says TIME IS MONEY., ending the lottery. It's set to 320 frames (~5 s) when the host asks whether to play
# (0x296C6), then to 640 (~11 s) for the next stage (0x2975E). The first is now 0xFFFF (~18 minutes, the value
# the game itself uses for "off", e.g. 0x29A3E); the second, and its TIME IS MONEY., stay.
PROMPT_TIMER = 0x296C6      # move.w #320,0x78BC(a6)


def apply(rom):
    rom.write(PROMPT_TIMER + 2, bytes.fromhex("FFFF"), expect=(320).to_bytes(2, "big"),
              why="lottery: no time limit on the play / pass choice")
