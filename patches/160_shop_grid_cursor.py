NAME = "shop-grid-cursor"
DESCRIPTION = "Fairy shop: no floating cursor - move box to box; the selected box gets a blue (1P) / green (2P) frame with a white light chasing around it"

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
# - The pointers are also spawned hidden: the shop set-up creates them with 0xA158 from inline data whose
#   fourth field is the starting graphic (+8); that is 0 now, so they don't show during the fade-in.
# - The joystick direction the movement reads (0x1FE30) is replaced by 0, so the hidden pointer stays put.
# - The shop's main loop (0x1F86E, and the closing loop at 0x1F8D2) calls `frames` each frame, which draws
#   a thin frame just inside the gold border of each player's box on the fix layer: blue for player 1,
#   green for player 2, left half blue / right half green when both are on the same box. It redraws only
#   when a box changes, and erases a player's frame once their pointer stops running (they left the shop).
#   A white light with a fading tail chases around each frame - clockwise on player 1's, counter-clockwise
#   on player 2's, both at once (passing each other) on a shared box.
#
# The frame is made of new fix-layer tiles (rom.add_fix_tile: slots that are blank in the S ROM and never
# drawn by the game), generated below from the boxes' inner edges. The loop is cut into 30 segments clockwise
# from the top middle: 15 on the right half and 15 on the left, split at a tile boundary near the middle (x 64
# / 128), so every tile belongs to one half and each half gets its own palette. A pixel's color index is its
# segment number within its half (1-15). The chasing light is palette cycling: each frame, `frames` copies
# one step of a precomputed table into six fix palettes - right / left half for player 1 (blue), player 2
# (green) and a shared box (green right, blue left) - palettes the fix layer never uses. The game does load
# colors into them, though, so `frames` saves them the first time it runs and the shop's closing (before its
# fade-out, 0x1F8F4) puts them back.
BOX_COLUMNS = [(38, 90), (101, 153)]                        # inner (black) area of each box, screen x
BOX_ROWS = [(22, 58), (69, 106), (117, 154), (165, 201)]    # and screen y, top to bottom
GRID_X = [0x5000, 0x7000]                                   # item object x / y for each column / row
GRID_Y = [0xA800, 0x9000, 0x7800, 0x6000]
START_BOX = [6, 7]                                          # player 1 bottom left, player 2 bottom right (EXIT)
THICKNESS = 2                                               # frame line width in pixels
HALF_SEGMENTS = 15                                          # color indices 1-15 in each half
PALETTES = [(14, 13), (12, 11), (9, 7)]                     # (right, left) for player 1, player 2, both
BLUE, GREEN, WHITE = (4, 12, 31), (6, 31, 6), (31, 31, 31)  # 5-bit R, G, B
STEPS = 96                                                  # animation steps per lap (one per frame)
TAIL = 0.25                                                 # length of the fading tail, as a part of a lap
BLANK = 0x0520                                              # the fix layer's blank cell (as 0x9FBE fills it)

PICK_SITE = 0x1FDAE        # jsr 0xB642
SPAWN_GRAPHICS = [(0x1FB2C, 0x3044), (0x1FB5E, 0x3048), (0x1FBAE, 0x3048)]   # P1, P2, P2 (another layout)
MOVE_SITE = 0x1FE30        # move.b 0x786A(a6),d2  (joystick direction for the pointer's velocity)
LOOP_SITES = [(0x1F86E, "422E78664EBA1CEE"), (0x1F8D2, "422E78664EBA1C8A")]   # clr.b 0x7866(a6) ; jsr 0x21562
CLOSE_SITE = 0x1F8F4       # jsr 0x15724 - the shop's fade-out
FADE_OUT = 0x15724
TYPEWRITER = 0x21562
FRAME_COUNTER = 0x100204   # long, +1 every vblank
RAM = 0x10E920             # spare RAM: see the offsets in the code


def box_middle(box):
    """x where the right half starts: the tile boundary nearest the box's middle."""
    x0, x1 = BOX_COLUMNS[box % 2]
    return round((x0 + x1 + 1) / 2 / 8) * 8


