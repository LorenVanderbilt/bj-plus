NAME = "hud"
DESCRIPTION = "HUD: no LIFE; score, flowers (x000) and hearts at the screen's edges; the timer as a column; the lives (each player's colours) by the item bar, which is a row higher"

# LIFE: each player's hearts routine (player 1 0x4EA7C, player 2 0x4EAA2) draws it beside them as two 2x2 blocks of
# fix tiles (from 0x4EAC8) after the hearts: each routine now returns after the hearts (LIFE_DRAWN) - and the
# hearts take its place at the screen's edges (HEARTS_AT: player 1's drawn rightwards from column 1, player 2's leftwards from
# column 37; they were at 5 / 33). OLD_HEART_CELLS, where the hearts reached before, are cleared too.
# The timer (0x4E560: as normal, or blinking when time is short) drew TIME at fix offset 0x201 (column 16; the
# big-font printers put text 2 rows down: row 3), = at 0x281 and the time at 0x2A1: TIME=287 on one line. Now
# TIME at TIME_AT (columns 18-21, rows 3-4) and the time under it at DIGITS_AT (columns 19-21, rows 5-6), no =; the
# = call's place clears the old layout's cells nothing draws now (OLD_CELLS: TI and the last digits stayed on
# screen from a save state made before).
# The flowers: each player's count (block +0x10) was drawn at the bottom, by the item bar (player 1's 0x4E99C at row
# 27, columns 2-6: flower = and the number, leading zeros blank; player 2's 0x4E9D0, columns 33-37). Now under the
# score, above the hearts (row 4), flower x and always 3 digits (000): each routine jumps to `flowers`; the old
# cells (OLD_FLOWER_CELLS) are cleared with the rest. For 2 pixels' room above and below, the score line is drawn 2
# pixels higher and the hearts 6 (SCORE, HEARTS_SHIFTED - their glyphs as new shifted fix tiles).
FLOWERS = [(0x4E99C, 0x7000 + 1 * 32 + 4), (0x4E9D0, 0x7000 + 34 * 32 + 4)]   # (routine, where its icon goes: row 4)
FLOWER_ICON, TIMES, DIGIT_0 = 0x442F, 0x552A, 0x5530
# The x in the flowers and the lives: the font's (TIMES) with each arm a pixel shorter, the crossing where it was.
SMALL_X = ["........",
           "........",
           ".A22A22A",
           "..A111A.",
           "..A222..",
           ".A33A33.",
           "..AA.AA.",
           "........"]
TO_DECIMAL = 0x4D8B6         # d0 -> d1: its decimal digits (BCD)
OLD_FLOWER_CELLS = []        # (by the item bar, row 27: the bar's top row now - it draws over them)
# The lives (the hero's face, x and the count): player 1's 0x4EA04 at row 3, columns 12-14; player 2's 0x4EA3A at
# columns 25-27 - now on the flowers' line, a space on (player 1: columns 7-9; player 2: 30-32, a space before its
# flowers), drawn by `lives`. As before only the count's last digit shows.
LIVES = [(0x4EA04, 0x7000 + 7 * 32 + 4), (0x4EA3A, 0x7000 + 30 * 32 + 4)]   # (routine, where the face goes)
# The item bar (rows 28-29) a row higher, off the screen's bottom edge (TVs crop it): its frame (inline strings at
# 0x9FE2 calls), the markers over it (row 27) and each player's boxes (their base fix address) - each address one
# row up (BAR); row 29, its old bottom row, cleared.
BAR = [0x4E5EE, 0x4E5FC, 0x4E60C, 0x4E61A,                    # the frame
       0x4E632, 0x4E640, 0x4E656, 0x4E664, 0x4E67A, 0x4E68C, 0x4E6A6, 0x4E6B8,   # the markers over it
       0x4E6DE, 0x4E70A]                                      # the boxes (addi.w #base,d0)
