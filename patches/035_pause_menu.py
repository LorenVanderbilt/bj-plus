NAME = "pause-menu"
DESCRIPTION = "The pause has a menu: RESUME / RESTART LEVEL / QUIT TO TITLE (Up / Down, A picks; Start resumes)"

# The gameplay mode (mode 1, 0x11ABC: one frame per call from the mode loop 0x10D20) pauses at 0x11ACC: 0x1541A
# prints PAUSE (fix-layer address 0x722C) and freezes, then it waits a frame at a time (0x11AD0-0x11B10) until
# Start (see pause-start) and resumes with 0x15446, carrying on at 0x11B16. That wait is replaced by a menu under
# PAUSE, in PAUSE's own font and palette (read back from its P):
#   RESUME        - as before (Start does it too)
#   RESTART LEVEL - mode 0 (the stage's start: 0x113BC) for the stage being played, then back to the mode loop
#   QUIT TO TITLE - mode 8 (the game's end: the mode loop returns to the attract sequence), the title first - as
#                   the title menu's BACK TO TITLE
# Meant for testing; may be switched off for release.
PAUSE_SITE = 0x11ACC        # bsr.w 0x1541A ; jsr 0xE856 ...
PAUSE_ENTER, PAUSE_EXIT = 0x1541A, 0x15446
RESUME_AT = 0x11B16
START_CHECK_SITE = 0x11B06  # pause-start's `jsr <its Start press check>` (Z clear on a new press)
WAIT_FRAME = 0xE856
MODE = 0x103004
CHECKPOINT = 0x103008       # the restart point reached (10 bytes; 0 = the stage's beginning)
ATTRACT_TOGGLE = 0x1033CA   # bit 0 clear: the attract cycle with the title runs next
P_TILE = 0x722C             # PAUSE's P on the fix layer
MENU_ADDR = 0x7000 + 13 * 32 + 15   # column 13, row 15
ITEMS = ["RESUME", "RESTART LEVEL", "QUIT TO TITLE"]
WIDTH = 16
CURSOR = 0x10E816           # spare RAM: the cursor (byte), the buttons last frame (byte), the font base (word)
PREV = 0x10E817
BASE = 0x10E818
P1_NOW = 0x10FD96


def apply(rom):
    if rom.data[START_CHECK_SITE:START_CHECK_SITE + 2] != bytes.fromhex("4EB9"):
        raise SystemExit("pause-menu: needs pause-start (its Start check at 0x%X)" % START_CHECK_SITE)
    start_check = int.from_bytes(rom.data[START_CHECK_SITE + 2:START_CHECK_SITE + 6], "big")
    lines = "".join("    .ascii \"%s\"\n    .byte 0\n" % ("  " + t).ljust(WIDTH) for t in ITEMS)
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
    move.b 0x%(p1)X,0x%(prev)X
    bsr draw
1:  jsr 0x%(wait)X
    jsr 0x%(start)X                  | Start: resume
    bne resume
    move.b 0x%(p1)X,%%d0
    move.b 0x%(prev)X,%%d1
    move.b %%d0,0x%(prev)X
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
    bsr erase
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a1
    jsr 0x%(exit)X
    cmp.b #1,0x%(cursor)X
    bne 5f
    clr.l 0x%(checkpoint)X              | RESTART LEVEL: the checkpoint forgotten, then the stage's start
    clr.l 0x%(checkpoint)X+4
    clr.w 0x%(checkpoint)X+8
    move.b #0,0x%(mode)X
    rts
5:  bclr #0,0x%(toggle)X              | QUIT TO TITLE
    move.b #8,0x%(mode)X
    rts
resume:
    bsr erase
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a1
    jsr 0x%(exit)X
    jmp 0x%(resume_at)X

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
items:
%(lines)s    .even
""" % {"enter": PAUSE_ENTER, "exit": PAUSE_EXIT, "ptile": P_TILE, "base": BASE, "cursor": CURSOR, "prev": PREV,
       "p1": P1_NOW, "wait": WAIT_FRAME, "start": start_check, "mode": MODE, "toggle": ATTRACT_TOGGLE,
       "resume_at": RESUME_AT, "checkpoint": CHECKPOINT, "addr": MENU_ADDR, "w1": WIDTH - 1, "lines": lines},
        why="pause menu: RESUME / RESTART LEVEL / QUIT TO TITLE")
    rom.write(PAUSE_SITE, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("61003" + "94C4EB9"),
              why="pause: the menu instead of waiting for Start")
