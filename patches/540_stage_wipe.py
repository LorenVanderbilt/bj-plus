NAME = "stage-wipe"
DESCRIPTION = "After a stage's title card, the level is revealed by a wipe from the screen's centre (a spiral or an iris)"

import math

# A stage starts (after its title card, or after losing a life) by building the level over a few frames (from
# SETUPS: jsr 0x5AED2), clearing the fix layer (CLEARS: jsr 0x9FBE) and setting MODE 1 (STARTS). Now SETUPS first
# cover the screen (the fix layer, above everything) with BLACK_PIXEL tiles, CLEARS fill it with them again, and
# STARTS start the wipe: after START_DELAY frames, the cells are cleared in ORDER (the centre first) over DURATION
# frames. It runs at the HUD's start each frame (HUD_ENTRY, before the hud patch's routine), and the HUD isn't drawn
# from the cover to the wipe's end - then it's drawn whole (TIMER_HIDDEN set with the cover: the hud patch draws
# every part when that changes).
#   SHAPE "iris": a ring growing from the centre; "spiral": a wiper blade pinned at the centre sweeps round TURNS
#   times, growing from nothing to the corners - each cell cleared the first time the blade reaches it.
SHAPE = "iris"
TURNS = 2
CLOCKWISE = False
START_DELAY = 0               # frames of black after the title card, before the wipe
DURATION = 30                 # frames from the centre to the corners (60 = a second)
TITLE_HOLD = 105              # frames the title card stays up (was 189; a button press ends it)
MUSIC_AT = DURATION           # frames into play before the stage's music starts (the title card's jingle plays on
                              # till then; after losing a life the music starts as before)

SETUPS = [0x114E0, 0x115B0]   # jsr 0x5AED2: the level's set-up starts
SETUP = 0x5AED2
CLEARS = [0x1154C, 0x11612]   # jsr 0x9FBE: the fix layer cleared (0x4FE cells from 0x7002 to BLANK)
FIX_CLEAR = 0x9FBE
STARTS = [0x11552, 0x11618]   # move.b #1,0x3004(a6): play starts
HOLD = 0x13A98                # move.w #189,d7 (the title card's hold, in frames)
MUSIC = 0x11532               # jsr 0x151CE: stop the sound, start the stage's music (after the title card)
STAGE_MUSIC = 0x151CE
CARD_ENDS = [0x13AFA, 0x13B1C]   # jsr 0x9FBE: the title card's text cleared (held out / a button pressed)
# The top corners of a player not in the game are redrawn (blank: no-join-prompts) every 32 frames - through the
# cover: CORNERS (andi.w #31,d1 ; bne.w <past it>) skip that while the wipe is on.
CORNERS = [(0x11B58, 0x11CBA), (0x11CD6, 0x11E28)]   # (where, past the corner's drawing)
MODE = 0x103004
HUD_ENTRY = 0x4E4B8           # jsr <the hud patch's frame routine> ; nop
NO_HUD = 0x10309B
TIMER_HIDDEN = 0x10E9FE       # (the hud patch's)
BLACK_PALETTE, BLACK_PIXEL = 7, 1   # (fix palette 7, entry 1: black - the hud patch keeps it so)
BLANK = 0x0520
COLUMNS, ROWS = range(40), range(2, 30)   # the visible fix cells
WIPE_ON, WIPE_T, WIPE_I = 0x10EA60, 0x10EA62, 0x10EA64   # (spare RAM: byte 1 = covered / 2 = running; frame; cells)
MUSIC_DUE = 0x10EA66          # a byte: the stage's music still to start
BLINKS = [0x107009, 0x107409] # each hero's blink (can't be hurt) timer: none as a stage starts, only after a death


