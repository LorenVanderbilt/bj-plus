NAME = "score-before-sparkles"
DESCRIPTION = "Goal: the bonus score that zooms up from the screen's middle no longer loses pieces (the goal's sparkles give way)"

# Grabbing the goal, the height bonus (e.g. 7770: an object, 0x52EFE) zooms up from the screen's middle. A line of the
# screen shows 96 sprites at most - the first 96 by sprite number; the rest are dropped - and the score's lines carry
# the three background layers' strips (63), Blue, the stalk, the bells and their clappers, and goal-bend's sparkles:
# up to 102 there (2026-10-20, sta/aes/goal_bell.sta). The score was the front-most object (+0x28 = 1), so it had the
# highest sprites and pieces of it went missing, frame to frame. Now it's drawn just behind the sparkles (PRIORITY:
# above their 0x40, so drawn before them - the game sorts its objects by +0x28, higher first): they come after it -
# in front of it, and the first to go on a crowded line (a twinkle's sliver for a frame, not part of the number).
# Everything else at the goal (Blue 0x80, the bells 0x7F, the clappers) is drawn before it, as before.
# (It wasn't drawn too late: its writes end around line 110, its top is line 137.)
# (Drawing it first in sprites of its own, with the sparkles after, did the same but cost a frame at the goal - the
# busiest moment - and changed the round_clear replay.)
SET_PRIORITY = 0x52F10         # move.b #1,0x28(a5) - the score set up
PRIORITY = 0x41


def apply(rom):
    rom.write(SET_PRIORITY, bytes.fromhex("1B7C00%02X0028" % PRIORITY), expect=bytes.fromhex("1B7C00010028"),
              why="goal's bonus score: drawn just behind the sparkles")
