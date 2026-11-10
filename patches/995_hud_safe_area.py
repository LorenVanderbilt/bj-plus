NAME = "hud-safe-area"
DESCRIPTION = "HUD inside a CRT's safe area: the old layout's cells cleared once, for saves made before it moved"

# On a real TV the picture's edges are cropped, and the HUD sat at them (the user, on the BackBit). Its score,
# flowers, lives and hearts now sit two columns in, on the same rows, and the item bars a column in; `hud`
# (patches/500_hud.py) has the positions. The boundary is the CRT-safe area measured from Riding Hero
# (../neogeo-notes/findings.md: columns 3-36, rows 4-28; columns 2-37, rows 3-29 at the most). The score lines stay
# in rows 2-3, level with TIME, above even the outer limit: the user's call on their CRT, where they fit. The two
# players' item bars together reach columns 2-37, since they don't fit side by side inside 3-36.
#
# A save state made before the move still has the old layout's tiles in the fix layer, and the HUD redraws only its
# new cells. So on the first frame of play after a load (the HUD's call in the gameplay loop, HUD_CALL), every cell
# the old layout used and the new one doesn't (OLD - NEW) is blanked, once (DONE). The attract's RAM clear resets
# DONE, but in a fresh game those cells are blank already. It waits while stage-wipe's black cover is up or its iris
# runs (WIPE_ON): a fresh stage's first frames of play come then, and blanking those cells punched holes in the
# cover (the user, on the Retroid, 2026-11-09).
#
# The lottery's text box now overlaps the flowers and lives too, but the HUD is hidden from ROUND CLEAR until the
# next stage (hud's TIMER_HIDDEN), so in play nothing shows under it. Only a save made mid-lottery before that hiding
# existed shows the HUD there.
HUD_CALL = 0x11828              # jsr <lottery-box-hearts', which calls the HUD>: each frame of play
DONE = 0x10D5F5                 # spare RAM (a byte): set once the old cells are cleared
WIPE_ON = 0x10EA60              # stage-wipe's byte: the screen covered (1) or the iris running (2)
BLANK = 0x0520                  # hud's blank cell


def cells(cols, rows):
    return {(c, r) for c in cols for r in rows}


def mirror(cs):
    return {(39 - c, r) for c, r in cs}


# player 1's cells (column, row); player 2's are mirrored, column 39 - c
OLD = (cells(range(1, 10), (2, 3)) | cells(range(1, 6), (4,)) | cells(range(7, 10), (4,)) |    # score, flowers, lives
       cells(range(1, 11), (5, 6)) | cells((1,), (26, 27, 28)))                               # hearts, the bar's end
NEW = (cells(range(3, 12), (2, 3)) | cells(range(3, 8), (4,)) | cells(range(9, 12), (4,)) |
       cells(range(3, 13), (5, 6)) | cells(range(2, 20), (26, 27, 28)))


def apply(rom):
    old, new = OLD | mirror(OLD), NEW | mirror(NEW)
    clear = sorted(0x7000 + c * 32 + r for c, r in old - new)
    assert rom.u16(HUD_CALL) == 0x4EB9
    next_call = rom.u32(HUD_CALL + 2)
    code = rom.place_code("""
| each frame of play: the old layout's cells blanked once, then the HUD as before
    tst.b 0x%(done)X
    bne 2f
    tst.b 0x%(wipe)X                    | not under the stage's black cover or its iris
    bne 2f
    st 0x%(done)X
    move.l %%a0,-(%%sp)
    move.l %%d0,-(%%sp)
    lea cells(%%pc),%%a0
    move.w #%(count)d-1,%%d0
1:  move.w (%%a0)+,0x3C0000
    nop                                 | (the LSPC's wait after a data write, before a new address)
    move.w #0x%(blank)X,0x3C0002
    dbf %%d0,1b
    move.l (%%sp)+,%%d0
    movea.l (%%sp)+,%%a0
2:  jmp 0x%(next)X
cells:
    .word %(cells)s
""" % {"done": DONE, "wipe": WIPE_ON, "count": len(clear), "blank": BLANK, "next": next_call,
       "cells": ",".join("0x%X" % a for a in clear)}, why="HUD safe area: the old layout's cells blanked once")
    rom.write(HUD_CALL + 2, code.to_bytes(4, "big"), expect=next_call.to_bytes(4, "big"),
              why="each frame of play: the old HUD's cells blanked first, once")

