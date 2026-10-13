NAME = "sold-out-stamp"
DESCRIPTION = "Fairy shop: an item the player already has is stamped SOLD OUT (a red, tilted rubber stamp over its box)"

import os
import random

# The shop's items are objects in slots 9-17 (shop-grid-cursor): +41 the item (1-7; 8 = EXIT), +0 / +2 its y / x
# (one of GRID_Y / GRID_X: its box). Each frame of the shop's loops (LOOP_SITES, after shop-grid-cursor's routine),
# every item whose routine (the shop's table, as shop-sold-out-first finds it) is one of SOLD's and that every player
# in the shop already has gets STAMP drawn over its box: four sprites (one 16-pixel-tall column each, chained) in
# sprite slots from SLOT_BASE - far above what the shop's objects use, so the drawing loop never touches them. When
# the shop has faded out (CLOSE_SITE), the drawing loop's last count (both lists') is set to the top, so its next
# frame clears every sprite above what it draws - the stamps too.
# The stamp: ART as drawn; without it, drawn here - a frame and SOLD OUT in a bold 5x7 hand, the whole
# tilted RISE pixels up to the right (the letters each kept whole, on steps), the frame with a few pixels left out
# (the stamp's wear); red from fix palette 4 (the hearts' - palettes 0-15 are the sprites' too, and fix palettes
# never change), entry RED.
ART = "art/shop/sold_out.png"  # the stamp as drawn (up to 64 x 32; fix palette 4's colours, index 0 clear), centred on
                               # each box - else the one drawn below, W x H
W, H = 52, 16                  # (the boxes inside their gold frames: 52 x 36)
RISE = 3
WEAR = 0.07
PALETTE, RED = 4, 14
FONT = {
    "S": ["01111", "11000", "11000", "01110", "00011", "00011", "11110"],
    "O": ["01110", "11011", "11011", "11011", "11011", "11011", "01110"],
    "L": ["11000", "11000", "11000", "11000", "11000", "11000", "11111"],
    "D": ["11110", "11011", "11011", "11011", "11011", "11011", "11110"],
    "U": ["11011", "11011", "11011", "11011", "11011", "11011", "01110"],
    "T": ["11111", "01100", "01100", "01100", "01100", "01100", "01100"],
}
LOOP_SITES = [0x1F86E, 0x1F8D2]   # jsr <shop-grid-cursor's frame routine> ; nop
CLOSE_SITE = 0x1F8F4              # jsr <shop-grid-cursor's fade-out>
ITEMS = [0x104000 + n * 0x80 for n in range(9, 18)]
ACTIVE, ITEM = 0x28, 41
SHOP_TABLES, SHOP = 0x1FF90, 0x1078F6   # (shop-sold-out-first: a table per shop, a routine per item)
GRID_X = [0x5000, 0x7000]               # (shop-grid-cursor: the items' x / y for each column / row)
GRID_Y = [0xA800, 0x9000, 0x7800, 0x6000]
BOX_COLUMNS = [(38, 90), (101, 153)]    # (the boxes' inner areas, screen x / y)
BOX_ROWS = [(22, 58), (69, 106), (117, 154), (165, 201)]
SOLD = [   # (the item's routines, player byte, "set" = has it when nonzero / "two" = when 2 / "full" = when it equals
           # the byte after it in the tuple) - shop-sold-out-first's, and nectar's own check (life at its maximum)
    ((0x2028C, 0x20286), 0x20, "full", 0x11),     # nectar (its SORRY, SOLD OUT! while life is full)
    ((0x2038A, 0x20390, 0x20396), 0x15, "set"),   # flippers
    ((0x20458, 0x2045E), 0x13, "set"),            # ice shoes (spike)
    ((0x204C8,), 0x18, "set"),                    # light safe (either safe)
    ((0x20550,), 0x18, "two"),                    # super safe
    ((0x2069E, 0x206A6), 0x14, "set"),            # fern (spring)
    ((0x2070C,), 0x2A, "set"),                    # ocarina
]
PLAYERS = 0x106800                      # bit 0 / 1: player 1 / 2 in the game
BLOCKS = [0x107000, 0x107400]
SLOT_BASE, STAMPS = 352, 7              # sprite slots 352-379: up to 7 stamps of 4 (above the rest: on top)
LAST_COUNTS = [0x1002E8, 0x1002F8]      # the drawing loop's lists (0x1002E0 / 0x1002F0): their last count


