NAME = "wall-light"
DESCRIPTION = "Mechanical City: one light in a row of three blinking wall lights blinks yellow"

# Stage 28's grey machinery wall has a row of three blinking green lights: tile 0x2320 (auto-animated) in the
# wall's palette 0xB2, from the level's block data - the blocks whose tiles share one palette and attribute (0x80 kind) give each tile a byte, drawn by 0xD2F2
# as the screen scrolls up or down (`move.b (a4),d1 ; move.w d1,(a0) ; swap d1 ; move.w d1,(a0) ; swap d1`: a4 its
# byte, d1's high word the attributes) and by 0xCF10 as it scrolls sideways (the same with `move.b (a2)+,d1`).
# The level holds the row twice, one copy for each (0xA486D... and 0xA3C74...: 46 47 5A, the lights, 5A).
# Now the light from LIGHT_BYTES is drawn in palette LIGHT_PAL instead: the wall's colours with its greens (11-15,
# the lights) yellow - written to the palette as it is drawn.
DRAW_ROW = 0xD2F2
DRAW_COLUMN = 0xCF10
LIGHT_BYTES = [0xA4871, 0xA3C78]   # the middle light, in each copy (0xA4870-0xA4872, 0xA3C77-0xA3C79: left to right)
STAGE, LIGHT_STAGE = 0x103005, 28
LIGHT_PAL = 0xC7             # empty in the stage
COLOURS = [0x8000, 0x8DDD, 0x8CCC, 0x8BBB, 0x8AAA, 0x8999, 0x8888, 0x8777, 0x8666, 0x8555, 0x8444,  # 0xB2's greys
           0x8EC2, 0x0CA0, 0x0980, 0x0760, 0x8540]   # its greens 80C7 00A5 B083 3061 8050, now yellows


def apply(rom):
    code = rom.place_code(r"""
    bra.w row
    bra.w column

row:                                    | its byte at a4
    move.b (%%a4),%%d1
    move.l %%a4,-(%%sp)
    bra 5f
column:                                 | its byte at a2 (then the next)
    move.b (%%a2)+,%%d1
    move.l %%a2,-(%%sp)
    subq.l #1,(%%sp)
5:  move.w %%d1,(%%a0)                  | the tile
    swap %%d1
    cmpi.l #0x%(byte0)X,(%%sp)
    beq 6f
    cmpi.l #0x%(byte1)X,(%%sp)
6:  addq.l #4,%%sp                      | (flags kept)
    bne 1f
    cmpi.b #%(stage)d,0x%(stage_at)X
    bne 1f
    movem.l %%d0/%%a0-%%a1,-(%%sp)      | the light: its own palette ...
    lea colours(%%pc),%%a0
    lea 0x%(pal_ram)X,%%a1
    moveq #15,%%d0
2:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,2b
    movem.l (%%sp)+,%%d0/%%a0-%%a1
    move.w %%d1,-(%%sp)                 | ... in its attributes
    move.b #0x%(pal)X,(%%sp)
    move.w (%%sp)+,(%%a0)
    bra 3f
1:  move.w %%d1,(%%a0)
3:  swap %%d1
    rts
colours:
    .word %(colours)s
""" % {"byte0": LIGHT_BYTES[0], "byte1": LIGHT_BYTES[1], "stage": LIGHT_STAGE, "stage_at": STAGE, "pal_ram": 0x400000 + LIGHT_PAL * 32,
       "pal": LIGHT_PAL, "colours": ",".join("0x%04X" % c for c in COLOURS)},
        why="wall lights: one yellow")
    for at, entry, first, why in [(DRAW_ROW, 0, "1214", "rows"), (DRAW_COLUMN, 4, "121A", "columns")]:
        rom.write(at, bytes.fromhex("4EB9") + (code + entry).to_bytes(4, "big") + bytes.fromhex("4E714E71"),
                  expect=bytes.fromhex(first + "3081484130814841"),
                  why="block tiles (%s): the wall's light in its own palette" % why)
