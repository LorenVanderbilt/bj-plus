NAME = "hud"
DESCRIPTION = "HUD: no LIFE; score, flowers (x000) and hearts at the screen's edges; the timer as a column; the lives (each player's colours) by the item bar, which is a row higher"

# LIFE: each player's hearts routine (player 1 0x4EA7C, player 2 0x4EAA2) draws it beside them as two 2x2 blocks of
# fix tiles (from 0x4EAC8) after the hearts: each routine now returns after the hearts (LIFE_DRAWN) - and the
# hearts take its place at the screen's edges (HEARTS_AT: player 1's drawn rightwards from column 1, player 2's leftwards from
# column 37; they were at 5 / 33).
# The timer (0x4E560: as normal, or blinking when time is short) drew TIME at fix offset 0x201 (column 16; the
# big-font printers put text 2 rows down: row 3), = at 0x281 and the time at 0x2A1: TIME=287 on one line. Now
# TIME in the HUD's small font on the score line (2 pixels up, rows 2-3, as 1P=) and the time under it at DIGITS_AT
# (columns 19-21, rows 4-5), no =.
# The = call's place clears the old layouts' cells nothing draws now (OLD_CELLS: a save state made before showed
# bits of them) - once, then CLEARED is set (cleared every frame, they cut into text boxes drawn over the HUD: the
# lottery gnomes').
OLD_CELLS = ([0x7000 + c * 32 + r for c in range(16, 24) for r in (3, 4)] +                  # TIME= (TIME and
             # its digits draw only over blanks and their own tiles: the old ones there are cleared first)
             [0x7000 + c * 32 + 3 for c in (12, 13, 14, 25, 26, 27)] +                          # lives
             [0x7000 + c * 32 + 4 for c in (6, 10, 11, 12, 13, 14, 16, 17, 23, 25, 26, 27, 28, 29, 33)] +   # hearts, TIME=
             [0x7000 + c * 32 + 5 for c in (1, 2, 3, 4, 11, 12, 13, 14, 25, 26, 27, 28, 35, 36, 37, 38)] +   # LIFE, hearts
             [0x7000 + c * 32 + 7 for c in list(range(1, 11)) + list(range(29, 39))] +           # (tried layouts)
             [0x7000 + c * 32 + r for c in (2, 3, 4, 33, 34, 35) for r in (25, 26)] +
             [0x7000 + c * 32 + 29 for c in range(40)])                                          # the bar's old row
CLEARED = 0x10E9FD           # a byte (spare RAM): 0xA5 once cleared
BLANK_TILE = 0x0520
# The flowers: each player's count (block +0x10) was drawn at the bottom, by the item bar (player 1's 0x4E99C at row
# 27, columns 2-6: flower = and the number, leading zeros blank; player 2's 0x4E9D0, columns 33-37). Now under the
# score, above the hearts (row 4), flower x and always 3 digits (000): each routine jumps to `flowers`. For 2 pixels' room above and below, the score line is drawn 2
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
# The lives (the hero's face, x and the count): player 1's 0x4EA04 at row 3, columns 12-14; player 2's 0x4EA3A at
# columns 25-27 - now on the flowers' line, a space on (player 1: columns 7-9; player 2: 30-32, a space before its
# flowers), drawn by `lives`. As before only the count's last digit shows.
LIVES = [(0x4EA04, 0x7000 + 7 * 32 + 4), (0x4EA3A, 0x7000 + 30 * 32 + 4)]   # (routine, where the face goes)
# The item bar (rows 28-29) a row higher, off the screen's bottom edge (TVs crop it): its frame (inline strings at
# 0x9FE2 calls), the markers over it (row 27) and each player's boxes (their base fix address) - each address one
# row up (BAR).
BAR = [0x4E5EE, 0x4E5FC, 0x4E60C, 0x4E61A,                    # the frame
       0x4E632, 0x4E640, 0x4E656, 0x4E664, 0x4E67A, 0x4E68C, 0x4E6A6, 0x4E6B8,   # the markers over it
       0x4E6DE, 0x4E70A]                                      # the boxes (addi.w #base,d0)
