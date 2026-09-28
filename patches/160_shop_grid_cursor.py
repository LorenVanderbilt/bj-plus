NAME = "shop-grid-cursor"
DESCRIPTION = "Fairy shop: no floating cursor - move box to box, the selected box gets a blue (1P) / green (2P) frame"

# In the fairy shop each player had a pointer (object slot 0 / 1, code 0x1FD6E / 0x1FD08 / 0x1FD38) that
# floated around under the joystick. Every frame, after 0x1FD9A, it asks the collision routine 0xB642 which
# item object it touches (the items are objects in slots 9-17, item index at +41: 1-7 goods, 8 = EXIT); when
# that changes it types the item's description in the player's own speech bubble (P1 top, P2 bottom), and
# 0x1FF60 buys the item under it on a button press. Its movement comes from the joystick direction
# (0x1FE30, via the velocity table at 0x1FF20).
#
# - The `jsr 0xB642` (0x1FDAE) now goes to `pick` below instead: it keeps each player's box on a 2x4 grid,
#   moves it one box per new Up/Down/Left/Right press (stopping at the edges), and returns the item object
#   sitting in that box (or "nothing" for an empty box) exactly like 0xB642 did - so the descriptions,
#   buying and EXIT all work as before. It also hides the pointer (+8 = 0, as the game itself does).
# - The joystick direction the movement reads (0x1FE30) is replaced by 0, so the hidden pointer stays put.
# - The shop's main loop (0x1F86E, and the closing loop at 0x1F8D2) calls `frames` each frame, which draws
#   a thin frame just inside the gold border of each player's box on the fix layer: blue for player 1,
#   green for player 2, left half blue / right half green when both are on the same box. It redraws only
#   when a box changes, and erases a player's frame once their pointer stops running (they left the shop).
#
# The frame is made of new fix-layer tiles (fix tiles 0x300+, a run that is blank in the S ROM and never
# drawn by the game), generated below from the boxes' inner edges, in fix palette 14 (unused by the fix
# layer) colors 11 and 12 (black filler in that palette), which are set to blue and green every frame.
BOX_COLUMNS = [(38, 90), (101, 153)]                        # inner (black) area of each box, screen x
BOX_ROWS = [(22, 58), (69, 106), (117, 154), (165, 201)]    # and screen y, top to bottom
GRID_X = [0x5000, 0x7000]                                   # item object x / y for each column / row
GRID_Y = [0xA800, 0x9000, 0x7800, 0x6000]
START_BOX = [6, 7]                                          # player 1 bottom left, player 2 bottom right (EXIT)
THICKNESS = 2                                               # frame line width in pixels
FIRST_TILE = 0x300
PALETTE, BLUE_INDEX, GREEN_INDEX = 14, 11, 12
BLUE, GREEN = 0x126F, 0x23F3                                # Neo Geo colors
BLANK = 0x0520                                              # the fix layer's blank cell (as 0x9FBE fills it)

PICK_SITE = 0x1FDAE        # jsr 0xB642
MOVE_SITE = 0x1FE30        # move.b 0x786A(a6),d2  (joystick direction for the pointer's velocity)
LOOP_SITES = [(0x1F86E, "422E78664EBA1CEE"), (0x1F8D2, "422E78664EBA1C8A")]   # clr.b 0x7866(a6) ; jsr 0x21562
TYPEWRITER = 0x21562
FRAME_COUNTER = 0x100204   # long, +1 every vblank
RAM = 0x10C220             # spare RAM: see the offsets in the code


