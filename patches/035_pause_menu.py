NAME = "pause-menu"
DESCRIPTION = "The pause has a menu: RESUME / RESTART LEVEL / QUIT TO TITLE (Up / Down, A picks; Start resumes) on a bubble; Select hides it"

# The gameplay mode (mode 1, 0x11ABC: one frame per call from the mode loop 0x10D20) pauses at 0x11ACC: 0x1541A
# prints PAUSE (fix-layer address 0x722C) and freezes, then it waits a frame at a time (0x11AD0-0x11B10) until
# Start (see pause-start) and resumes with 0x15446, carrying on at 0x11B16. That wait is replaced by a menu under
# PAUSE, in PAUSE's own font and palette (read back from its P):
#   RESUME        - as before (Start does it too)
#   RESTART LEVEL - mode 0 (the stage's start: 0x113BC) for the stage being played, then back to the mode loop -
#                   its restart points forgotten first (RESTART_POINTS: each player's checkpoint, the way back out of
#                   a cave), as the game's own stage select does (0x12DF2), so it's the stage's beginning
#   QUIT TO TITLE - mode 8 (the game's end: the mode loop returns to the attract sequence), the title first - as
#                   the title menu's BACK TO TITLE
# PAUSE moves a column right (PAUSE_AT, both where 0x1541A prints it and where 0x15446 blanks it: PAUSE_ADDRS), centred
# over the menu. Behind it all, a box: Blue's answer bubble (BUBBLE_TILES: its corner, side, top and fill - the rest
# flipped; no tail) COLS x ROWS tiles at X, Y, in sprite slots from SLOT (above anything the game draws in play: its
# drawing loop never reaches them) - drawn with palette PALETTE (empty in play - the title's), its colours
# (BUBBLE_COLOURS: the bubble's black and golds) written in while the menu's up and the palette put back after.
# Select (player 1's, 0x10FDAC bit 1 - unused in play since pause-start) hides PAUSE, the menu and the box for a clean
# pause screen, and shows them again; Up / Down / A do nothing while hidden.
PAUSE_SITE = 0x11ACC        # bsr.w 0x1541A ; jsr 0xE856 ...
PAUSE_ENTER, PAUSE_EXIT = 0x1541A, 0x15446
PAUSE_ADDRS = [0x15436, 0x15462]   # (the inline printer's fix address word in each)
RESUME_AT = 0x11B16
START_CHECK_SITE = 0x11B06  # pause-start's `jsr <its Start press check>` (Z clear on a new press)
WAIT_FRAME = 0xE856
MODE = 0x103004
RESTART_POINTS = [0x107100, 0x107500, 0x103024]   # (longs: 0 = none - the stage's beginning)
ATTRACT_TOGGLE = 0x1033CA   # bit 0 clear: the attract cycle with the title runs next
PAUSE_WAS = 0x722C
PAUSE_AT = 0x7000 + 18 * 32 + 12   # column 18, row 12 (was 17): centred over the menu
MENU_ADDR = 0x7000 + 13 * 32 + 15   # column 13, row 15
ITEMS = ["RESUME", "RESTART LEVEL", "QUIT TO TITLE"]
WIDTH = 16
CURSOR = 0x10E816           # spare RAM: the cursor (byte), the buttons last frame (byte), the font base (word),
PREV = 0x10E817             # hidden (byte), Select last frame (byte), the palette put aside (16 words)
BASE = 0x10E818
HIDDEN = 0x10E81A
SELECT_PREV = 0x10E81B
PALETTE_SAVE = 0x10E830
P1_NOW = 0x10FD96
BUTTONS = 0x10FDAC          # (bit 1: player 1's Select)
BUBBLE_TILES = (0x58D9, 0x58D7, 0x58DA, 0x58D6)   # (frame 0x345C's: corner, left side, top, fill)
SLOT, COLS, ROWS = 300, 10, 6
X, Y = 86, 64               # (screen pixels; the tiles' outline is 6 px in from the left, 8 down from the top)
PALETTE = 0x7E
BUBBLE_COLOURS = {3: 0x7FD4, 4: 0x4FB1, 15: 0x0000}   # (the bubble's: light gold, gold, black)


def bubble_words():
    """The box's SCB1 words, column by column: (tile, attributes) for each row."""
    corner, side, top, fill = BUBBLE_TILES
    out = []
    for c in range(COLS):
        edge = c in (0, COLS - 1)
        h = 1 if c == COLS - 1 else 0
        for r in range(ROWS):
            v = 2 if r == ROWS - 1 else 0
            tile = (corner if r in (0, ROWS - 1) else side) if edge else (top if r in (0, ROWS - 1) else fill)
            out += [tile, PALETTE << 8 | v | h]
    return out