# The face was purple (fix palette 3's entries 10-12, its suit) for both players: now each player's suit. Palette 3
# is shared (the catfish sprite uses it), so both faces are in palette 7 - the only one 0-15 no fix cell or sprite
# used in any of 86 save states (2026-10-12): its suit entries made player 2's greens (palette 0x11), its outline
# palette 3's, and three more (2, 9, 15: FACE_MERGE) player 1's blues (the hero's palette 0x10) - player
# 1's face a copy of the tile with its suit there (FACE_REMAP). FIX_PALETTES: the fix palettes' table (loaded with a
# stage); `lives` also puts the colours in the palette RAM as it draws (a save state's are the old ones).
FIX_PALETTES = 0x1000
FACE_COLOURS = [(7, 3, "EFB0 8F91 9F70", "4FD0 6F90 8C60"), (7, 10, "BC38 0A27 1805", "B0F9 A0D4 11A1"),
                (7, 1, "8000 8777", "8000 B08F"), (7, 9, "EFFA", "F04F"), (7, 15, "FFFF", "201E")]   # (palette, first entry, old, new)
FACE_TILE, FACE_PALETTE = 0x400, 7
BLACKOUT = 0x10E600          # (screen-blackout's flag: the screen held black while it's built)
FACE_MERGE = {9: 3, 15: 6}           # (both faces: the face uses every entry but 2, so its one yellow and one white pixel
                                     # take the nearest colours it has - freeing 9 and 15 for player 1's suit)
FACE_REMAP = {10: 2, 11: 9, 12: 15}  # (player 1's face: its suit's entries)
LIVES_SHIFT = 4
LIFE_DRAWN = [0x4EA84, 0x4EAAA]   # lea <LIFE's tiles>(pc),a0 - after the hearts (player 1, 2): rts instead
BLANK = 0x5520
HEARTS_AT = [(0x4EA7C, 0x70A4, 0x7026), (0x4EAA2, 0x7424, 0x74A6)]   # (move.w #fix address,d0, old, new: rows 6-7)
# The hearts' 2x2 blocks (0x4E8CC, from the tables HEART_TABLES: full, empty, none) drawn 6 pixels higher: rows 5-6
# from a row-6 address (the draw `blocks` in its place for those tables; the hearts are 13 pixels tall: nothing in
# a third row).
BLOCK = 0x4E8CC              # movem.l d0/a0,-(sp) ; move.w d0,0x3C0000 ; ... (a 2x2 block of fix tiles, a0 = them)
HEART_TABLES = [0x4EBAC, 0x4EBB4, 0x4EBBC]
# The hearts' second row (6) and the timer's digits (rows 5-6) reach below the old HUD (rows 3-5), where text over
# the level goes (the lottery gnomes' lines from row 6; round clear): each of their cells is only drawn if it's blank
# or already theirs (HEART_PALETTE / TIMER_PALETTES) - an overlay's text in it stays, and when it clears they're back.
HEART_PALETTE = 4
TIMER_PALETTES = (0xA, 0x6)          # (normal, blinking)
TIMER_DIGIT_CALLS = [0x4DCF6, 0x4DD28, 0x4DD4C, 0x4DD84, 0x4DDB8, 0x4DDDE]   # jsr 0x5F0EA (a 2-row character)
BIG_CHARACTER = 0x5F0EA      # d0 = fix offset (+0x7002), d1 = tile word
TIMER_HIDDEN = 0x10E9FE      # a byte (spare RAM): the HUD hidden - worked out first each frame (HUD_ENTRY), and as
                             # the stage's end starts (MODE_SET: after a boss the HUD isn't run then): from a hero
                             # frozen at the goal (state GOAL_STATE), ROUND CLEAR (ROUND_CLEARS - after a boss, the
                             # lottery follows on the same stage) or the stage's end (game MODE 2) until play starts
                             # again (MODE 1 after another: the next stage) - LATCH. Meanwhile every part of the HUD clears its cells instead of drawing
                             # (the hearts and the timer only their own tiles)
