NAME = "how-to-play-look"
DESCRIPTION = "How-to-play cinema: the title a row higher (off the demo); the B, C and D buttons yellow, green and blue"

# The cinema (0x1111C) prints its title with `lea text,a0 ; move.w #pos,d0 ; move.w #0xA000,d2 ; jsr 0x4DED6`
# (pos 0x62: fix column 3, row 2 of the text's own frame) - TITLE_POS, a row higher now. The control panel along the
# bottom is fix tiles (rows 24-27; 0x1A0EE draws it every frame at 0x7058, pressed buttons and all), all in fix
# palette 15, whose colours 5-9 are the buttons' red. Each frame, after the panel is drawn (the loop's `jsr 0x542C8`,
# its text schedule), palettes BUTTON_PALS get palette 15 with those colours recoloured and the B / C / D buttons'
# tiles (two columns each) are put in them.
TITLE_POS = 0x111CC          # move.w #0x62,d0
FRAME_CALL = 0x11206         # jsr 0x542C8
FIX = 0x7000
ROWS = range(24, 28)
BUTTON_COLUMNS = [10, 12, 14]                # B, C, D (A at 8)
BUTTON_PALS = [1, 2, 3]
PANEL = [0x8000, 0x0BBB, 0x0AAA, 0x0666, 0xF444, None, None, None, None, None, 0x0000, 0x7FFF, 0x204C, 0x0FF0,
         0x0FB0, 0x8000]                     # fix palette 15; colours 5-9 the red: 0800 0B00 0F66 0F33 0F00
BUTTON_COLOURS = [
    [0x0870, 0x0BA0, 0x0FE6, 0x0FD3, 0x0FD0],   # B yellow
    [0x0080, 0x00B0, 0x06F6, 0x03E3, 0x00D0],   # C green
    [0x0028, 0x003B, 0x069F, 0x036F, 0x004F],   # D blue
]


def apply(rom):
    words = []
    for colours in BUTTON_COLOURS:
        words += [c if c is not None else colours[i - 5] for i, c in enumerate(PANEL)]
    cols = "".join("    move.w #0x%X,%%d0\n    moveq #%d,%%d1\n    bsr button\n"
                   % (FIX + c * 32 + ROWS[0], pal) for c, pal in zip(BUTTON_COLUMNS, BUTTON_PALS))
    code = rom.place_code(r"""
    jsr 0x542C8
    movem.l %%d0-%%d3/%%a0-%%a1,-(%%sp)
    lea colours(%%pc),%%a0              | the buttons' palettes
    lea 0x%(pal_ram)X,%%a1
    moveq #%(words)d-1,%%d0
1:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,1b
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
%(cols)s
    move.w (%%sp)+,%%sr
    movem.l (%%sp)+,%%d0-%%d3/%%a0-%%a1
    rts

button:                                 | d0 = its first column's top tile, d1 = palette: both columns' tiles in it
    ror.w #4,%%d1
    moveq #1,%%d3
3:  moveq #%(rows)d-1,%%d2
2:  move.w %%d0,0x3C0000
    move.w 0x3C0002,%%a0
    move.w %%a0,-(%%sp)
    andi.w #0x0FFF,(%%sp)
    or.w %%d1,(%%sp)
    move.w %%d0,0x3C0000
    move.w (%%sp)+,0x3C0002
    addq.w #1,%%d0
    dbf %%d2,2b
    add.w #32-%(rows)d,%%d0
    dbf %%d3,3b
    rts

colours:
    .word %(colours)s
""" % {"pal_ram": 0x400000 + BUTTON_PALS[0] * 32, "words": len(words), "cols": cols, "rows": len(ROWS),
       "colours": ",".join("0x%04X" % w for w in words)},
        why="how-to-play: the B, C, D buttons coloured")
    rom.write(FRAME_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("4EB9000542C8"),
              why="how-to-play: the buttons coloured every frame")
    rom.write(TITLE_POS + 2, bytes.fromhex("0061"), expect=bytes.fromhex("0062"),
              why="how-to-play: the title a row higher")
