NAME = "boss-hits"
DESCRIPTION = "Bosses and mini bosses take more or fewer hits with the difficulty (LEVEL 1-8)"

# Each boss keeps the hits it can still take in the byte at +0x4013 of its object, counting down one per hit. It's
# set once as the boss starts (move.b #N,0x4013(a5)), the same at every difficulty. Each of those now looks up N in
# the boss's row of HITS by the difficulty (0x103063: 0-7, LEVEL 1-8). LEVEL 4, the game's default, keeps the
# original numbers.
#
# The jungle boss's second set-up is the game's mercy rule, one hit fewer after two lost tries. It now takes one
# fewer than his row, at least 1.
DIFFICULTY = 0x103063
HITS = [   # (set-up address, original N, hits at LEVEL 1..8, who)
    (0x28A3A, 5, [2, 3, 4, 5, 6, 7, 8, 9], "Jungle boss (caveman)"),
    (0x28A48, 4, [1, 2, 3, 4, 5, 6, 7, 8], "Jungle boss after two lost tries"),
    (0x2A4AA, 6, [2, 4, 5, 6, 7, 8, 10, 11], "Lower Earth Empire boss"),
    (0x2B066, 7, [2, 4, 6, 7, 8, 10, 11, 12], "Empire Marsh boss"),
    (0x32082, 8, [2, 4, 6, 8, 10, 11, 12, 12], "Mechanical City boss"),
    (0x3700A, 8, [2, 4, 6, 8, 10, 11, 12, 12], "Strange Space boss"),
    (0x36158, 5, [2, 3, 4, 5, 6, 7, 8, 9], "final boss"),
    (0x32B0E, 5, [2, 3, 4, 5, 6, 7, 8, 9], "Daruma Empire 1 mini boss"),
    (0x1DDFE, 3, [2, 2, 2, 3, 4, 4, 5, 5], "Daruma Empire 3 mini boss (frog)"),
    (0x38A90, 3, [2, 2, 2, 3, 4, 4, 5, 5], "Mechanical City mini boss"),
    (0x33A20, 8, [2, 4, 6, 8, 10, 11, 12, 12], "last level mini boss (robot)"),
]


def apply(rom):
    for at, n, row, who in HITS:
        if row[3] != n:
            raise SystemExit("boss-hits: %s - LEVEL 4 should keep the original %d" % (who, n))
        code = rom.place_code("""
    move.l %%a0,-(%%sp)
    move.w %%d0,-(%%sp)
    moveq #0,%%d0
    move.b 0x%(difficulty)X,%%d0        | the hits for this difficulty
    and.w #7,%%d0
    lea 1f(%%pc),%%a0
    move.b (%%a0,%%d0.w),0x4013(%%a5)
    move.w (%%sp)+,%%d0
    move.l (%%sp)+,%%a0
    rts
1:  .byte %(hits)s
""" % {"difficulty": DIFFICULTY, "hits": ",".join(str(h) for h in row)}, why="boss hits by difficulty: %s" % who)
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
                  expect=bytes.fromhex("1B7C%04X4013" % n), why="%s: hits by difficulty" % who)
