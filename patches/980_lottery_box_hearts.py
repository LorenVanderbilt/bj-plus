NAME = "lottery-box-hearts"
DESCRIPTION = "Lottery after a boss: the gnomes' text box covers the hearts behind it (they were drawn over its corner)"

# hud's hearts are in rows 5-6 (from column 1 rightwards), and the lottery's text box (the text engine's object, BOX:
# frame 0x3254 at a fixed place) is drawn over that corner. The box is sprites and the hearts the fix layer, which the
# hardware always draws in front - so the hearts showed over the box's border and its first line. Now, after each
# frame's HUD (its call in the gameplay loop, HUD_CALL), while the box is up every heart cell the box overlaps
# (COLUMNS x ROWS) is swapped for a copy with the box's part cleared - so the box covers them, a heart's top still
# showing above its edge - and swapped back once the box has gone (SWAPPED). Cheap when there's no box (one slot
# looked at: the box's, BOX_SLOT) - every frame of play runs it, and busy ones have no time to spare. The box's edge on the fix layer: from pixel BOX_LEFT
# across, BOX_TOP down (its black outline included). Each copy is a tile of its own (a clear one too, for a cell
# the box covers whole), so it can be told from the heart it was made from and swapped back.
HUD_CALL = 0x11828              # jsr 0x4E4B8 - the HUD, each frame of play
HUD = 0x4E4B8
BOX = (0x21562, 0x3254, 0xA800, 0x4800)   # the box's object: its code, frame, y and x (the same in every lottery)
BOX_SLOT = 0x104600             # (its object slot - the same in every lottery)
SWAPPED = 0x10EA68              # a byte (spare RAM): the hearts swapped for their copies
BOX_LEFT, BOX_TOP = 22, 43      # (fix-layer pixels: column 2's 7th; row 5's 4th)
COLUMNS, ROWS = range(1, 11), (5, 6)   # player 1's hearts: up to 5, two columns each


def heart_words(rom, hud):
    """hud's heart tiles by row: {row: [fix words]} - got as hud got them (its share=True tiles: the same words)."""
    words = {5: set(), 6: set()}
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
    copies = {}                                   # (word, mask) -> its copy's word
    cells = ""
    for row in ROWS:
        for col in COLUMNS:
            mask = tuple((x, y) for y in range(8) for x in range(8) if covered(col, row, x, y))
            if not mask:
                continue
            pairs = []
            for word in words[row]:
                if (word, mask) not in copies:
                    px = rom.fix_tile(word & 0xFFF, built=True)    # (hud's tiles)
                    px = [[0 if (x, y) in mask else px[y][x] for x in range(8)] for y in range(8)]
                    copies[word, mask] = word & 0xF000 | rom.add_fix_tile(
                        px, why="lottery: a heart under the text box (row %d, %s)" % (
                            row, "whole" if len(mask) == 64 else "its edge"))
                pairs.append((word, copies[word, mask]))
            cells += "    .word 0x%X,%d\n" % (0x7000 + col * 32 + row, len(pairs) - 1)
            cells += "".join("    .word 0x%X,0x%X\n" % p for p in pairs)
    assert rom.data[HUD_CALL:HUD_CALL + 6] == bytes.fromhex("4EB9") + HUD.to_bytes(4, "big")
    code = rom.place_code(r"""
| the HUD, then the hearts under the lottery's text box swapped (box up) or back (box gone)
    jsr 0x%(hud)X
    movem.l %%d0-%%d4/%%a0-%%a1,-(%%sp)
    moveq #0,%%d3                       | d3: the box up?
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
2:  tst.b 0x%(swapped)X                 | (no box: the hearts put back, once)
    beq 10f
    clr.b 0x%(swapped)X
3:  lea cells(%%pc),%%a1
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
4:  move.w (%%a1)+,%%d0                 | a cell: its address (0: done), its pairs (heart, copy) - 1
    beq 9f
    move.w (%%a1)+,%%d1
    move.w %%d0,0x3C0000
    move.w 0x3C0002,%%d2                | what's there
5:  move.w (%%a1)+,%%d4                 | the heart
    tst.w %%d3
    beq 6f
    cmp.w %%d4,%%d2                     | (box up: the heart -> its copy)
    bne 7f
    move.w %%d0,0x3C0000
    move.w (%%a1),0x3C0002
    bra 7f
6:  cmp.w (%%a1),%%d2                   | (box gone: the copy -> the heart)
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