BAR_OLD_ROW = [0x7000 + c * 32 + 29 for c in range(40)]
# The face was purple (fix palette 3's entries 10-12, its suit) for both players: now each player's suit - player 1's
# blues (as the hero's palette 0x10) in palette 3; player 2's face in palette 7 (unused on the HUD: Red's colours),
# its suit made player 2's greens (palette 0x11) and its outline palette 3's. FIX_PALETTES: the fix palettes' table
# (loaded with a stage); `lives` also puts them in the palette RAM as it draws (a save state's are the old ones).
FIX_PALETTES = 0x1000
FACE_COLOURS = [(3, 10, "897F C63D C50A", "B08F F04F 201E"),            # (palette, first entry, old, new)
                (7, 3, "EFB0 8F91 9F70", "4FD0 6F90 8C60"), (7, 10, "BC38 0A27 1805", "B0F9 A0D4 11A1")]
FACES = [0x3400, 0x7400]     # (each player's face: palette 3 / 7)
LIVES_SHIFT = 4
OLD_LIVES_CELLS = [0x7000 + c * 32 + 3 for c in (12, 13, 14, 25, 26, 27)] + \
                  [0x7000 + c * 32 + r for c in (2, 3, 4, 33, 34, 35) for r in (25, 26)]   # (by the item bar before)
LIFE_DRAWN = [0x4EA84, 0x4EAAA]   # lea <LIFE's tiles>(pc),a0 - after the hearts (player 1, 2): rts instead
BLANK = 0x5520
HEARTS_AT = [(0x4EA7C, 0x70A4, 0x7026), (0x4EAA2, 0x7424, 0x74A6)]   # (move.w #fix address,d0, old, new: rows 6-7)
OLD_HEART_CELLS = [0x7000 + c * 32 + r for c in (11, 12, 13, 14, 25, 26, 27, 28) for r in (4, 5)] + \
                  [0x7000 + c * 32 + 4 for c in (6, 10, 29, 33)] + \
                  [0x7000 + c * 32 + 7 for c in list(range(1, 11)) + list(range(29, 39))]   # (beside the flowers;
                  # the hearts' second row before they were raised)
# The hearts' 2x2 blocks (0x4E8CC, from the tables HEART_TABLES: full, empty, none) drawn 6 pixels higher: rows 5-6
# from a row-6 address (the draw `blocks` in its place for those tables; the hearts are 13 pixels tall: nothing in
# a third row).
BLOCK = 0x4E8CC              # movem.l d0/a0,-(sp) ; move.w d0,0x3C0000 ; ... (a 2x2 block of fix tiles, a0 = them)
HEART_TABLES = [0x4EBAC, 0x4EBB4, 0x4EBBC]
HEARTS_UP = 6
# The score line (player 1's 0x4E954: 6 digits from 0x1030A1, leading zeros blank, at column 4, then 1P= at 1;
# player 2's 0x4E978: from 0x1030A5 at 33, 2P= at 30) drawn 2 pixels higher by `score`: each glyph as two shifted
# tiles, its top in row 2 and the rest in row 3.
SCORE = [(0x4E954, 0x1030A1, 0x7000 + 4 * 32 + 3, 0x7000 + 1 * 32 + 3, 0x5531),
         (0x4E978, 0x1030A5, 0x7000 + 33 * 32 + 3, 0x7000 + 30 * 32 + 3, 0x5532)]   # (routine, BCD, digits, label, its digit)
SCORE_UP = 2
P_TILE, EQUALS_TILE = 0x5550, 0x5508
TIMER = [   # (the move.w #offset,d0 before each printer call, its old offset): normal, then blinking
    (0x4E57A, 0x2A1, "the time"), (0x4E58E, 0x201, "TIME"),
    (0x4E5B0, 0x2A1, "the time (blinking)"), (0x4E5C4, 0x201, "TIME (blinking)"),
]
EQUALS = [0x4E59C, 0x4E5C6 + 0xC]     # move.w #0x281,d0 ; move.w #'=',d1 ; jsr 0x5F0EA - each 14 bytes
OLD_CELLS = [0x7000 + c * 32 + r for c in (16, 17, 23) for r in (3, 4)]
HUD_BLANK = 0x0520           # (the top rows' blank round the timer)
TIME_AT = 18 * 32 + 1
# ... and TIME half a tile right, so the 3 digits sit under its middle (the fix layer moves in 8-pixel columns): its
# big-font letters (TIME_LETTERS: top tiles, the bottom ones 0x10 on) redrawn shifted 4 pixels as 5 new fix tiles a
# row (columns 18-22), drawn by `time_word` in place of the printer's call (TIME_PRINTS; d2 = its palette).
TIME_LETTERS = [0x6A4, 0x689, 0x68D, 0x685]
TIME_PRINTS = [0x4E596, 0x4E5CC]      # jsr 0x4DDEE (the big-font printer: TIME)
TIME_COLUMN = 0x7000 + 18 * 32 + 3
DIGITS_AT = 19 * 32 + 3




