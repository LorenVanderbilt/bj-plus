NAME = "keep-flowers-on-death"
DESCRIPTION = "Losing a life no longer takes a quarter of the flowers (continuing still does)"

# Losing a life took a quarter of the player's flowers (block +0x10: halved, then half of that added back) without a
# word - unless +0x1C was set (the quiz man's prize, "FLOWERS WILL REMAIN EVEN AFTER DIE"). Each player's check
# (tst.b 0x1C(block) ; bne <past it>) now always skips it. The continue's quarter (0x3BA56) and the game over save's
# (0xF00C) are left as they are.
SKIPS = [0x11EA2, 0x124F8]   # bne.s past the penalty (player 1, player 2) -> bra.s


def apply(rom):
    for n, at in enumerate(SKIPS):
        rom.write(at, b"\x60\x12", expect=b"\x66\x12",
                  why="player %d: losing a life keeps the flowers" % (n + 1))
