NAME = "score-before-sparkles"
DESCRIPTION = "Goal: the bonus score that zooms up from the screen's middle no longer loses pieces (the goal's sparkles give way)"

# When the goal is grabbed, the height bonus (for example 7770, object 0x52EFE) zooms up from the middle of the
# screen. The hardware shows at most 96 sprites on a line, the first 96 by sprite number, and drops the rest. The
# score's lines carry the three background layers' strips (63), Blue, the stalk, the bells and clappers, and
# goal-bend's sparkles: up to 102 (measured 2026-10-20 with sta/aes/goal_bell.sta). The score was the front-most
# object (+0x28 = 1), so it got the highest sprite numbers and pieces of it went missing from frame to frame.
#
# The game sorts objects by +0x28, higher first. The score is now set just above the sparkles' 0x40 (PRIORITY), so
# it's drawn before them. The sparkles come after it, in front, and are the first to go on a crowded line, which
# loses a sliver of a twinkle for a frame rather than part of the number. Everything else at the goal (Blue 0x80,
# the bells 0x7F, the clappers) is still drawn before it.
#
# Timing wasn't the problem: its writes end around line 110 and its top is at line 137. Drawing it first in sprites
# of its own, with the sparkles after, also worked but cost a frame at the goal, the busiest moment, and changed the
# round_clear replay.
SET_PRIORITY = 0x52F10         # move.b #1,0x28(a5), in the score's set-up
PRIORITY = 0x41


def apply(rom):
    rom.write(SET_PRIORITY, bytes.fromhex("1B7C00%02X0028" % PRIORITY), expect=bytes.fromhex("1B7C00010028"),
              why="goal's bonus score: drawn just behind the sparkles")