def fix_pixels(rom, tile):
    at = tile * 32
    return [[rom.fix_orig[at + rom.FIX_COLUMN_BYTE[x] + y] >> (0 if x % 2 == 0 else 4) & 15 for x in range(8)]
            for y in range(8)]


def time_tiles(rom):
    """TIME's 2 rows, 4 pixels right: 5 new fix tiles each (top row, then bottom)."""
    out = []
    for row in (0, 0x10):
        letters = [fix_pixels(rom, t + row) for t in TIME_LETTERS]
        wide = [sum((letters[i][y] for i in range(4)), []) for y in range(8)]       # 32 pixels across
        wide = [[0] * 4 + r + [0] * 4 for r in wide]                                 # 40, shifted 4
        out.append([rom.add_fix_tile([r[c * 8:c * 8 + 8] for r in wide], why="HUD: TIME, half a tile right")
                    for c in range(5)])
    return out



def half_tiles(rom, word, down=LIVES_SHIFT):
    """Tile word `word`'s glyph `down` pixels lower (negative: higher), as two new fix tiles' words (its palette):
    down - its row's and the next's; up - the row above's and its own."""
    px = fix_pixels(rom, word & 0xFFF)
    return shifted(rom, px, down, "glyph 0x%X" % word, word & 0xF000)


def shifted(rom, px, down, what, palette, rows=2):
    """Pixel rows `px` (8 across) moved `down` pixels (negative: up) within `rows` fix rows: the new tiles' words,
    top row first (a row that ends up empty: the HUD's blank)."""
    if down < 0:
        tall = [[0] * 8 for _ in range(8 + down)] + px + [[0] * 8 for _ in range(rows * 8 - 8 - len(px) - down)]
    else:
        tall = [[0] * 8 for _ in range(down)] + px + [[0] * 8 for _ in range(rows * 8 - len(px) - down)]
    out = []
    for r in range(rows):
        tile = tall[r * 8:r * 8 + 8]
        out.append(BLANK if not any(any(t) for t in tile) else
                   palette | rom.add_fix_tile(tile, why="HUD: %s, shifted" % what))
    return out



def heart_column(rom, column, palette):
    """A heart's 16-pixel column HEARTS_UP pixels higher, as rows 5-6 from a row-6 address: two new tiles' words."""
    tall = [[0] * 8 for _ in range(8 - HEARTS_UP)] + column
    tall = (tall + [[0] * 8 for _ in range(16)])[:16]
    return [palette | rom.add_fix_tile(tall[r * 8:r * 8 + 8], why="HUD: heart, %d pixels higher" % HEARTS_UP)
            if any(any(t) for t in tall[r * 8:r * 8 + 8]) else BLANK for r in (0, 1)]