def order():
    """The visible cells' fix addresses, in the order they're cleared; and how many are cleared by each frame."""
    cx, cy = (len(COLUMNS) - 1) / 2, (ROWS[0] + ROWS[-1]) / 2
    far = math.hypot(cx, cy - ROWS[0])
    def key(c, r):
        d = math.hypot(c - cx, r - cy) / far
        if SHAPE == "iris":
            return d
        turn = (math.atan2(r - cy, c - cx) / (2 * math.pi)) % 1
        turn = turn if CLOCKWISE else 1 - turn
        reach = d * TURNS                       # (in turns: when the blade first reaches this far)
        return reach + (turn - reach) % 1       # ... then the next time it points this way
    cells = sorted(((c, r) for c in COLUMNS for r in ROWS), key=lambda cr: key(*cr))
    keys = [key(c, r) for c, r in cells]
    # how many are cleared by each frame: the edge moves at a steady pace (a cell count per frame would open the
    # iris with a jump - its area grows with the square of its size)
    counts = [sum(1 for k in keys if k <= keys[-1] * (f + 1) / DURATION) for f in range(DURATION)]
    return [0x7000 + c * 32 + r for c, r in cells], counts


def apply(rom):
    assert rom.u16(HUD_ENTRY) == 0x4EB9, "expected the hud patch's call"
    hud = rom.u32(HUD_ENTRY + 2)
    black = BLACK_PALETTE << 12 | rom.add_fix_tile([[BLACK_PIXEL] * 8 for _ in range(8)], why="stage wipe: black",
                                                   share=True)
    cells, counts = order()
    code = rom.place_code(r"""
    bra.w start
    bra.w frame
    bra.w cover
    bra.w music
    bra.w card_end
| the level's set-up: the screen covered first (unless the title card's end did)
    tst.b 0x%(on)X
    bne 1f
    move.b #1,0x%(on)X
    st 0x%(hidden)X
    bsr fill
1:  jmp 0x%(setup)X
| the title card's end: the screen covered but for its text, which stays up while the level is built
card_end:
    move.b #1,0x%(on)X
    st 0x%(hidden)X
    movem.l %%d0-%%d1,-(%%sp)
    move.w #0x7002,%%d1
1:  move.w %%d1,0x3C0000
    move.w 0x3C0002,%%d0
    andi.w #0xFFF,%%d0
    cmpi.w #0x020,%%d0
    beq 2f
    cmpi.w #0x520,%%d0
    beq 2f
    tst.w %%d0
    bne 3f
2:  move.w %%d1,0x3C0000
    move.w #0x%(black)X,0x3C0002
3:  addq.w #1,%%d1
    cmpi.w #0x7500,%%d1
    bcs 1b
    movem.l (%%sp)+,%%d0-%%d1
    rts
| ... and the fix layer's clear before play: black, not blank
cover:
fill:
    move.l %%d1,-(%%sp)
    move.w #0x7002,0x3C0000
    move.w #1,0x3C0004
    move.w #0x4FE-1,%%d1
1:  move.w #0x%(black)X,0x3C0002
    dbf %%d1,1b
    move.l (%%sp)+,%%d1
    rts
| each frame, before the HUD: covered or wiping (the HUD skipped), else the HUD as usual
frame:
    tst.b 0x%(on)X
    bne 1f
    jmp 0x%(hud)X
1:  tst.b 0x%(no_hud)X
    beq 2f
    jmp 0x%(hud)X
2:  cmpi.b #2,0x%(on)X
    bne 10f                             | (covered: waiting for play)
    movem.l %%d0-%%d3/%%a0,-(%%sp)
    move.w #1,0x3C0004
    addq.w #1,0x%(t)X
    tst.b 0x%(due)X                     | the stage's music, when it's due
    beq 3f
    move.w 0x%(t)X,%%d0
    cmpi.w #%(music_at)d,%%d0
    blt 3f
    clr.b 0x%(due)X
    movem.l %%d4-%%d7/%%a1-%%a6,-(%%sp)
    jsr 0x%(stage_music)X
    movem.l (%%sp)+,%%d4-%%d7/%%a1-%%a6
3:  move.w 0x%(t)X,%%d0
    bmi 9f                              | (the delay)
    add.w %%d0,%%d0                      | cells to have cleared by now
    lea counts(%%pc),%%a0
    move.w (%%a0,%%d0.w),%%d0
    cmp.w #%(count)d,%%d0
    bcs 5f
    clr.b 0x%(on)X                      | (the last frame: the HUD from the next)
5:  move.w 0x%(i)X,%%d1
    lea cells(%%pc),%%a0
    add.w %%d1,%%a0
    add.w %%d1,%%a0
6:  cmp.w %%d0,%%d1
    bcc 7f
    move.w (%%a0)+,0x3C0000
    move.w #0x%(blank)X,0x3C0002
    addq.w #1,%%d1
    bra 6b
7:  move.w %%d1,0x%(i)X
9:  movem.l (%%sp)+,%%d0-%%d3/%%a0
10: addq.l #4,%%sp                      | (the HUD's routine left, as its own no-HUD case does)
    rts
| after the title card: the stage's music later (the jingle plays on)
music:
    st 0x%(due)X
    rts
| play starts: the wipe
start:
    move.b #1,0x%(mode)X
    move.b #2,0x%(on)X
    move.w #-%(delay)d-1,0x%(t)X
    clr.w 0x%(i)X
    tst.b 0x%(due)X                     | (after the title card: the heroes don't blink - after a death they do)
    beq 1f
    clr.b 0x%(blink1)X
    clr.b 0x%(blink2)X
1:  rts
counts:
    .word %(counts)s
cells:
    .word %(cells)s
""" % {"on": WIPE_ON, "t": WIPE_T, "i": WIPE_I, "hud": hud, "no_hud": NO_HUD, "hidden": TIMER_HIDDEN,
       "black": black, "count": len(cells), "duration": DURATION, "blank": BLANK, "mode": MODE, "delay": START_DELAY,
       "setup": SETUP, "due": MUSIC_DUE, "music_at": min(MUSIC_AT, START_DELAY + DURATION - 1) - START_DELAY,
       "stage_music": STAGE_MUSIC, "blink1": BLINKS[0], "blink2": BLINKS[1],
       "counts": ",".join(str(n) for n in counts), "cells": ",".join("0x%X" % a for a in cells)}, why="stage wipe: %s over %d frames" % (SHAPE, DURATION))
    rom.write(HUD_ENTRY + 2, (code + 4).to_bytes(4, "big"), expect=hud.to_bytes(4, "big"),
              why="the HUD each frame: the stage wipe first")
    rom.write(MUSIC, bytes.fromhex("4EB9") + (code + 12).to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + STAGE_MUSIC.to_bytes(4, "big"),
              why="after the title card: the stage's music once the wipe's under way (the jingle plays on)")
    for at in SETUPS:
        rom.write(at, bytes.fromhex("4EB9") + (code + 20).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + SETUP.to_bytes(4, "big"), why="stage set-up: the screen covered first")
    for at in CARD_ENDS:
        rom.write(at, bytes.fromhex("4EB9") + (code + 16).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + FIX_CLEAR.to_bytes(4, "big"),
                  why="title card's end: covered but for its text (no black gap)")
    rom.write(HOLD, bytes.fromhex("3E3C") + TITLE_HOLD.to_bytes(2, "big"), expect=bytes.fromhex("3E3C00BD"),
              why="title card: held %d frames (was 189), then the stage wipe" % TITLE_HOLD)
    for at, past in CORNERS:
        skip = rom.place_code("""
    andi.w #31,%%d1
    bne 1f
    tst.b 0x%X
    bne 1f
    rts
1:  addq.l #4,%%sp
    jmp 0x%X
""" % (WIPE_ON, past), why="stage wipe: a player's empty corner not drawn through it")
        rom.write(at, bytes.fromhex("4EB9") + skip.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex("0241001F6600") + (past - at - 6).to_bytes(2, "big"),
                  why="empty corner: not while the stage wipe is on")
    for at in CLEARS:
        rom.write(at, bytes.fromhex("4EB9") + (code + 8).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + FIX_CLEAR.to_bytes(4, "big"), why="before play: the fix layer black")
    for at in STARTS:
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("1D7C00013004"),
                  why="title card done: the stage wipe")