def apply(rom):
    if rom.data[START_CHECK_SITE:START_CHECK_SITE + 2] != bytes.fromhex("4EB9"):
        raise SystemExit("pause-menu: needs pause-start (its Start check at 0x%X)" % START_CHECK_SITE)
    start_check = int.from_bytes(rom.data[START_CHECK_SITE + 2:START_CHECK_SITE + 6], "big")
    for at in PAUSE_ADDRS:
        rom.write(at, PAUSE_AT.to_bytes(2, "big"), expect=PAUSE_WAS.to_bytes(2, "big"),
                  why="pause: PAUSE centred over the menu")
    lines = "".join("    .ascii \"%s\"\n    .byte 0\n" % ("  " + t).ljust(WIDTH) for t in ITEMS)
    colours = [BUBBLE_COLOURS.get(i, 0) for i in range(16)]
    code = rom.place_code(r"""
    jsr 0x%(enter)X
    movem.l %%d0-%%d7/%%a0-%%a1,-(%%sp)
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #0x%(ptile)X,0x3C0000
    move.w 0x3C0002,%%d0
    move.w (%%sp)+,%%sr
    sub.w #0x50,%%d0                   | ('P': the font's base)
    move.w %%d0,0x%(base)X
    clr.b 0x%(cursor)X
    clr.b 0x%(hidden)X
    move.b 0x%(p1)X,0x%(prev)X
    move.b 0x%(buttons)X,%%d0
    andi.b #2,%%d0
    move.b %%d0,0x%(selprev)X
    lea 0x%(palram)X,%%a0               | the palette put aside, the bubble's colours in
    lea 0x%(palsave)X,%%a1
    moveq #15,%%d0
0:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,0b
    lea 0x%(palram)X,%%a0
    lea colours(%%pc),%%a1
    moveq #15,%%d0
0:  move.w (%%a1)+,(%%a0)+
    dbf %%d0,0b
    bsr bubble
    bsr draw
1:  jsr 0x%(wait)X
    jsr 0x%(start)X                  | Start: resume
    bne resume
    move.b 0x%(buttons)X,%%d0           | Select: hide / show it all
    andi.b #2,%%d0
    move.b 0x%(selprev)X,%%d1
    move.b %%d0,0x%(selprev)X
    not.b %%d1
    and.b %%d1,%%d0
    beq 5f
    not.b 0x%(hidden)X
    beq 6f
    bsr erase
    lea blanks(%%pc),%%a0
    bsr pause
    bsr unbubble
    bra 5f
6:  lea pause_text(%%pc),%%a0
    bsr pause
    bsr bubble
    bsr draw
5:  move.b 0x%(p1)X,%%d0
    move.b 0x%(prev)X,%%d1
    move.b %%d0,0x%(prev)X
    tst.b 0x%(hidden)X
    bne 1b
    not.b %%d1
    and.b %%d1,%%d0                   | new presses
    btst #0,%%d0                      | up
    beq 2f
    subq.b #1,0x%(cursor)X
    bpl 3f
    move.b #2,0x%(cursor)X
    bra 3f
2:  btst #1,%%d0                      | down
    beq 4f
    addq.b #1,0x%(cursor)X
    cmp.b #3,0x%(cursor)X
    bcs 3f
    clr.b 0x%(cursor)X
3:  bsr draw
    bra 1b
4:  btst #4,%%d0                      | A: pick
    beq 1b
    move.b 0x%(cursor)X,%%d0
    beq resume
    bsr close
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a1
    jsr 0x%(exit)X
    cmp.b #1,0x%(cursor)X
    bne 5f
%(forget)s    move.b #0,0x%(mode)X               | RESTART LEVEL
    rts
5:  bclr #0,0x%(toggle)X              | QUIT TO TITLE
    move.b #8,0x%(mode)X
    rts
resume:
    bsr close
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a1
    jsr 0x%(exit)X
    jmp 0x%(resume_at)X

| the menu, the box and the palette gone
close:
    bsr erase
    bsr unbubble
    lea 0x%(palsave)X,%%a0
    lea 0x%(palram)X,%%a1
    moveq #15,%%d0
0:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,0b
    rts

| the three lines, the cursor (>) on the picked one
draw:
    movem.l %%d0-%%d3/%%a0,-(%%sp)
    lea items(%%pc),%%a0
    move.w #0x%(addr)X,%%d1
    moveq #0,%%d3
10: move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #32,0x3C0004
    move.w %%d1,0x3C0000
    moveq #0,%%d2
11: moveq #0,%%d0
    move.b (%%a0)+,%%d0
    beq 12f
    tst.w %%d2                         | (the first character: the cursor or a space)
    bne 13f
    cmp.b 0x%(cursor)X,%%d3
    bne 13f
    moveq #0x11,%%d0                   | (the game's cursor)
13: addq.w #1,%%d2
    add.w 0x%(base)X,%%d0
    move.w %%d0,0x3C0002
    bra 11b
12: move.w #1,0x3C0004
    move.w (%%sp)+,%%sr
    addq.w #2,%%d1                     | two rows down
    addq.w #1,%%d3
    cmp.w #3,%%d3
    bcs 10b
    movem.l (%%sp)+,%%d0-%%d3/%%a0
    rts

| the three lines blanked
erase:
    movem.l %%d0-%%d3,-(%%sp)
    move.w #0x%(addr)X,%%d1
    moveq #2,%%d3
20: move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #32,0x3C0004
    move.w %%d1,0x3C0000
    moveq #%(w1)d,%%d2
21: move.w 0x%(base)X,%%d0
    add.w #0x20,%%d0
    move.w %%d0,0x3C0002
    dbf %%d2,21b
    move.w #1,0x3C0004
    move.w (%%sp)+,%%sr
    addq.w #2,%%d1
    dbf %%d3,20b
    movem.l (%%sp)+,%%d0-%%d3
    rts

| PAUSE's place: the text at a0 (PAUSE or blanks)
pause:
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #32,0x3C0004
    move.w #0x%(pause_at)X,0x3C0000
30: moveq #0,%%d0
    move.b (%%a0)+,%%d0
    beq 31f
    add.w 0x%(base)X,%%d0
    move.w %%d0,0x3C0002
    bra 30b
31: move.w #1,0x3C0004
    move.w (%%sp)+,%%sr
    rts

| the box: COLS chained sprites from SLOT
bubble:
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
    lea tiles(%%pc),%%a0
    move.w #%(slot)d*64,%%d1           | SCB1: each column's tiles
    moveq #%(cols)d-1,%%d3
40: move.w %%d1,0x3C0000
    moveq #%(rows)d*2-1,%%d2
41: move.w (%%a0)+,0x3C0002
    dbf %%d2,41b
    add.w #64,%%d1
    dbf %%d3,40b
    move.w #0x8000+%(slot)d,0x3C0000   | SCB2: full size
    moveq #%(cols)d-1,%%d3
42: move.w #0x0FFF,0x3C0002
    dbf %%d3,42b
    move.w #0x8200+%(slot)d,0x3C0000   | SCB3: y and height, the rest chained
    move.w #%(scb3)d,0x3C0002
    moveq #%(cols)d-2,%%d3
43: move.w #0x40,0x3C0002
    dbf %%d3,43b
    move.w #0x8400+%(slot)d,0x3C0000   | SCB4: x
    move.w #%(scb4)d,0x3C0002
    move.w (%%sp)+,%%sr
    rts

| the box hidden (height 0)
unbubble:
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
    move.w #0x8200+%(slot)d,0x3C0000
    moveq #%(cols)d-1,%%d3
50: move.w #0,0x3C0002
    dbf %%d3,50b
    move.w (%%sp)+,%%sr
    rts

items:
%(lines)s
pause_text:
    .ascii "PAUSE"
    .byte 0
blanks:
    .ascii "     "
    .byte 0
    .even
colours:
    .word %(colours)s
tiles:
    .word %(tiles)s
""" % {"enter": PAUSE_ENTER, "exit": PAUSE_EXIT, "ptile": PAUSE_AT, "base": BASE, "cursor": CURSOR, "prev": PREV,
       "hidden": HIDDEN, "selprev": SELECT_PREV, "buttons": BUTTONS, "palsave": PALETTE_SAVE,
       "palram": 0x400000 + PALETTE * 32, "pause_at": PAUSE_AT,
       "p1": P1_NOW, "wait": WAIT_FRAME, "start": start_check, "mode": MODE, "toggle": ATTRACT_TOGGLE,
       "resume_at": RESUME_AT, "forget": "".join("    clr.l 0x%X\n" % a for a in RESTART_POINTS),
       "addr": MENU_ADDR, "w1": WIDTH - 1, "lines": lines,
       "slot": SLOT, "cols": COLS, "rows": ROWS, "scb3": (496 - Y) << 7 | ROWS, "scb4": X << 7,
       "colours": ",".join("0x%04X" % c for c in colours),
       "tiles": ",".join("0x%04X" % w for w in bubble_words())},
        why="pause menu: RESUME / RESTART LEVEL / QUIT TO TITLE on a bubble; Select hides it")
    rom.write(PAUSE_SITE, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("61003" + "94C4EB9"),
              why="pause: the menu instead of waiting for Start")
