NAME = "title-banner"
DESCRIPTION = "Title screen: the bird tows a PLUS banner across under the logo and lets it go where it pops the balloon"

import os

# The title's bird (object code BIRD; +2 its x, +0 its y, a 32x32 sprite) flies right to left under the logo at
# 1.5 px a frame and pops Blue's balloon as its left edge passes screen x 140. On the title, x on screen is
# 2 * (+2 / 256) - 127 and the sprite's top is +0 / 256 - 20. ART (rope first, then the cloth) is drawn just behind it
# (its left edge GAP px right of the bird's) every frame of the title (title-menu's per-frame call FRAME_CALL), until it
# reaches STOP_X: there it stays and the bird flies on. Sprites SLOTS (one 16-px column each, chained) - above what the
# title draws (its last at 280); hidden and the state cleared as the title ends (LEAVE_CALL), so the next title tows
# it in again. Colours: its own, COLOURS (a GIMP palette: index 0 clear, then up to 15), written into palette PALETTE
# - empty on the title - while it's drawn (nothing changes the palettes until the title ends, when the next scene
# loads them all). Without the pictures: the placeholder, in fix palette 1 (palettes 0-15 never change).
# The cloth flutters: ARTS' pictures in SEQUENCE's order (0 = the first), FRAME_TIME frames each, round and round
# (TICK counts).
ARTS = ["art/title/bannerA1b%d.png" % n for n in range(1, 7)]   # all one size, up to 128 x 32, in
                               # COLOURS' colours (index 0 clear) - else the placeholder (one picture)
COLOURS = "art/title/banner_palette.gpl"
FRAME_TIME = 6
SEQUENCE = [0, 1, 2, 3, 4, 5]
FRAME_CALL = 0x1AF94           # jsr (the title's per-frame chain: title-menu, title-clouds)
LEAVE_CALL = 0x1B026           # jsr (the title's end chain)
BIRD = 0x1BF2E
OBJECTS, OBJECT_SIZE, LAST_OBJECT = 0x104000, 0x80, 0x107F80
ACTIVE = 0x28
GAP = 32                       # (the bird's width: the rope starts at its tail)
DROP = 6                      # (the banner's top, below the bird's)
STOP_X = 172                   # (where it is as the bird pops the balloon)
SLOT = 330
PALETTE = 0x7E
FIXED_PALETTE = 1              # (the placeholder's)
STATE = 0x10EA70               # a byte (spare RAM): 0 = not shown yet, 1 = towed, 2 = let go
BANNER_X = 0x10EA72            # two words: its x, y on screen once let go
TICK = 0x10EA76                # bytes: frames shown of this picture, the step in SEQUENCE
WHITE, RED, DARK, ROPE = 15, 13, 14, 5
FONT = {
    "P": ["11110", "11011", "11011", "11110", "11000", "11000", "11000"],
    "L": ["11000", "11000", "11000", "11000", "11000", "11000", "11111"],
    "U": ["11011", "11011", "11011", "11011", "11011", "11011", "01110"],
    "S": ["01111", "11000", "11000", "01110", "00011", "00011", "11110"],
}


def placeholder():
    """96 x 24: a rope (x 0-9), then the cloth - white, a red border, PLUS in red letters twice the font's size."""
    w, h = 96, 24
    px = [[0] * w for _ in range(h)]
    for x in range(0, 10):
        px[11][x] = px[12][x] = ROPE
    left, right = 10, 89
    for y in range(h):
        for x in range(left, right + 1):
            edge = y < 2 or y >= h - 2 or x < left + 2 or x > right - 2
            px[y][x] = RED if edge else WHITE
    for y in range(h):
        px[y][left] = px[y][left + 1] = DARK                   # (the pole the rope's tied to)
    x = left + (right - left + 1 - (4 * 10 + 3 * 2)) // 2
    for c in "PLUS":
        for r, row in enumerate(FONT[c]):
            for i, bit in enumerate(row):
                if bit == "1":
                    for dy in range(2):
                        for dx in range(2):
                            px[5 + 2 * r + dy][x + 2 * i + dx] = RED
        x += 12
    return px


