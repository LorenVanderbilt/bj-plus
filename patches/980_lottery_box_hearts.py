NAME = "lottery-box-hearts"
DESCRIPTION = "Lottery after a boss: the gnomes' text box covers the hearts behind it (they were drawn over its corner)"

# hud draws the hearts in fix rows 6-7 from column 3 rightwards, and the lottery's text box (BOX, the text engine's
# object, frame 0x3254 at a fixed place) is drawn over that corner. The box is made of sprites and the hearts are on
# the fix layer, which the hardware always draws in front, so the hearts showed over the box's border and first line.
#
# After each frame's HUD (its call in the gameplay loop, HUD_CALL), while the box is up, every heart cell the box
# overlaps (COLUMNS x ROWS) is swapped for a copy with the covered part cleared. The box then covers them, with the
# tops of the hearts still showing above its edge. They're swapped back once the box has gone (SWAPPED). The box's
# edge on the fix layer is BOX_LEFT pixels across and BOX_TOP down, including its black outline.
#
# This runs every frame of play, and busy frames have no time to spare, so it only looks at the box's own object
# slot (BOX_SLOT). Each copy is a tile of its own, including a clear one for cells the box covers whole, so it can
# be told apart from the heart it was made from and swapped back.
HUD_CALL = 0x11828              # jsr 0x4E4B8: the HUD, each frame of play
HUD = 0x4E4B8
BOX = (0x21562, 0x3254, 0xA800, 0x4800)   # the box object's code, frame, y and x, the same in every lottery
BOX_SLOT = 0x104600             # its object slot, the same in every lottery
SWAPPED = 0x10EA68              # spare RAM byte: set while the hearts are swapped for their copies
BOX_LEFT, BOX_TOP = 22, 43      # fix-layer pixels: the 7th of column 2, the 4th of row 5
COLUMNS, ROWS = range(3, 13), (6, 7)   # player 1's hearts: up to 5, two columns each


def heart_words(rom, hud):
    """hud's heart tiles by row, {row: [fix words]}, worked out the way hud makes them (shared tiles give the same
    words)."""
    words = {row: set() for row in ROWS}
    for table in hud.HEART_TABLES:
        tiles = [rom.u16(table + 2 * i) for i in range(4)]          # left top, left bottom, right top, right bottom
        for col in (0, 1):
            top, bottom = tiles[2 * col], tiles[2 * col + 1]
            if (top & 0xFFF) == 0x520:
                continue
            column = rom.fix_tile(top & 0xFFF) + rom.fix_tile(bottom & 0xFFF)
            for row, word in zip(ROWS, hud.heart_column(rom, column, top & 0xF000)):
                if word != hud.BLANK:
                    words[row].add(word)
    return {row: sorted(w) for row, w in words.items()}


def covered(col, row, x, y):
    return col * 8 + x >= BOX_LEFT and row * 8 + y >= BOX_TOP


def apply(rom):
    hud = rom.other_patch("hud")
    words = heart_words(rom, hud)
    copies = {}                                   # (word, mask) -> the copy's word
    cells = ""
    for row in ROWS:
        for col in COLUMNS:
            mask = tuple((x, y) for y in range(8) for x in range(8) if covered(col, row, x, y))
            if not mask:
                continue
            pairs = []
            for word in words[row]:
                if (word, mask) not in copies:
                    px = rom.fix_tile(word & 0xFFF, built=True)    # hud's tiles, so from the built ROM
                    px = [[0 if (x, y) in mask else px[y][x] for x in range(8)] for y in range(8)]
                    copies[word, mask] = word & 0xF000 | rom.add_fix_tile(
                        px, why="lottery: a heart under the text box (row %d, %s)" % (
                            row, "whole" if len(mask) == 64 else "its edge"))
                pairs.append((word, copies[word, mask]))
            cells += "    .word 0x%X,%d\n" % (0x7000 + col * 32 + row, len(pairs) - 1)
            cells += "".join("    .word 0x%X,0x%X\n" % p for p in pairs)
    assert rom.data[HUD_CALL:HUD_CALL + 6] == bytes.fromhex("4EB9") + HUD.to_bytes(4, "big")
    code = rom.place_code(r"""
| the HUD, then swap the hearts under the lottery's text box (box up) or back (box gone)
    jsr 0x%(hud)X
    movem.l %%d0-%%d4/%%a0-%%a1,-(%%sp)
    moveq #0,%%d3                       | d3: is the box up?
    lea 0x%(slot)X,%%a0
    cmpi.l #0x%(code)X,4(%%a0)
    bne 2f
    tst.b 0x28(%%a0)
    beq 2f
    cmpi.w #0x%(frame)X,8(%%a0)
    bne 2f
    cmpi.l #0x%(y)04X%(x)04X,(%%a0)
    bne 2f
    moveq #1,%%d3
    st 0x%(swapped)X
    bra 3f
2:  tst.b 0x%(swapped)X                 | no box: put the hearts back, once
    beq 10f
    clr.b 0x%(swapped)X
3:  lea cells(%%pc),%%a1
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
4:  move.w (%%a1)+,%%d0                 | a cell: its address (0 = done), then its pair count - 1
    beq 9f
    move.w (%%a1)+,%%d1
    move.w %%d0,0x3C0000
    move.w 0x3C0002,%%d2                | the tile there now
5:  move.w (%%a1)+,%%d4                 | the heart
    tst.w %%d3
    beq 6f
    cmp.w %%d4,%%d2                     | box up: heart to copy
    bne 7f
    move.w %%d0,0x3C0000
    move.w (%%a1),0x3C0002
    bra 7f
6:  cmp.w (%%a1),%%d2                   | box gone: copy to heart
    bne 7f
    move.w %%d0,0x3C0000
    move.w %%d4,0x3C0002
7:  addq.l #2,%%a1
    dbf %%d1,5b
    bra 4b
9:  move.w (%%sp)+,%%sr
10: movem.l (%%sp)+,%%d0-%%d4/%%a0-%%a1
    rts
cells:
%(cells)s    .word 0
""" % {"hud": HUD, "slot": BOX_SLOT, "code": BOX[0], "frame": BOX[1], "y": BOX[2], "x": BOX[3], "swapped": SWAPPED,
       "cells": cells}, why="lottery: the text box covers the hearts behind it")
    rom.write(HUD_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=rom.data[HUD_CALL:HUD_CALL + 6],
              why="each frame of play: the HUD, then the hearts under the lottery's text box")
