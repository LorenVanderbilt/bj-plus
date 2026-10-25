NAME = "leaf-gusts"
DESCRIPTION = "Leaf level 2: its gust of wind along the ground comes as a burst - a second crescent trailing the first"

# The level 2 leaf, once down, sends a gust along the ground: the leaf object's own frames GUST (player 1's; player
# 2's are copies in their leaf palette, found by their bytes) - the landed leaf (a 2 x 2 grid) and the gust, a
# crescent of wind as two one-column pieces (see 0xAF1C: rows - 1, x and up in 2 px units, palette, the tile number's
# high byte, the low bytes) further out each frame, cycling through 3 drawings. A thin crescent, it was easy to miss.
# Now each frame has TRAIL more crescents behind it - each SPACING further back, a drawing behind (so they spin out
# of step), RISE higher, coming in DELAY frames apart - a burst of wind; the leaf's hit (the object) is as before.
# Data only: the frames' definitions copied with the pieces added. (Its own patch, last: nothing moves.)
GUST = [0x2A0, 0x2A4, 0x2A8, 0x2AC, 0x2B0, 0x2B4]
FRAME_TABLE = 0x60772
TRAIL = 1
SPACING = 6                    # 2 px units behind the one before
RISE = 1                       # 2 px units higher than the one before
DELAY = 3                      # frames of GUST between one coming in and the next


def parse(rom, p):
    """(head: the grid's bytes, pieces: [(x, up, palette, hi, [low bytes])], end)"""
    cols, rows = rom.data[p] + 1, rom.data[p + 1] + 1
    q = p + 5 + cols * rows
    assert all(b > 1 or b == 0 for b in rom.data[p + 5:q]), "leaf-gusts: a grid with tile escapes"
    head = bytes(rom.data[p:q])
    pieces = []
    while rom.data[q] != 0xFF:
        n = rom.data[q] + 1
        x, up, pal, hi = rom.data[q + 1:q + 5]
        lows = list(rom.data[q + 5:q + 5 + n])
        assert all(b > 1 for b in lows)
        pieces.append((x, up, pal, hi, lows))
        q += 5 + n
    return head, pieces


def build(head, pieces):
    body = bytearray(head)
    for x, up, pal, hi, lows in pieces:
        body += bytes([len(lows) - 1, x & 0xFF, up & 0xFF, pal, hi]) + bytes(lows)
    return bytes(body) + b"\xFF"


def apply(rom):
    defs = [rom.u32(FRAME_TABLE + f) for f in GUST]
    parsed = [parse(rom, p) for p in defs]
    # player 2's copies: frames whose definitions are player 1's with another palette byte
    players = [GUST]
    first = bytes(rom.data[defs[0]:defs[0] + 32])
    for f in range(0, 0x4000, 4):
        p = rom.u32(FRAME_TABLE + f)
        if f in GUST or not 0x60000 <= p < 0xF0000:
            continue
        cand = bytes(rom.data[p:p + 32])
        if cand[:3] == first[:3] and cand[4:9] == first[4:9] and cand[3] != first[3]:
            two = [f + 4 * i for i in range(len(GUST))]
            try:
                theirs = [parse(rom, rom.u32(FRAME_TABLE + g)) for g in two]
            except (AssertionError, IndexError):
                continue
            if all([pc[4] for pc in theirs[i][1]] == [pc[4] for pc in parsed[i][1]] for i in range(len(two))):
                players.append(two)
    assert len(players) == 2, "leaf-gusts: player 2's gust frames not found (%d sets)" % len(players)
    for frames in players:
        mine = [parse(rom, rom.u32(FRAME_TABLE + f)) for f in frames]
        for i, f in enumerate(frames):
            head, pieces = mine[i]
            extra = []
            for k in range(1, TRAIL + 1):
                j = i - k * DELAY                      # the drawing (and place) it trails with
                if j < 0:
                    continue
                for (x, up, pal, hi, lows), (_, _, _, _, older) in zip(pieces, mine[j][1]):
                    sx = x if x < 0x80 else x - 0x100
                    su = up if up < 0x80 else up - 0x100
                    extra.append((sx + SPACING * k, su + RISE * k, pal, hi, older))
            body = build(head, pieces + extra)
            at = rom.alloc(len(body))
            rom.data[at:at + len(body)] = body
            rom.write(FRAME_TABLE + f, at.to_bytes(4, "big"), expect=rom.u32(FRAME_TABLE + f).to_bytes(4, "big"),
                      why="leaf level 2: frame 0x%X's gust with %d trailing" % (f, len(extra) // max(1, len(pieces))))