def palette_colours(rom):
    """Fix palette FIXED_PALETTE as RGB (the placeholder's colours)."""
    from png_tiles import neo_to_rgb
    return [neo_to_rgb(rom.u16(0x1000 + FIXED_PALETTE * 32 + 2 * i)) for i in range(16)]


def own_colours():
    """COLOURS' 16 colours as RGB (a GIMP palette: one 'r g b name' a line after its header)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = []
    for line in open(os.path.join(root, COLOURS)):
        parts = line.split()
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            out.append(tuple(int(p) for p in parts[:3]))
    assert 2 <= len(out) <= 16, "%s: 2-16 colours" % COLOURS
    return out + [(0, 0, 0)] * (16 - len(out))


def pictures(rom):
    """ARTS' pixels (fix palette 1 entries; 0 = clear), those that are there - else [the placeholder]."""
    from png_tiles import read_indices
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = [read_indices(os.path.join(root, a), own_colours()) for a in ARTS if os.path.exists(os.path.join(root, a))]
    for px in out:
        assert len(px) == len(out[0]) and len(px[0]) == len(out[0][0]), "the banner's pictures differ in size"
        assert len(px) <= 32 and len(px[0]) <= 128, "the banner: at most 128 x 32"
    assert not out or max(SEQUENCE) < len(out), "SEQUENCE names a picture that isn't there"
    return out or [placeholder()]