def stamp():
    """H rows of W pixels, 1 = red: the frame tilted pixel by pixel, each letter whole on its own step of the tilt."""
    rise = lambda x: RISE // 2 - round(RISE * x / (W - 1))     # (rows to move at column x: up to the right)
    out = [[0] * W for _ in range(H)]
    for x in range(1, W - 1):
        for y in (2, H - 2):
            if 0 <= y + rise(x) < H:
                out[y + rise(x)][x] = 1
    for y in range(2, H - 1):
        for x in (1, W - 2):
            out[y + rise(x)][x] = 1
    wear = random.Random(7)
    out = [[v if not v or wear.random() >= WEAR else 0 for v in row] for row in out]   # (the frame worn, not the letters)
    text = "SOLD OUT"
    widths = [3 if c == " " else 5 for c in text]
    x, top = (W - sum(widths) - len(text) + 1) // 2, (H - 7) // 2
    for c, width in zip(text, widths):
        step = rise(x + width // 2)
        for r, row in enumerate(FONT.get(c, [])):
            for i, bit in enumerate(row):
                if bit == "1":
                    out[top + r + step][x + i] = 1
        x += width + 1
    return out


def palette_colours(rom):
    """Fix palette 4 as RGB (from the fix palettes' table, 0x1000)."""
    from png_tiles import neo_to_rgb
    return [neo_to_rgb(rom.u16(0x1000 + PALETTE * 32 + 2 * i)) for i in range(16)]


def art(rom):
    """The stamp's pixels (palette 4 entries; 0 = clear): ART if it's there, else stamp()."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ART)
    if os.path.exists(path):
        from png_tiles import read_indices
        px = read_indices(path, palette_colours(rom))
        assert len(px) <= 32 and len(px[0]) <= 64, "%s: at most 64 x 32" % ART
        return px
    return [[RED if v else 0 for v in row] for row in stamp()]


def apply(rom):
    px = art(rom)
    width, height = len(px[0]), len(px)
    cols, rows = (width + 15) // 16, (height + 15) // 16
    tiles = [[rom.add_sprite_tile([[px[r * 16 + y][c * 16 + x] if r * 16 + y < height and c * 16 + x < width else 0
                                    for x in range(16)] for y in range(16)],
                                  why="SOLD OUT stamp, column %d row %d" % (c, r)) for r in range(rows)]
             for c in range(cols)]
    loop = rom.u32(LOOP_SITES[0] + 2)
    for at in LOOP_SITES:
        assert rom.u16(at) == 0x4EB9 and rom.u32(at + 2) == loop, "expected shop-grid-cursor's call"
    close = rom.u32(CLOSE_SITE + 2)
    sold = ""
    for i, (routines, flag, when, *_) in enumerate(SOLD):
        sold += "".join("    cmpa.l #0x%X,%%a1\n    beq sold%d\n" % (r, i) for r in routines)
    tests = ""
    for i, (routines, flag, when, *other) in enumerate(SOLD):
        def has(block):
            if when == "full":
                return "    move.b 0x%X,%%d1\n    cmp.b 0x%X,%%d1\n    bne 8f\n" % (block + flag, block + other[0])
            return {"set": "    tst.b 0x%X\n    beq 8f\n", "two": "    cmpi.b #2,0x%X\n    bne 8f\n"}[when] % (block + flag)
        tests += "sold%d:\n" % i + "".join(
            "    btst #%d,0x%X\n    beq 1f\n%s1:\n" % (p, PLAYERS, has(BLOCKS[p])) for p in range(2)) + \
            "    bra stamp\n"
    columns = "".join("    move.w #%d,%%d4\n    bsr column\n" % n for n in range(cols))
    places = []
    for gx, (bx0, bx1) in zip(GRID_X, BOX_COLUMNS):
        for gy, (by0, by1) in zip(GRID_Y, BOX_ROWS):
            places.append((gx, gy, (bx0 + bx1 + 1) // 2 - width // 2, (by0 + by1 + 1) // 2 - height // 2))
    code = rom.place_code(r"""
    bra.w each_frame
    bra.w closed
| the shop's fade-out done: the drawing loop's next frame clears every sprite above its own - the stamps too
closed:
    jsr 0x%(close)X
    move.w #%(top)d,0x%(last1)X
    move.w #%(top)d,0x%(last2)X
    rts
| each frame: the stamps over items every player has already
each_frame:
    jsr 0x%(loop)X
    movem.l %%d0-%%d7/%%a0-%%a2,-(%%sp)
    move.w #1,0x3C0004
    moveq #0,%%d7                       | (stamps drawn)
    lea items(%%pc),%%a2
    moveq #%(n_items)d-1,%%d6
item:
    movea.l (%%a2)+,%%a0
    tst.b %(active)d(%%a0)
    beq 8f
    moveq #0,%%d0
    move.b %(item)d(%%a0),%%d0
    beq 8f
    cmpi.b #8,%%d0
    bcc 8f
    lea 0x%(tables)X,%%a1               | (its routine: the shop's table)
    move.w 0x%(shop)X,%%d1
    lsl.w #2,%%d1
    movea.l (%%a1,%%d1.w),%%a1
    lsl.w #2,%%d0
    movea.l (%%a1,%%d0.w),%%a1
%(sold)s    bra 8f
%(tests)s
stamp:                                  | its box: the place matching its x / y
    lea places(%%pc),%%a1
    moveq #%(n_places)d-1,%%d0
2:  move.w (%%a1)+,%%d1
    move.w (%%a1)+,%%d2
    move.w (%%a1)+,%%d4
    move.w (%%a1)+,%%d5
    cmp.w 2(%%a0),%%d1
    bne 3f
    cmp.w 0(%%a0),%%d2
    beq 4f
3:  dbf %%d0,2b
    bra 8f
4:  cmpi.w #%(stamps)d,%%d7
    bcc 8f
    move.w %%d7,%%d3                    | (its first sprite: SLOT_BASE + 4 * stamps so far)
    lsl.w #2,%%d3
    add.w #%(base)d,%%d3
    move.w %%d4,%%d1                    | x, y (screen) -> SCB4, SCB3
    lsl.w #7,%%d1
    move.w #%(y_top)d,%%d2
    sub.w %%d5,%%d2
    lsl.w #7,%%d2
    addq.w #%(rows)d,%%d2                      | (its height in tiles)
    lea tiles(%%pc),%%a1
%(columns)s    addq.w #1,%%d7
8:  dbf %%d6,item
9:  cmpi.w #%(stamps)d,%%d7             | the stamps not drawn this frame: hidden
    bcc 10f
    move.w %%d7,%%d3
    lsl.w #2,%%d3
    add.w #%(base)d+0x8200,%%d3
    move.w %%d3,0x3C0000
    moveq #%(per)d-1,%%d0
5:  move.w #0,0x3C0002
    dbf %%d0,5b
    addq.w #1,%%d7
    bra 9b
10: movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a2
    rts
| one column of a stamp: sprite d3 + d4, tile d4 (a1: the tiles), x d1 / y d2 (the first column; the rest chained)
column:
    move.w %%d3,%%d0
    add.w %%d4,%%d0
    move.w %%d0,%%d5
    lsl.w #6,%%d5                       | SCB1: the tiles and their attributes
    move.w %%d5,0x3C0000
    move.w %%d4,%%d5
    mulu #%(rows)d*4,%%d5
    lea 0(%%a1,%%d5.w),%%a0
    moveq #%(rows)d*2-1,%%d5
7:  move.w (%%a0)+,0x3C0002
    dbf %%d5,7b
    move.w %%d0,%%d5
    add.w #0x8000,%%d5                  | SCB2: full size
    move.w %%d5,0x3C0000
    move.w #0x0FFF,0x3C0002
    add.w #0x200,%%d5                   | SCB3: y and height (chained after the first)
    move.w %%d5,0x3C0000
    move.w %%d2,%%d0
    tst.w %%d4
    beq 6f
    move.w #0x40,%%d0
6:  move.w %%d0,0x3C0002
    add.w #0x200,%%d5                   | SCB4: x
    move.w %%d5,0x3C0000
    move.w %%d1,0x3C0002
    rts
items:
    .long %(items)s
places:
    .word %(places)s
tiles:
    .word %(tiles)s
""" % {"close": close, "loop": loop, "top": 381, "last1": LAST_COUNTS[0], "last2": LAST_COUNTS[1],
       "n_items": len(ITEMS), "active": ACTIVE, "item": ITEM, "tables": SHOP_TABLES, "shop": SHOP,
       "sold": sold, "tests": tests, "n_places": len(places), "stamps": STAMPS, "base": SLOT_BASE,
       "y_top": 496, "columns": columns, "per": cols, "rows": rows,
       "items": ",".join("0x%X" % a for a in ITEMS),
       "places": ",".join("0x%X,0x%X,%d,%d" % p for p in places),
       "tiles": ",".join("0x%X,0x%X" % (t & 0xFFFF, PALETTE << 8 | (t >> 16 & 15) << 4) for col in tiles for t in col)},
        why="fairy shop: SOLD OUT stamps")
    for at in LOOP_SITES:
        rom.write(at + 2, code.to_bytes(4, "big"), expect=loop.to_bytes(4, "big"),
                  why="fairy shop, each frame: the SOLD OUT stamps")
    rom.write(CLOSE_SITE + 2, (code + 4).to_bytes(4, "big"), expect=close.to_bytes(4, "big"),
              why="fairy shop faded out: the stamps cleared with the sprites above the drawing loop's")