MODE, STAGE = 0x103004, 0x103005
GOAL_STATE = 45              # (the hero's state byte, object +0x68: frozen - grabbing the goal)
HEROES = [0x104068, 0x1040E8]
HUD_ENTRY = 0x4E4B8          # tst.b 0x309B(a6) ; bne <rts> (the HUD each frame)
TIMER_COUNT, TIMER_DRAW = 0x106904, 0x4E560   # (the timer's count; its drawing, d0 = the count)
LATCH, LAST_MODE = 0x10EA01, 0x10EA02   # (bytes; spare RAM: LATCH set while hidden, the mode last frame)
MODE_SET = 0x29EB4           # move.b #2,MODE(a6): the stage's end (after the goal or a boss)
ROUND_CLEARS = [0x54CD0, 0x54FD8]   # ROUND CLEAR's routines (the goal's; a boss's): move.w #<first letter>,d0 ;
                                    # move.w #<its tile>,d1 (its place as `round-clear-centred` left it)
BAR_PRINTS = {0x9FE2: [0x4E5E8, 0x4E5F6, 0x4E606, 0x4E614],   # the item bar's frame and markers: inline prints
              0x9FE6: [0x4E62C, 0x4E63A, 0x4E650, 0x4E65E, 0x4E674, 0x4E686, 0x4E6A0, 0x4E6B2]}
BAR_ROWS = (27, 28)          # (its boxes: 2x2 blocks there)
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
TIME_AT = 18 * 32 + 1
# ... and TIME half a tile right, so the 3 digits sit under its middle (the fix layer moves in 8-pixel columns): the
# small font's letters (TIME_LETTERS, as 1P= and the scores: tile 0x500 + the character) redrawn 4 pixels right and
# SCORE_UP higher as 5 new fix tiles a row (columns 18-22, rows 2-3), drawn by `time_word` in place of the big-font
# printer's call
# (TIME_PRINTS) in the HUD font's palette (TIME_PALETTE) - steady when the time is short (the digits blink).
TIME_LETTERS = [0x500 + ord(c) for c in "TIME"]
TIME_PALETTE = P_TILE & 0xF000
TIME_PRINTS = [0x4E596, 0x4E5CC]      # jsr 0x4DDEE (the big-font printer: TIME)
TIME_COLUMN = 0x7000 + 18 * 32 + 2
DIGITS_AT = 19 * 32 + 2




def fix_pixels(rom, tile):
    at = tile * 32
    return [[rom.fix_orig[at + rom.FIX_COLUMN_BYTE[x] + y] >> (0 if x % 2 == 0 else 4) & 15 for x in range(8)]
            for y in range(8)]


def time_tiles(rom):
    """TIME 4 pixels right and SCORE_UP higher, over 2 rows: 5 new fix tiles each (top row, then bottom)."""
    letters = [fix_pixels(rom, t) for t in TIME_LETTERS]
    wide = [[0] * 4 + sum((letters[i][y] for i in range(4)), []) + [0] * 4 for y in range(8)]   # 40 across
    tall = [[0] * 40 for _ in range(8 - SCORE_UP)] + wide + [[0] * 40 for _ in range(SCORE_UP)]
    return [[rom.add_fix_tile([r[c * 8:c * 8 + 8] for r in tall[row:row + 8]], why="HUD: TIME on the score line",
                              share=True) for c in range(5)] for row in (0, 8)]



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
                   palette | rom.add_fix_tile(tile, why="HUD: %s, shifted" % what, share=True))
    return out



def heart_column(rom, column, palette):
    """A heart's 16-pixel column HEARTS_UP pixels higher, as rows 5-6 from a row-6 address: two new tiles' words."""
    tall = [[0] * 8 for _ in range(8 - HEARTS_UP)] + column
    tall = (tall + [[0] * 8 for _ in range(16)])[:16]
    return [palette | rom.add_fix_tile(tall[r * 8:r * 8 + 8], why="HUD: heart, %d pixels higher" % HEARTS_UP, share=True)
            if any(any(t) for t in tall[r * 8:r * 8 + 8]) else BLANK for r in (0, 1)]


