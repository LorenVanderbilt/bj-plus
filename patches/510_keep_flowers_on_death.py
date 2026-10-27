NAME = "keep-flowers-on-death"
DESCRIPTION = "Losing a life no longer takes a quarter of the flowers; the riddle man's prize keeps them through a game over too"

# Losing a life took a quarter of the player's flowers (block +0x10: halved, then half of that added back) without a
# word - unless +0x1C was set (the riddle man's prize, was "FLOWERS WILL REMAIN EVEN AFTER DIE"). Each player's check
# (tst.b 0x1C(block) ; bne <past it>) now always skips it (SKIPS). The continue's quarter (0x3BA56) stays, skipped
# with the prize as before; the game over save's (SAVE_PENALTY, the save builder) is now skipped with the prize too -
# so the prize ("NEVER LOSE FLOWERS.", text-fixes) keeps them through a game over.
SKIPS = [0x11EA2, 0x124F8]   # bne.s past the penalty (player 1, player 2) -> bra.s
SAVE_PENALTY = 0xF00C        # move.b 16(a4),d0 ; lsr.b #1,d0 ; move.b d0,16(a4) ; lsr.b #1,d0 ; add.b d0,16(a4)
PRIZE = 0x1C


def apply(rom):
    for n, at in enumerate(SKIPS):
        rom.write(at, b"\x60\x12", expect=b"\x66\x12",
                  why="player %d: losing a life keeps the flowers" % (n + 1))
    original = bytes(rom.data[SAVE_PENALTY:SAVE_PENALTY + 16])
    assert original.hex() == "102c0010e2081940" "0010e208d12c0010", original.hex()
    code = rom.place_code("""
    tst.b %d(%%a4)
    bne 1f
    .word %s
1:  rts
""" % (PRIZE, ",".join("0x%02X%02X" % (original[i], original[i + 1]) for i in range(0, 16, 2))),
                          why="game over save: the riddle man's prize keeps the flowers")
    rom.write(SAVE_PENALTY, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71") * 5,
              expect=original, why="game over save: its flower penalty skipped with the riddle man's prize")