def apply(rom):
    x_px = [[0 if c == "." else int(c, 16) for c in row] for row in SMALL_X]
    small_x = TIMES & 0xF000 | rom.add_fix_tile(x_px, why="HUD: the x, smaller")
    for at in LIFE_DRAWN:
        assert rom.u16(at) == 0x41FA, hex(at)
        rom.write(at, bytes.fromhex("4E75"), why="HUD: no LIFE after the hearts")
    for at, old, new in HEARTS_AT:
        rom.write(at, bytes.fromhex("303C") + new.to_bytes(2, "big"), expect=bytes.fromhex("303C") +
                  old.to_bytes(2, "big"), why="HUD: player %d's hearts at the screen's edge" % (1 + (old > 0x7400)))
    for at, old, what in TIMER:
        new = DIGITS_AT if old == 0x2A1 else TIME_AT
        rom.write(at, bytes.fromhex("303C") + new.to_bytes(2, "big"), expect=bytes.fromhex("303C") +
                  old.to_bytes(2, "big"), why="HUD timer: %s, as a column" % what)
    for pal, entry, old, new in FACE_COLOURS:
        rom.write(FIX_PALETTES + pal * 32 + entry * 2, bytes.fromhex(new.replace(" ", "")),
                  expect=bytes.fromhex(old.replace(" ", "")), why="HUD: the lives face's suit, fix palette %d" % pal)
    lives = rom.place_code(r"""
| a player's lives (a4 = their block, d0 = where): the face (each player's colours), x, the count's last digit
    bra.w lives
    bra.w lives2
lives:
    move.w #0x%(face1)X,%%d2
    bra 3f
lives2:
    move.w #0x%(face2)X,%%d2
3:
%(colours)s    moveq #0,%%d1
    move.b 0(%%a4),%%d1
    divu #10,%%d1
    swap %%d1                           | d1 = the last digit
    add.w #0x%(digit)X,%%d1
    move.w #0x20,0x3C0004
    move.w %%d0,0x3C0000
    move.w %%d2,0x3C0002
    move.w #0x%(x)X,0x3C0002
    move.w %%d1,0x3C0002
    rts
""" % {"colours": "".join("    move.l #0x%s,0x%X\n" % (new.replace(" ", "")[:8], 0x400000 + pal * 32 + entry * 2)
                          for pal, entry, old, new in FACE_COLOURS) +
                  "".join("    move.w #0x%s,0x%X\n" % (new.split()[2], 0x400000 + pal * 32 + entry * 2 + 4)
                          for pal, entry, old, new in FACE_COLOURS),
       "face1": FACES[0], "face2": FACES[1], "x": small_x, "digit": DIGIT_0}, why="HUD: a player's lives")
    for n, (at, where) in enumerate(LIVES):
        rom.write(at, bytes.fromhex("303C") + where.to_bytes(2, "big") + bytes.fromhex("4EF9") +
                  (lives + 4 * n).to_bytes(4, "big"), why="HUD: player %d's lives by the flowers" % (n + 1))
    # the hearts, 6 pixels higher
    block_tiles = []
    for table in HEART_TABLES:
        words = [rom.u16(table + 2 * i) for i in range(4)]          # left top, left bottom, right top, right bottom
        for col in (0, 1):
            top, bottom = words[2 * col], words[2 * col + 1]
            if (top & 0xFFF) == 0x520:
                block_tiles += [BLANK, BLANK]
                continue
            column = fix_pixels(rom, top & 0xFFF) + fix_pixels(rom, bottom & 0xFFF)
            block_tiles += heart_column(rom, column, top & 0xF000)
    blocks = rom.place_code(r"""
| a 2x2 block of fix tiles (d0 = where, a0 = its tiles): a heart's - drawn %(up)d pixels higher (rows d0-1, d0) from
| its own tiles; any other as before
    cmpa.l #0x%(full)X,%%a0
    beq 1f
    cmpa.l #0x%(empty)X,%%a0
    beq 2f
    cmpa.l #0x%(none)X,%%a0
    beq 3f
    movem.l %%d0/%%a0,-(%%sp)
    move.w %%d0,0x3C0000
    jmp 0x%(back)X
1:  lea full(%%pc),%%a1
    bra 4f
2:  lea empty(%%pc),%%a1
    bra 4f
3:  lea none(%%pc),%%a1
4:  movem.l %%d0/%%a1,-(%%sp)
    move.w #1,0x3C0004
    subq.w #1,%%d0
    move.w %%d0,0x3C0000
    move.w (%%a1)+,0x3C0002
    move.w (%%a1)+,0x3C0002
    add.w #0x20,%%d0
    move.w %%d0,0x3C0000
    move.w (%%a1)+,0x3C0002
    move.w (%%a1)+,0x3C0002
    movem.l (%%sp)+,%%d0/%%a1
    rts
full:
    .word %(full_tiles)s
empty:
    .word %(empty_tiles)s
none:
    .word %(none_tiles)s
""" % {"up": HEARTS_UP, "full": HEART_TABLES[0], "empty": HEART_TABLES[1], "none": HEART_TABLES[2],
       "back": BLOCK + 10, "full_tiles": ",".join("0x%X" % w for w in block_tiles[0:4]),
       "empty_tiles": ",".join("0x%X" % w for w in block_tiles[4:8]),
       "none_tiles": ",".join("0x%X" % w for w in block_tiles[8:12])}, why="HUD: the hearts, 6 pixels higher")
    rom.write(BLOCK, bytes.fromhex("4EF9") + blocks.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("48E7808033C0003C0000"), why="HUD: 2x2 fix blocks - the hearts drawn higher")
    # the score line, 2 pixels higher
    glyphs = {n: half_tiles(rom, DIGIT_0 + n, -SCORE_UP) for n in range(10)}
    p_tiles, eq_tiles = half_tiles(rom, P_TILE, -SCORE_UP), half_tiles(rom, EQUALS_TILE, -SCORE_UP)
    score = rom.place_code(r"""
| a player's score, 2 pixels higher (a0 = its 3 BCD bytes, d0 = the digits' row-3 address, d1 = the label's, d2 =
| the label's digit 0-9): each glyph's top in row 2, the rest in row 3; leading zeros blank (not the last)
    bra.w score1
    bra.w score2
score1:
    lea 0x%(bcd1)X,%%a0
    move.w #0x%(digits1)X,%%d0
    move.w #0x%(label1)X,%%d1
    moveq #1,%%d2
    bra 5f
score2:
    lea 0x%(bcd2)X,%%a0
    move.w #0x%(digits2)X,%%d0
    move.w #0x%(label2)X,%%d1
    moveq #2,%%d2
5:  movem.l %%d0-%%d5/%%a0-%%a1,-(%%sp)
    move.w #0x20,0x3C0004
    lea tops(%%pc),%%a1                 | the label: digit, P, =
    moveq #1,%%d3                       | (d3: rows - 1 = up, 0 = the glyph's own)
6:  move.w %%d1,%%d4
    sub.w %%d3,%%d4
    move.w %%d4,0x3C0000
    move.w %%d2,%%d4
    add.w %%d4,%%d4
    move.w 0(%%a1,%%d4.w),0x3C0002
    move.w 20(%%a1),0x3C0002
    move.w 22(%%a1),0x3C0002
    lea bottoms(%%pc),%%a1
    dbf %%d3,6b
    moveq #1,%%d3                       | the 6 digits, twice (tops, then the rest)
    lea tops(%%pc),%%a1
7:  move.w %%d0,%%d4
    sub.w %%d3,%%d4
    move.w %%d4,0x3C0000
    movea.l 24(%%sp),%%a0               | (a0 again: saved after d0-d5)
    moveq #5,%%d5
    moveq #0,%%d2                       | (d2: a digit seen)
8:  moveq #0,%%d4
    move.b (%%a0),%%d4
    btst #0,%%d5
    beq 9f
    lsr.b #4,%%d4
    bra 10f
9:  andi.b #15,%%d4
    addq.l #1,%%a0
10: andi.w #15,%%d4
    or.w %%d4,%%d2
    bne 11f
    tst.w %%d5
    beq 11f
    move.w #0x%(blank)X,0x3C0002
    bra 12f
11: add.w %%d4,%%d4
    move.w 0(%%a1,%%d4.w),0x3C0002
12: dbf %%d5,8b
    lea bottoms(%%pc),%%a1
    dbf %%d3,7b
    movem.l (%%sp)+,%%d0-%%d5/%%a0-%%a1
    rts
tops:
    .word %(tops)s
bottoms:
    .word %(bottoms)s
""" % {"bcd1": SCORE[0][1], "digits1": SCORE[0][2], "label1": SCORE[0][3], "bcd2": SCORE[1][1],
       "digits2": SCORE[1][2], "label2": SCORE[1][3], "blank": BLANK,
       "tops": ",".join("0x%X" % glyphs[n][0] for n in range(10)) + ",0x%X,0x%X" % (p_tiles[0], eq_tiles[0]),
       "bottoms": ",".join("0x%X" % glyphs[n][1] for n in range(10)) + ",0x%X,0x%X" % (p_tiles[1], eq_tiles[1])},
        why="HUD: the score line, 2 pixels higher")
    for n, (at, *_rest) in enumerate(SCORE):
        rom.write(at, bytes.fromhex("4EF9") + (score + 4 * n).to_bytes(4, "big"),
                  why="HUD: player %d's score, 2 pixels higher" % (n + 1))
    for at in BAR:
        v = rom.u16(at)
        assert 0x7000 <= v < 0x7500 and (v & 31) in (27, 28), hex(at)
        rom.write(at, (v - 1).to_bytes(2, "big"), why="HUD: the item bar a row higher (0x%X)" % v)
    cells = [(a, HUD_BLANK) for a in OLD_CELLS + OLD_FLOWER_CELLS + OLD_LIVES_CELLS + BAR_OLD_ROW] + \
            [(a, BLANK) for a in OLD_HEART_CELLS]
    clear = rom.place_code("".join("    move.w #0x%X,0x3C0000\n    move.w #0x%X,0x3C0002\n" % c for c in cells) +
                           "    rts\n", why="HUD: the old layout's cells cleared")
    flowers = rom.place_code(r"""
| a player's flowers (a4 = their block, d0 = where): flower x and 3 digits, across
flowers:
    move.w %%d0,-(%%sp)
    moveq #0,%%d0
    move.b 0x10(%%a4),%%d0
    jsr 0x%(decimal)X
    move.w (%%sp)+,0x3C0000
    move.w #0x20,0x3C0004
    move.w #0x%(icon)X,0x3C0002
    move.w #0x%(times)X,0x3C0002
    moveq #2,%%d2
1:  move.w %%d1,%%d0
    lsr.w #8,%%d0
    andi.w #15,%%d0
    add.w #0x%(digit)X,%%d0
    move.w %%d0,0x3C0002
    lsl.w #4,%%d1
    dbf %%d2,1b
    rts
""" % {"decimal": TO_DECIMAL, "icon": FLOWER_ICON, "times": small_x, "digit": DIGIT_0},
                             why="HUD: a player's flowers under their hearts, x000")
    for at, where in FLOWERS:
        assert rom.u16(at) == 0x7000, hex(at)            # moveq #0,d0 (the routine's start)
        rom.write(at, bytes.fromhex("303C") + where.to_bytes(2, "big") + bytes.fromhex("4EF9") +
                  flowers.to_bytes(4, "big"), why="HUD: player %d's flowers under the hearts" % (1 + (where > 0x7400)))
    top, bottom = time_tiles(rom)
    word = rom.place_code("""
| TIME, half a tile right (d2 = the palette, as the printer's)
    move.w #1,0x3C0004
    move.w #0x%X,%%d0
""" % TIME_COLUMN + "".join("""    move.w %%d0,0x3C0000
    move.w #0x%X,%%d1
    or.w %%d2,%%d1
    move.w %%d1,0x3C0002
    move.w #0x%X,%%d1
    or.w %%d2,%%d1
    move.w %%d1,0x3C0002
    add.w #0x20,%%d0
""" % (t, b) for t, b in zip(top, bottom)) + "    rts\n", why="HUD: TIME, half a tile right")
    for at in TIME_PRINTS:
        rom.write(at, bytes.fromhex("4EB9") + word.to_bytes(4, "big"), expect=bytes.fromhex("4EB90004DDEE"),
                  why="HUD timer: TIME half a tile right (the digits centred under it)")
    for at in EQUALS:
        assert rom.u16(at) == 0x303C and rom.u16(at + 2) == 0x281 and rom.u16(at + 8) == 0x4EB9, hex(at)
        rom.write(at, bytes.fromhex("4EB9") + clear.to_bytes(4, "big") + bytes.fromhex("4E71") * 4,
                  why="HUD timer: no = (the old layout's cells cleared instead)")