def apply(rom):
    frames = pictures(rom)
    from png_tiles import rgb_to_neo
    own = any(os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), a)) for a in ARTS)
    palette = PALETTE if own else FIXED_PALETTE
    copy = ("""    lea colours(%%pc),%%a1             | its colours, while it's drawn
    lea 0x%X,%%a0
    moveq #15,%%d4
0:  move.w (%%a1)+,(%%a0)+
    dbf %%d4,0b
""" % (0x400000 + PALETTE * 32)) if own else ""
    colour_words = ",".join("0x%04X" % (rgb_to_neo(c) if i else 0) for i, c in enumerate(own_colours()))
    width, height = len(frames[0][0]), len(frames[0])
    cols, rows = (width + 15) // 16, (height + 15) // 16
    tiles = [[[rom.add_sprite_tile([[px[r * 16 + y][c * 16 + x] if r * 16 + y < height and c * 16 + x < width else 0
                                     for x in range(16)] for y in range(16)],
                                   why="title banner %d, column %d row %d" % (n + 1, c, r), share=True)
               for r in range(rows)] for c in range(cols)] for n, px in enumerate(frames)]
    frame_before, leave_before = rom.u32(FRAME_CALL + 2), rom.u32(LEAVE_CALL + 2)
    assert rom.u16(FRAME_CALL) == 0x4EB9 and rom.u16(LEAVE_CALL) == 0x4EB9
    tile_words = ",".join("0x%04X,0x%04X" % (t & 0xFFFF, palette << 8 | (t >> 16) << 4)
                          for picture in tiles for col in picture for t in col)
    hides = "".join("    move.w #0x%X,0x3C0000\n    move.w #0,0x3C0002\n" % (0x8200 + SLOT + c) for c in range(cols))
    code = rom.place_code(r"""
    bra.w frame
    bra.w leave

leave:
    jsr 0x%(leave_before)X
    move.l %%d0,-(%%sp)
    move.w #1,0x3C0004
%(hides)s    clr.b 0x%(state)X
    clr.w 0x%(tick)X
    move.l (%%sp)+,%%d0
    rts

frame:
    jsr 0x%(frame_before)X
    movem.l %%d0-%%d4/%%a0-%%a1,-(%%sp)
    cmpi.b #2,0x%(state)X
    beq 5f                              | (let go: where it stopped)
    lea 0x%(objects)X,%%a0              | the bird, if it's out
1:  tst.b %(active)d(%%a0)
    beq 2f
    cmpi.l #0x%(bird)X,4(%%a0)
    beq 3f
2:  lea %(size)d(%%a0),%%a0
    cmpa.l #0x%(last)X,%%a0
    bls 1b
    bra 9f                              | (none: not drawn)
3:  move.b #1,0x%(state)X
    move.w 2(%%a0),%%d0                 | x on screen: 2 * x - 127, then behind the bird
    lsr.w #7,%%d0
    sub.w #127-%(gap)d,%%d0
    move.w (%%a0),%%d1                  | y on screen: y - 20, then a little lower
    lsr.w #8,%%d1
    add.w #%(drop)d-20,%%d1
    cmpi.w #%(stop)d,%%d0
    bgt 6f
    move.w #%(stop)d,%%d0               | there: let go
    move.w %%d0,0x%(banner_x)X
    move.w %%d1,0x%(banner_x)X+2
    move.b #2,0x%(state)X
    bra 6f
5:  move.w 0x%(banner_x)X,%%d0
    move.w 0x%(banner_x)X+2,%%d1
6:
%(copy)s    move.w #1,0x3C0004                  | the banner: COLS columns from SLOT, the first at x, y
    and.w #511,%%d0
    lsl.w #7,%%d0
    move.w #496,%%d2
    sub.w %%d1,%%d2
    and.w #511,%%d2
    lsl.w #7,%%d2
    addq.w #%(rows)d,%%d2               | (its height in tiles)
    moveq #0,%%d4                       | (this step's picture)
    move.b 0x%(tick)X+1,%%d4
    lea sequence(%%pc),%%a1
    move.b (%%a1,%%d4.w),%%d4
    lea tiles(%%pc),%%a1
    mulu #%(cols)d*%(rows)d*4,%%d4
    adda.l %%d4,%%a1
    moveq #0,%%d3
7:  move.w %%d3,%%d4                    | SCB1: the column's tiles
    add.w #%(slot)d,%%d4
    lsl.w #6,%%d4
    move.w %%d4,0x3C0000
    moveq #%(rows)d*2-1,%%d4
8:  move.w (%%a1)+,0x3C0002
    dbf %%d4,8b
    move.w %%d3,%%d4
    add.w #%(slot)d+0x8000,%%d4         | SCB2: full size
    move.w %%d4,0x3C0000
    move.w #0x0FFF,0x3C0002
    add.w #0x200,%%d4                   | SCB3: y, height (the others stick to the first)
    move.w %%d4,0x3C0000
    move.w %%d2,0x3C0002
    add.w #0x200,%%d4                   | SCB4: x
    move.w %%d4,0x3C0000
    move.w %%d0,0x3C0002
    move.w #0x40+%(rows)d,%%d2           | (the rest: sticky)
    addq.w #1,%%d3
    cmpi.w #%(cols)d,%%d3
    bne 7b
    addq.b #1,0x%(tick)X                | the next picture after FRAME_TIME frames
    cmpi.b #%(frame_time)d,0x%(tick)X
    bne 9f
    clr.b 0x%(tick)X
    addq.b #1,0x%(tick)X+1
    cmpi.b #%(steps)d,0x%(tick)X+1
    bne 9f
    clr.b 0x%(tick)X+1
9:  movem.l (%%sp)+,%%d0-%%d4/%%a0-%%a1
    rts
colours:
    .word %(colours)s
sequence:
    .byte %(sequence)s
    .even
tiles:
    .word %(tiles)s
""" % {"frame_before": frame_before, "leave_before": leave_before, "hides": hides, "state": STATE,
       "banner_x": BANNER_X, "objects": OBJECTS, "active": ACTIVE, "bird": BIRD, "size": OBJECT_SIZE,
       "last": LAST_OBJECT, "gap": GAP, "drop": DROP, "stop": STOP_X, "slot": SLOT, "rows": rows, "cols": cols,
       "tiles": tile_words, "tick": TICK, "frame_time": FRAME_TIME, "steps": len(SEQUENCE),
       "sequence": ",".join(str(n) for n in SEQUENCE), "colours": colour_words, "copy": copy},
        why="title: the bird's PLUS banner")
    rom.write(FRAME_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + frame_before.to_bytes(4, "big"), why="title: the banner every frame")
    rom.write(LEAVE_CALL, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + leave_before.to_bytes(4, "big"), why="title: the banner hidden as it ends")