def frame_pixels(box, mode):
    """{(x, y) fix-layer pixel: color index} of one box's frame; mode 0 blue, 1 green, 2 split."""
    (x0, x1), (y0, y1) = BOX_COLUMNS[box % 2], BOX_ROWS[box // 2]
    y0, y1 = y0 + 16, y1 + 16                    # screen y 0 is fix row 2
    mid = (x0 + x1 + 1) // 2
    out = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x < x0 + THICKNESS or x > x1 - THICKNESS or y < y0 + THICKNESS or y > y1 - THICKNESS:
                blue = mode == 0 or (mode == 2 and x < mid)
                out[(x, y)] = BLUE_INDEX if blue else GREEN_INDEX
    return out


def apply(rom):
    tiles = {}                                   # pixel rows -> tile number
    draws, erases = [], []
    for box in range(8):
        cells_used = set()
        for mode in range(3):
            px = frame_pixels(box, mode)
            cells = sorted({(x // 8, y // 8) for x, y in px})
            entries = []
            for cx, cy in cells:
                rows = tuple(tuple(px.get((cx * 8 + x, cy * 8 + y), 0) for x in range(8)) for y in range(8))
                if rows not in tiles:
                    tiles[rows] = FIRST_TILE + len(tiles)
                entries.append((0x7000 + cx * 32 + cy, PALETTE << 12 | tiles[rows]))
                cells_used.add((cx, cy))
            draws.append(entries)
        erases.append(sorted(0x7000 + cx * 32 + cy for cx, cy in cells_used))
    if len(tiles) > 0x100:
        raise SystemExit("shop frame needs %d tiles, more than the 256 free slots" % len(tiles))
    for rows, n in tiles.items():
        rom.put_fix_tile(n, rows, why="shop selection frame piece")

    def table(name, lists, fmt):
        out = "%s:\n" % name + "".join("    .word %s_%d-%s\n" % (name, i, name) for i in range(len(lists)))
        for i, entries in enumerate(lists):
            out += "%s_%d:\n    .word %d\n" % (name, i, len(entries))
            out += "".join(fmt(e) for e in entries)
        return out
    data = (table("draw_tab", draws, lambda e: "    .word 0x%04X,0x%04X\n" % e) +
            table("erase_tab", erases, lambda a: "    .word 0x%04X\n" % a))

    # RAM (bytes from RAM): +0/+1 each player's box, +2/+3 last frame's joystick, +4..+11 the frame number each
    # player's pointer last ran (long each), +12/+13 the boxes the frames are drawn on (0xFF none)
    src = r"""
| ---- replaces jsr 0xB642 in the pointer's per-frame code: a5 = pointer object, a4 = player block.
| Returns a0 = the item object in this player's box and Z clear, or Z set if the box is empty.
pick:
    movem.l %d0-%d4/%a1,-(%sp)
    lea RAM,%a1
    moveq #0,%d3                    | d3 = player
    cmpa.l #0x107000,%a4
    beq 1f
    moveq #1,%d3
1:  move.w %d3,%d1
    lsl.w #2,%d1
    move.l FRAME_COUNTER,%d0
    move.l %d0,%d2
    sub.l 4(%a1,%d1.w),%d2          | frames since this pointer last ran
    move.l %d0,4(%a1,%d1.w)
    cmp.l #4,%d2
    bls 2f
    lea start_box(%pc),%a0          | a new shop visit: start box, and treat the stick as held
    move.b (%a0,%d3.w),(%a1,%d3.w)
    move.b #0xFF,2(%a1,%d3.w)
2:  move.b 0x10FD96,%d0             | this player's joystick (bits 0-3 up down left right)
    tst.w %d3
    beq 3f
    move.b 0x10FD9C,%d0
3:  and.b #15,%d0
    move.b 2(%a1,%d3.w),%d1
    move.b %d0,2(%a1,%d3.w)
    not.b %d1
    and.b %d1,%d0                   | d0 = newly pressed directions
    moveq #0,%d2
    move.b (%a1,%d3.w),%d2          | d2 = box = row * 2 + column
    btst #0,%d0                     | up
    beq 4f
    cmp.b #2,%d2
    bcs 4f
    subq.b #2,%d2
4:  btst #1,%d0                     | down
    beq 5f
    cmp.b #6,%d2
    bcc 5f
    addq.b #2,%d2
5:  btst #2,%d0                     | left
    beq 6f
    btst #0,%d2
    beq 6f
    subq.b #1,%d2
6:  btst #3,%d0                     | right
    beq 7f
    btst #0,%d2
    bne 7f
    addq.b #1,%d2
7:  move.b %d2,(%a1,%d3.w)
    clr.w 8(%a5)                    | hide the pointer
    move.w %d2,%d0                  | the item object sitting in this box, if any
    and.w #1,%d0
    add.w %d0,%d0
    move.w grid_x(%pc,%d0.w),%d1
    move.w %d2,%d0
    lsr.w #1,%d0
    add.w %d0,%d0
    move.w grid_y(%pc,%d0.w),%d0
    lea 0x104480,%a0
    moveq #8,%d4
8:  tst.b 40(%a0)
    beq 9f
    cmp.w (%a0),%d0
    bne 9f
    cmp.w 2(%a0),%d1
    bne 9f
    and.b #0xFB,%ccr                | found: Z clear (movem below leaves the flags alone)
    bra 10f
9:  lea 0x80(%a0),%a0
    dbf %d4,8b
    or.b #4,%ccr                    | empty box: Z set
10: movem.l (%sp)+,%d0-%d4/%a1
    rts
grid_x:
    .word GRID_X
grid_y:
    .word GRID_Y
start_box:
    .byte START_BOX
    .even
"""
    frames_src = r"""
| ---- called from the shop's main loop in place of `clr.b 0x7866(a6) ; jsr 0x21562`
frames:
    clr.b 0x7866(%a6)
    jsr TYPEWRITER
    movem.l %d0-%d7/%a0-%a1,-(%sp)
    move.w #BLUE,PAL_BLUE
    move.w #GREEN,PAL_GREEN
    lea RAM,%a1
    move.l FRAME_COUNTER,%d0
    moveq #-1,%d4                   | d4 / d5 = player 1 / 2 box, 0xFF = not in the shop
    moveq #-1,%d5
    move.l %d0,%d1
    sub.l 4(%a1),%d1
    cmp.l #4,%d1
    bhi 11f
    move.b (%a1),%d4
11: move.l %d0,%d1
    sub.l 8(%a1),%d1
    cmp.l #4,%d1
    bhi 12f
    move.b 1(%a1),%d5
12: cmp.b 12(%a1),%d4
    bne 13f
    cmp.b 13(%a1),%d5
    beq 19f
13: move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.b 12(%a1),%d0              | erase the old frames
    bsr erase
    move.b 13(%a1),%d0
    bsr erase
    move.b %d4,12(%a1)
    move.b %d5,13(%a1)
    cmp.b %d4,%d5
    bne 14f
    move.b %d4,%d0                  | both on one box: split
    moveq #2,%d1
    bsr draw
    bra 18f
14: move.b %d4,%d0
    moveq #0,%d1
    bsr draw
    move.b %d5,%d0
    moveq #1,%d1
    bsr draw
18: move.w (%sp)+,%sr
19: movem.l (%sp)+,%d0-%d7/%a0-%a1
    rts

| d0.b = box (anything >= 8 = none), d1 = mode 0 blue / 1 green / 2 split
draw:
    cmp.b #8,%d0
    bcc 21f
    and.w #7,%d0
    mulu #3,%d0
    add.w %d1,%d0
    add.w %d0,%d0
    lea draw_tab(%pc),%a0
    move.w (%a0,%d0.w),%d0
    add.w %d0,%a0
    move.w (%a0)+,%d2
    bra 22f
20: move.w (%a0)+,0x3C0000
    move.w (%a0)+,0x3C0002
22: dbf %d2,20b
21: rts

| d0.b = box (>= 8 = none): blank its frame cells
erase:
    cmp.b #8,%d0
    bcc 24f
    and.w #7,%d0
    add.w %d0,%d0
    lea erase_tab(%pc),%a0
    move.w (%a0,%d0.w),%d0
    add.w %d0,%a0
    move.w (%a0)+,%d2
    bra 25f
23: move.w (%a0)+,0x3C0000
    move.w #BLANK,0x3C0002
25: dbf %d2,23b
24: rts

DATA
"""
    consts = {
        "RAM": "0x%X" % RAM, "FRAME_COUNTER": "0x%X" % FRAME_COUNTER, "TYPEWRITER": "0x%X" % TYPEWRITER,
        "GRID_X": ",".join("0x%04X" % v for v in GRID_X), "GRID_Y": ",".join("0x%04X" % v for v in GRID_Y),
        "START_BOX": ",".join(str(v) for v in START_BOX),
        "PAL_BLUE": "0x%X" % (0x400000 + PALETTE * 32 + BLUE_INDEX * 2),
        "PAL_GREEN": "0x%X" % (0x400000 + PALETTE * 32 + GREEN_INDEX * 2),
        "BLUE": "0x%04X" % BLUE, "GREEN": "0x%04X" % GREEN, "BLANK": "0x%04X" % BLANK, "DATA": data,
    }
    for k in sorted(consts, key=len, reverse=True):
        src = src.replace(k, consts[k])
        frames_src = frames_src.replace(k, consts[k])
    pick = rom.place_code(src, why="shop grid cursor: each player's box, moved one box per press")
    frames = rom.place_code(frames_src, why="shop grid cursor: draws / erases the blue and green frames")
    rom.write(PICK_SITE, bytes.fromhex("4EB9") + pick.to_bytes(4, "big"), expect=bytes.fromhex("4EB90000B642"),
              why="shop pointer: the item comes from the player's box, not from collision")
    rom.write(MOVE_SITE, bytes.fromhex("74004E71"), expect=bytes.fromhex("142E786A"),
              why="shop pointer: no free movement")
    for site, orig in LOOP_SITES:
        rom.write(site, bytes.fromhex("4EB9") + frames.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex(orig), why="shop loop: draw the selection frames each frame")