def frame_pixels(box):
    """{(x, y) fix-layer pixel: segment 1-15 within its half} of one box's frame."""
    (x0, x1), (y0, y1) = BOX_COLUMNS[box % 2], BOX_ROWS[box // 2]
    y0, y1 = y0 + 16, y1 + 16                    # screen y 0 is fix row 2
    mid = box_middle(box)
    height, half = HALF_SEGMENTS, y1 - y0 + 1
    out = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if not (x < x0 + THICKNESS or x > x1 - THICKNESS or y < y0 + THICKNESS or y > y1 - THICKNESS):
                continue
            dt, db = y - y0, y1 - y
            if x >= mid:                           # right half, clockwise from the top middle
                a = x1 - mid + 1
                edge = min(dt, x1 - x, db)
                pos = x - mid if edge == dt else a + dt if edge == x1 - x else a + half + (x1 - x)
                out[(x, y)] = 1 + min(height - 1, pos * height // (2 * a + half))
            else:                                  # left half, clockwise from the bottom middle
                b = mid - x0
                edge = min(db, x - x0, dt)
                pos = mid - 1 - x if edge == db else b + db if edge == x - x0 else b + half + (x - x0)
                out[(x, y)] = 1 + min(height - 1, pos * height // (2 * b + half))
    return out


def neo_color(rgb):
    r, g, b = (max(0, min(31, round(c))) for c in rgb)
    return (r & 1) << 14 | (g & 1) << 13 | (b & 1) << 12 | (r >> 1) << 8 | (g >> 1) << 4 | (b >> 1)


def animation():
    """STEPS rows of 6 palettes x 15 colors (indices 1-15), in the order of PALETTES flattened."""
    lap = 2 * HALF_SEGMENTS
    rows = []
    for step in range(STEPS):
        head = step * lap / STEPS                            # clockwise light; player 2's runs the other way
        rows.append([])
        for mode in range(3):
            for right in (True, False):
                for seg in range(1, HALF_SEGMENTS + 1):
                    c = (seg - 0.5 + (0 if right else HALF_SEGMENTS)) # position around the loop, clockwise
                    cw = (head - c) % lap                    # how far behind each light this segment is
                    ccw = (c - (lap - head)) % lap
                    light = [cw, ccw, min(cw, ccw)][mode] / lap
                    glow = max(0.0, 1 - light / TAIL) ** 1.5
                    base = [BLUE, GREEN, GREEN if right else BLUE][mode]
                    rows[-1].append(neo_color([bc + (wc - bc) * glow for bc, wc in zip(base, WHITE)]))
    return rows


def apply(rom):
    tiles = {}                                   # pixel rows -> tile number
    draws, erases = [], []
    for box in range(8):
        px = frame_pixels(box)
        cells = sorted({(x // 8, y // 8) for x, y in px})
        box_tiles = []
        for cx, cy in cells:
            rows = tuple(tuple(px.get((cx * 8 + x, cy * 8 + y), 0) for x in range(8)) for y in range(8))
            if rows not in tiles:
                tiles[rows] = rom.add_fix_tile(rows, why="shop selection frame piece")
            box_tiles.append((0x7000 + cx * 32 + cy, tiles[rows], cx * 8 >= box_middle(box)))
        for right_pal, left_pal in PALETTES:      # the same tiles in each mode, just other palettes
            draws.append([(addr, (right_pal if right else left_pal) << 12 | tile) for addr, tile, right in box_tiles])
        erases.append([addr for addr, tile, right in box_tiles])

    def table(name, lists, fmt):
        out = "%s:\n" % name + "".join("    .word %s_%d-%s\n" % (name, i, name) for i in range(len(lists)))
        for i, entries in enumerate(lists):
            out += "%s_%d:\n    .word %d\n" % (name, i, len(entries))
            out += "".join(fmt(e) for e in entries)
        return out
    data = (table("draw_tab", draws, lambda e: "    .word 0x%04X,0x%04X\n" % e) +
            table("erase_tab", erases, lambda a: "    .word 0x%04X\n" % a) +
            "anim_tab:\n" + "".join("    .word %s\n" % ",".join("0x%04X" % c for c in row) for row in animation()))

    # RAM (bytes from RAM): +0/+1 each player's box, +2/+3 last frame's joystick, +4..+11 the frame number each
    # player's pointer last ran (long each), +12/+13 the boxes the frames are drawn on (0xFF none), +14 word
    # 0x5AA5 while the palettes are saved, +16 word animation step, +0x20.. the saved palettes (32 bytes each)
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
    movem.l %d0-%d7/%a0-%a2,-(%sp)
    lea RAM,%a1
    cmp.w #0x5AA5,14(%a1)           | the first time: save the palettes (put back when the shop closes)
    beq 30f
SAVE_PALETTES
    move.w #0x5AA5,14(%a1)
30: move.w 16(%a1),%d0              | the chasing light: this frame's step of the color table
    addq.w #1,%d0
    cmp.w #STEPS,%d0
    bcs 37f
    moveq #0,%d0
37: move.w %d0,16(%a1)
    mulu #6*HALF_SEGMENTS*2,%d0
    lea anim_tab(%pc),%a0
    add.l %d0,%a0
CYCLE_PALETTES
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
19: movem.l (%sp)+,%d0-%d7/%a0-%a2
    rts
"""
    close_src = r"""
| ---- the shop is closing (in place of its jsr to the fade-out): put the saved palettes back
close:
    movem.l %d0/%a0-%a2,-(%sp)
    lea RAM,%a1
    cmp.w #0x5AA5,14(%a1)
    bne 36f
RESTORE_PALETTES
    clr.w 14(%a1)
36: movem.l (%sp)+,%d0/%a0-%a2
    jmp FADE_OUT
"""
    frames_src += r"""

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
    saved = sorted({p for pair in PALETTES for p in pair})

    def copies(palettes, save):
        """Code copying each palette (16 words) to / from its slot in the save area (a1 = RAM)."""
        out = ""
        for i, pal in enumerate(palettes):
            ram, hw = "0x%X(%%a1)" % (0x20 + i * 32), "0x%X" % (0x400000 + pal * 32)
            src, dst = (hw, ram) if save else (ram, hw)
            out += "    lea %s,%%a0\n    lea %s,%%a2\n    moveq #15,%%d0\n5%d%d: move.w (%%a0)+,(%%a2)+\n    dbf %%d0,5%d%db\n" % (
                src, dst, int(save), i, int(save), i)
        return out

    consts = {
        "RAM": "0x%X" % RAM, "FRAME_COUNTER": "0x%X" % FRAME_COUNTER, "TYPEWRITER": "0x%X" % TYPEWRITER,
        "GRID_X": ",".join("0x%04X" % v for v in GRID_X), "GRID_Y": ",".join("0x%04X" % v for v in GRID_Y),
        "START_BOX": ",".join(str(v) for v in START_BOX),
        "SAVE_PALETTES": copies(saved, True), "RESTORE_PALETTES": copies(saved, False),
        "CYCLE_PALETTES": "".join("    lea 0x%X,%%a2\n    moveq #%d,%%d0\n4%d: move.w (%%a0)+,(%%a2)+\n    dbf %%d0,4%db\n"
                                  % (0x400002 + pal * 32, HALF_SEGMENTS - 1, i, i)
                                  for i, pal in enumerate(p for pair in PALETTES for p in pair)),
        "HALF_SEGMENTS": str(HALF_SEGMENTS), "STEPS": str(STEPS), "FADE_OUT": "0x%X" % FADE_OUT,
        "BLANK": "0x%04X" % BLANK, "DATA": data,
    }
    for k in sorted(consts, key=len, reverse=True):
        src = src.replace(k, consts[k])
        frames_src = frames_src.replace(k, consts[k])
        close_src = close_src.replace(k, consts[k])
    pick = rom.place_code(src, why="shop grid cursor: each player's box, moved one box per press")
    frames = rom.place_code(frames_src, why="shop grid cursor: draws / erases the frames, cycles the chasing light")
    close = rom.place_code(close_src, why="shop grid cursor: puts the saved palettes back when the shop closes")
    rom.write(CLOSE_SITE, bytes.fromhex("4EB9") + close.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + FADE_OUT.to_bytes(4, "big"), why="shop closing: restore palettes first")
    rom.write(PICK_SITE, bytes.fromhex("4EB9") + pick.to_bytes(4, "big"), expect=bytes.fromhex("4EB90000B642"),
              why="shop pointer: the item comes from the player's box, not from collision")
    rom.write(MOVE_SITE, bytes.fromhex("74004E71"), expect=bytes.fromhex("142E786A"),
              why="shop pointer: no free movement")
    for site, graphic in SPAWN_GRAPHICS:
        rom.write(site, bytes(2), expect=graphic.to_bytes(2, "big"), why="shop pointer: spawned hidden")
    for site, orig in LOOP_SITES:
        rom.write(site, bytes.fromhex("4EB9") + frames.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex(orig), why="shop loop: draw the selection frames each frame")