def apply(rom):
    x_px = [[0 if c == "." else int(c, 16) for c in row] for row in SMALL_X]
    small_x = TIMES & 0xF000 | rom.add_fix_tile(x_px, why="HUD: the x, smaller", share=True)
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
    face = fix_pixels(rom, FACE_TILE)
    face = [[FACE_MERGE.get(v, v) for v in r] for r in face]
    face1 = FACE_PALETTE << 12 | rom.add_fix_tile([[FACE_REMAP.get(v, v) for v in r] for r in face],
                                                   why="HUD: player 1's lives face (its suit in other entries)", share=True)
    face2 = FACE_PALETTE << 12 | rom.add_fix_tile(face, why="HUD: player 2's lives face", share=True)
    faces = [face1, face2]
    lives = rom.place_code(r"""
| a player's lives (a4 = their block, d0 = where): the face (each player's colours), x, the count's last digit
    bra.w lives
    bra.w lives2
lives:
    move.w #0x%(face1)X,%%d2
    bra 3f
lives2:
    move.w #0x%(face2)X,%%d2
3:  tst.b 0x%(hidden)X                  | (the HUD hidden: its 3 cells cleared)
    beq 4f
    move.w #0x20,0x3C0004
    move.w %%d0,0x3C0000
    move.w #0x%(blank)X,0x3C0002
    move.w #0x%(blank)X,0x3C0002
    move.w #0x%(blank)X,0x3C0002
    rts
4:  tst.b 0x%(black)X                   | (screen-blackout's screen black: the colours left - the stage's own fix
    bne 5f                              | palettes, put in at its reveal, have them)
%(colours)s5:  moveq #0,%%d1
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
""" % {"colours": "".join("    move.w #0x%s,0x%X\n" % (w, 0x400000 + pal * 32 + (entry + i) * 2)
                          for pal, entry, old, new in FACE_COLOURS for i, w in enumerate(new.split())),
       "face1": faces[0], "face2": faces[1], "x": small_x, "digit": DIGIT_0, "hidden": TIMER_HIDDEN, "blank": BLANK,
       "black": BLACKOUT}, why="HUD: a player's lives")
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
    tst.b 0x%(hidden)X                  | (any other: the item bar's boxes, hidden with the HUD)
    beq 7f
    move.w %%d0,%%d1
    andi.w #31,%%d1
    cmpi.w #%(bar0)d,%%d1
    beq 8f
    cmpi.w #%(bar1)d,%%d1
    bne 7f
8:  move.w #1,0x3C0004
    move.w %%d0,0x3C0000
    move.w #0x%(blank)X,0x3C0002
    move.w #0x%(blank)X,0x3C0002
    add.w #0x20,%%d0
    move.w %%d0,0x3C0000
    move.w #0x%(blank)X,0x3C0002
    move.w #0x%(blank)X,0x3C0002
    sub.w #0x20,%%d0
    rts
7:  movem.l %%d0/%%a0,-(%%sp)
    move.w %%d0,0x3C0000
    jmp 0x%(back)X
1:  lea full(%%pc),%%a1
    bra 4f
2:  lea empty(%%pc),%%a1
    bra 4f
3:  lea none(%%pc),%%a1
4:  movem.l %%d0-%%d2/%%a1,-(%%sp)
    subq.w #1,%%d0
    bsr cell
    addq.w #1,%%d0
    bsr cell
    add.w #0x1F,%%d0
    bsr cell
    addq.w #1,%%d0
    bsr cell
    movem.l (%%sp)+,%%d0-%%d2/%%a1
    rts
| fix cell d0 <- (a1)+, if it's blank or a heart's (else something over the HUD is there: left alone, and the HUD
| hides a while); the HUD hidden - a heart's tile there cleared
cell:
    move.w (%%a1)+,%%d1
    move.w %%d0,0x3C0000
    move.w 0x3C0002,%%d2
    tst.b 0x%(hidden)X
    bne 9f
    bsr free
    bne 10f
    move.w %%d0,0x3C0000
    move.w %%d1,0x3C0002
5:  rts
10: rts
9:  bsr free                            | (hidden: blank, or a heart's - cleared)
    bne 5b
    move.w %%d0,0x3C0000
    move.w #0x%(blank)X,0x3C0002
    rts
| Z set if fix word d2 is blank or in palette %(heart_pal)d
free:
    move.w %%d2,-(%%sp)
    andi.w #0xFFF,%%d2
    cmpi.w #0x020,%%d2
    beq 6f
    cmpi.w #0x520,%%d2
    beq 6f
    tst.w %%d2
    beq 6f
    move.w (%%sp),%%d2
    lsr.w #8,%%d2
    lsr.w #4,%%d2
    cmpi.w #%(heart_pal)d,%%d2
6:  movem.w (%%sp)+,%%d2                | (movem: the flags stay)
    rts
full:
    .word %(full_tiles)s
empty:
    .word %(empty_tiles)s
none:
    .word %(none_tiles)s
""" % {"up": HEARTS_UP, "heart_pal": HEART_PALETTE, "hidden": TIMER_HIDDEN, "blank": BLANK,
       "bar0": BAR_ROWS[0], "bar1": BAR_ROWS[1], "full": HEART_TABLES[0], "empty": HEART_TABLES[1], "none": HEART_TABLES[2],
       "back": BLOCK + 10, "full_tiles": ",".join("0x%X" % w for w in block_tiles[0:4]),
       "empty_tiles": ",".join("0x%X" % w for w in block_tiles[4:8]),
       "none_tiles": ",".join("0x%X" % w for w in block_tiles[8:12])}, why="HUD: the hearts, 6 pixels higher")
    rom.write(BLOCK, bytes.fromhex("4EF9") + blocks.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("48E7808033C0003C0000"), why="HUD: 2x2 fix blocks - the hearts drawn higher")
    # the timer's digits: only into a blank cell or one of its own
    checked = rom.place_code(r"""
| a timer digit (as 0x%(big)X: d0 = offset, d1 = tile word), unless one of its two cells holds something other than
| blank or a timer digit (ROUND CLEAR and its bonus lines are drawn there)
    movem.l %%d0/%%d2,-(%%sp)
    add.w #0x7002,%%d0
    bsr 2f
    bne 1f
    addq.w #1,%%d0
    bsr 2f
    bne 1f
    tst.b 0x%(hidden)X
    bne 1f
    movem.l (%%sp)+,%%d0/%%d2
    jmp 0x%(big)X
1:                                      | (blocked, or hidden: this digit's own tiles cleared)
    movem.l (%%sp),%%d0/%%d2
    add.w #0x7002,%%d0
    bsr 5f
    addq.w #1,%%d0
    bsr 5f
    movem.l (%%sp)+,%%d0/%%d2
    rts
5:  move.w %%d0,0x3C0000                | (cell d0: a big digit there - blank)
    move.w 0x3C0002,%%d2
    andi.w #0xFEF,%%d2
    subi.w #0x6E4,%%d2
    cmpi.w #10,%%d2
    bcc 6f
    move.w %%d0,0x3C0000
    move.w #0x0520,0x3C0002
6:  rts
2:  move.w %%d0,0x3C0000                | Z set if cell d0 is blank or a big digit (0x6E4-0x6ED, 0x6F4-0x6FD)
    move.w 0x3C0002,%%d2
    andi.w #0xFFF,%%d2
    cmpi.w #0x020,%%d2
    beq 3f
    cmpi.w #0x520,%%d2
    beq 3f
    tst.w %%d2
    beq 3f
    andi.w #0xFEF,%%d2
    subi.w #0x6E4,%%d2
    cmpi.w #10,%%d2
    bcc 4f
3:  ori.b #4,%%ccr
    rts
4:  andi.b #0xFB,%%ccr
    rts
""" % {"big": BIG_CHARACTER, "hidden": TIMER_HIDDEN},
                             why="HUD timer: a digit only where nothing else is")
    for at in TIMER_DIGIT_CALLS:
        rom.write(at, bytes.fromhex("4EB9") + checked.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + BIG_CHARACTER.to_bytes(4, "big"),
                  why="HUD timer: its digits leave text over the HUD alone")
    # the item bar's frame and markers: hidden with the HUD (their inline prints' cells cleared)
    prints = rom.place_code(r"""
    bra.w print_down
    bra.w print_across
print_down:
    tst.b 0x%(hidden)X
    bne 1f
    jmp 0x9FE2
1:  move.w #1,-(%%sp)
    bra 3f
print_across:
    tst.b 0x%(hidden)X
    bne 2f
    jmp 0x9FE6
2:  move.w #0x20,-(%%sp)
3:  movem.l %%d0-%%d1/%%a0,-(%%sp)      | (the inline string after the call: its address word, then FC + a base,
    move.w 12(%%sp),0x3C0004            | characters, FF - each character's cell cleared; back after it)
    movea.l 14(%%sp),%%a0
    move.w (%%a0)+,0x3C0000
4:  move.b (%%a0)+,%%d1
    cmpi.b #0xFF,%%d1
    beq 6f
    cmpi.b #0xFC,%%d1
    bne 5f
    addq.l #1,%%a0
    bra 4b
5:  move.w #0x%(blank)X,0x3C0002
    bra 4b
6:  move.l %%a0,%%d0
    btst #0,%%d0
    beq 7f
    addq.l #1,%%a0
7:  move.l %%a0,14(%%sp)
    movem.l (%%sp)+,%%d0-%%d1/%%a0
    addq.l #2,%%sp
    rts
""" % {"hidden": TIMER_HIDDEN, "blank": 0x0520}, why="HUD: the item bar's prints, hidden with the HUD")
    for n, (target, sites) in enumerate(sorted(BAR_PRINTS.items())):
        for at in sites:
            rom.write(at, bytes.fromhex("4EB9") + (prints + 4 * n).to_bytes(4, "big"),
                      expect=bytes.fromhex("4EB9") + target.to_bytes(4, "big"), why="HUD: the item bar hides with it")
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
5:  tst.b 0x%(hidden)X                  | (the HUD hidden: the label's and digits' cells cleared, both rows)
    beq 15f
    movem.l %%d0-%%d3,-(%%sp)
    move.w #0x20,0x3C0004
    moveq #1,%%d3
13: move.w %%d1,%%d2
    sub.w %%d3,%%d2
    move.w %%d2,0x3C0000
    move.w #0x%(blank)X,0x3C0002
    move.w #0x%(blank)X,0x3C0002
    move.w #0x%(blank)X,0x3C0002
    move.w %%d0,%%d2
    sub.w %%d3,%%d2
    move.w %%d2,0x3C0000
    moveq #5,%%d2
14: move.w #0x%(blank)X,0x3C0002
    dbf %%d2,14b
    dbf %%d3,13b
    movem.l (%%sp)+,%%d0-%%d3
    rts
15: movem.l %%d0-%%d5/%%a0-%%a1,-(%%sp)
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
       "digits2": SCORE[1][2], "label2": SCORE[1][3], "blank": BLANK, "hidden": TIMER_HIDDEN,
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
    flowers = rom.place_code(r"""
| a player's flowers (a4 = their block, d0 = where): flower x and 3 digits, across
flowers:
    tst.b 0x%(hidden)X                  | (the HUD hidden: its 5 cells cleared)
    beq 1f
    move.w #0x20,0x3C0004
    move.w %%d0,0x3C0000
    moveq #4,%%d2
2:  move.w #0x%(blank)X,0x3C0002
    dbf %%d2,2b
    rts
1:  move.w %%d0,-(%%sp)
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
""" % {"decimal": TO_DECIMAL, "icon": FLOWER_ICON, "times": small_x, "digit": DIGIT_0, "hidden": TIMER_HIDDEN,
       "blank": BLANK},
                             why="HUD: a player's flowers under their hearts, x000")
    for at, where in FLOWERS:
        assert rom.u16(at) == 0x7000, hex(at)            # moveq #0,d0 (the routine's start)
        rom.write(at, bytes.fromhex("303C") + where.to_bytes(2, "big") + bytes.fromhex("4EF9") +
                  flowers.to_bytes(4, "big"), why="HUD: player %d's flowers under the hearts" % (1 + (where > 0x7400)))
    top, bottom = time_tiles(rom)
    word = rom.place_code(r"""
| TIME, half a tile right, in the HUD font's palette (not the printer's, d2) - a column only where its cells are
| blank or the timer's (ROUND CLEAR is drawn over it, in the same rows)
    movem.l %%d0-%%d4/%%a0,-(%%sp)
    move.w #1,0x3C0004
    move.w #0x%(at)X,%%d0
    lea tiles(%%pc),%%a0
    moveq #4,%%d4
    tst.b 0x%(hidden)X                  | (the HUD hidden: TIME's own tiles cleared instead)
    beq 1f
8:  move.w %%d0,%%d3
    bsr own
    bne 9f
    move.w %%d0,0x3C0000
    move.w #0x0520,0x3C0002
    move.w #0x0520,0x3C0002
9:  add.w #0x20,%%d0
    dbf %%d4,8b
    movem.l (%%sp)+,%%d0-%%d4/%%a0
    rts
1:  move.w %%d0,%%d3
    bsr own
    bne 3f
    addq.w #1,%%d3
    bsr own
    bne 3f
    move.w %%d0,0x3C0000
    move.w (%%a0),%%d1
    ori.w #0x%(palette)X,%%d1
    move.w %%d1,0x3C0002
    move.w 2(%%a0),%%d1
    ori.w #0x%(palette)X,%%d1
    move.w %%d1,0x3C0002
3:  addq.l #4,%%a0
    add.w #0x20,%%d0
    dbf %%d4,1b
    movem.l (%%sp)+,%%d0-%%d4/%%a0
    rts
| Z set if cell d3 is blank or one of TIME's tiles
own:
    movem.l %%d1/%%d3/%%a1,-(%%sp)
    move.w %%d3,0x3C0000
    move.w 0x3C0002,%%d1
    andi.w #0xFFF,%%d1
    cmpi.w #0x020,%%d1
    beq 6f
    cmpi.w #0x520,%%d1
    beq 6f
    tst.w %%d1
    beq 6f
    lea tiles(%%pc),%%a1
    moveq #9,%%d3
5:  cmp.w (%%a1)+,%%d1
    dbeq %%d3,5b
    bra 7f
6:  ori.b #4,%%ccr
7:  movem.l (%%sp)+,%%d1/%%d3/%%a1         | (movem: the flags stay)
    rts
tiles:
    .word %(tiles)s
""" % {"at": TIME_COLUMN, "hidden": TIMER_HIDDEN, "mode": MODE, "stage": STAGE, "palette": TIME_PALETTE,
       "goal": GOAL_STATE, "hero1": HEROES[0], "hero2": HEROES[1],
       "tiles": ",".join("0x%X,0x%X" % (t, b) for t, b in zip(top, bottom))}, why="HUD: TIME, half a tile right")
    for at in TIME_PRINTS:
        rom.write(at, bytes.fromhex("4EB9") + word.to_bytes(4, "big"), expect=bytes.fromhex("4EB90004DDEE"),
                  why="HUD timer: TIME half a tile right (the digits centred under it)")
    # Hidden or not is worked out at the HUD's start each frame (HUD_ENTRY), before any part draws; when it changes,
    # every part is drawn (or cleared) at once - each normally takes its turn (one group every 4 frames, the timer
    # every 16), so they went one by one, the time last.
    first_letter = {bytes(rom.data[at:at + 8]) for at in ROUND_CLEARS}
    assert len(first_letter) == 1, "ROUND CLEAR's routines don't start alike"
    first_letter = first_letter.pop()
    assert first_letter[0:2] == b"\x30\x3C" and first_letter[4:6] == b"\x32\x3C", first_letter.hex()
    frame = rom.place_code(r"""
    bra.w main
    bra.w stage_end
    bra.w round_clear
main:
    tst.b 0x10309B                      | (as the original: no HUD - the routine left)
    beq 1f
    addq.l #4,%%sp
    rts
1:  movem.l %%d0-%%d7/%%a0-%%a5,-(%%sp)
    bra 2f
| ROUND CLEAR starting (ROUND_CLEARS: its first two moves done here) - the HUD hidden at once, until the next
| stage (after a boss the lottery follows on the same stage, in play)
round_clear:
    st 0x%(latch)X
    pea 3f(%%pc)
    movem.l %%d0-%%d7/%%a0-%%a5,-(%%sp)
    bra 2f
3:  move.w #0x%(rc_d0)X,%%d0
    move.w #0x%(rc_d1)X,%%d1
    rts
| the stage's end starting (MODE_SET: the mode set to 2 first) - the HUD hidden at once
stage_end:
    move.b #2,0x%(mode)X
    movem.l %%d0-%%d7/%%a0-%%a5,-(%%sp)
2:  move.b 0x%(mode)X,%%d1              | the HUD hidden this frame? (LATCH: once hidden, until play starts again)
    cmpi.b #1,%%d1
    bne 10f
    cmpi.b #1,0x%(last)X                | (play starting - from the title card: no longer hidden)
    beq 10f
    clr.b 0x%(latch)X
10: move.b %%d1,0x%(last)X
    cmpi.b #2,%%d1                      | (the stage's end)
    beq 13f
    cmpi.b #%(goal)d,0x%(hero1)X        | (a hero at the goal)
    beq 13f
    cmpi.b #%(goal)d,0x%(hero2)X
    bne 11f
13: st 0x%(latch)X
11: move.b 0x%(latch)X,%%d3
14: move.b 0x%(hidden)X,%%d2
    move.b %%d3,0x%(hidden)X
    cmp.b %%d2,%%d3
    beq 9f
    btst #0,0x106800
    beq 20f
    tst.b 0x107000+0x23
    bne 20f
    lea 0x107000,%%a4
    jsr 0x4E954
    jsr 0x4E99C
    jsr 0x4EA04
    jsr 0x4EA7C
    jsr 0x4E624
    jsr 0x4E66C
    jsr 0x4E5E8
    jsr 0x4E6C4
20:
    btst #1,0x106800
    beq 21f
    tst.b 0x107400+0x23
    bne 21f
    lea 0x107400,%%a4
    jsr 0x4E978
    jsr 0x4E9D0
    jsr 0x4EA3A
    jsr 0x4EAA2
    jsr 0x4E648
    jsr 0x4E698
    jsr 0x4E606
    jsr 0x4E6EE
21:
    move.l 0x%(timer)X,%%d0             | (the timer, as its own turn: from its division)
    jsr 0x%(timer_draw)X
9:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a5
    rts
""" % {"hidden": TIMER_HIDDEN, "mode": MODE, "stage": STAGE, "goal": GOAL_STATE,
       "hero1": HEROES[0], "hero2": HEROES[1], "timer": TIMER_COUNT, "timer_draw": TIMER_DRAW,
       "latch": LATCH, "last": LAST_MODE, "rc_d0": int.from_bytes(first_letter[2:4], "big"),
       "rc_d1": int.from_bytes(first_letter[6:8], "big")},
        why="HUD: hidden or not, worked out first each frame - all of it at once when that changes")
    rom.write(HUD_ENTRY, bytes.fromhex("4EB9") + frame.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("4A2E309B66000682"), why="HUD: hidden or not, first each frame")
    rom.write(MODE_SET, bytes.fromhex("4EB9") + (frame + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("1D7C00023004"), why="HUD: hidden as the stage's end starts (after a boss too)")
    for at in ROUND_CLEARS:
        rom.write(at, bytes.fromhex("4EB9") + (frame + 8).to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=first_letter, why="HUD: hidden as ROUND CLEAR starts")
    clear = rom.place_code("""
    cmpi.b #0xA5,0x%X
    beq 1f
    move.b #0xA5,0x%X
""" % (CLEARED, CLEARED) + "".join("    move.w #0x%X,0x3C0000\n    move.w #0x%X,0x3C0002\n" % (a, BLANK_TILE)
                                     for a in OLD_CELLS) + "1:  rts\n", why="HUD: the old layouts' cells cleared, once")
    for at in EQUALS:
        assert rom.u16(at) == 0x303C and rom.u16(at + 2) == 0x281 and rom.u16(at + 8) == 0x4EB9, hex(at)
        rom.write(at, bytes.fromhex("4EB9") + clear.to_bytes(4, "big") + bytes.fromhex("4E71") * 4,
                  why="HUD timer: no = (the old layouts' cells cleared, once)")
