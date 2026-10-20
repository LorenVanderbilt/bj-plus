NAME = "goal-bells-rock"
DESCRIPTION = "Goal stalk: its bells rock as it swings - each a little pendulum on its hook, swinging out as the stalk turns"

import math

# The goal's flower bells (sta/aes/goal_bell.sta) hang from the stalk's segments and followed its swing upright. Now
# each is a small pendulum on its hook: the hook's sideways acceleration (its x against the stalk's base - the
# screen scrolls - each frame) pushes it the other way, gravity pulls it back to hanging, damping settles it - so it
# lags as the stalk sets off, swings out as the stalk turns at the end of a bend, and each bell (its own rate, PARAMS)
# a little out of step with the rest. Its angle picks a drawing: 15 degrees past TILT_15, 30 past TILT_30.
# The hanging ones (HANGING: their routines, each starting with jsr PARENT - a0 its segment, the hook - and the frame
# it shows, set just before), and the top one (TOP_FRAME: while it swings it runs the segments' SWINGING routine;
# its jsr PARENT at TOP_SITE - itself the hook, on the stalk's base). Each bell's state (STATE, 16 bytes: the frame
# it was last updated - another means it's just come into play, and it starts hanging still - the hook's last x and
# speed, the angle and its speed: 1/64 degree, the frames since the stalk first moved) is spare RAM. The stalk's
# push fades over FADE frames from its first move, so each swing of the bells is smaller and they settle.
# The drawings are the bells' own art (3 shapes: the top one, and the left- and right-hooked hanging ones - each
# frame the shape in its own palette) turned about their top (the hook, or the top bell's knob) by RotSprite
# (Scale2x three times, turned, each pixel's centre sampled) - or, once painted, ART's pictures (each shape's in
# its first frame's colours, ART_COLOURS; DRAWN: the build writes them from RotSprite, and reads them as painted
# once it's False) - then laid on the tile grid where they need the fewest tiles (an even offset: pieces are
# placed in 2 px steps). A frame is a blank 1 x 1 grid and a piece per column of tiles.
# (Its own patch, last, so its code moves nothing.)
PARENT = 0x5E036               # a0 = the object's parent (+0x4E); tst.b 0x28(a0)
HANGING = [0x52B52, 0x52B80, 0x52BAE, 0x52BDC, 0x52C0A, 0x52C38]
TOP_FRAME = 0x20D0
TOP_SITE = 0x52A3A             # (in SWINGING, 0x52A0C: jsr PARENT - after its angle, +0x3A, is worked out)
ANGLES = [-30, -15, 15, 30]    # (degrees: the drawings; 0 is the bell as it is)
TILT_15, TILT_30 = 8, 22       # (degrees swung: the drawing past each)
PARAMS = [(10, 15, 147), (13, 15, 230), (12, 15, 360), (12, 15, 147), (11, 15, 230), (14, 15, 360), (9, 15, 110)]
                               # (each bell, HANGING's order then the top one: its pull back to hanging, its damping,
                               # its push from the hook's acceleration - /256 a frame. Higher bells' hooks move more:
                               # the lower ones get more push)
FADE = 230                     # (frames: the stalk's push on the bells fades to nothing over them - each swing smaller)
STATE = 0x10E860               # 7 x 16 bytes (spare RAM, to 0x10E8CF)
FRAME = 0x100206               # (a word counted each frame)
FRAME_TABLE = 0x60772
ART = "art/goal_bells/bell_%04X_%+d.png"   # (a shape's first frame, the angle) - 64 x 56: the frame's (0, 0) at (16, 8)
ART_ORIGIN = (16, 8)
DRAWN = False                  # True: each build draws ART with RotSprite (and rewrites it) - False once painted
ART_COLOURS = {                # (the bells' palettes, as the goal loads them)
    0x74: "0444 8EFF BDEE BCDD 3BCC 3ABB BBFC 08E9 76C8 BAF8 B7C5 B492 B9AA 0CDD FEFF FFFF",
    0x75: "0444 CF77 7F55 5F43 6F22 EF00 CFBB 0F88 7D55 BAF8 B7C5 B492 4D00 7F88 FFCC FFFF",
    0x76: "0444 FFAA CFAA CF99 CF88 FF66 FFDD 4FBB FE89 BAF8 B7C5 B492 FE55 4FCC CFEE FFFF",
}


def frame_tiles(rom, frame):
    """A 2 x 2 tile frame's [[tile, tile], [tile, tile]] (rows) and palette."""
    p = rom.u32(FRAME_TABLE + frame)
    d = rom.data
    assert d[p:p + 2] == bytes([1, 1]), (hex(frame), d[p:p + 5].hex())
    mode, palette, hi = d[p + 2], d[p + 3], d[p + 4]
    q, cols = p + 5, []
    for c in range(2):
        col = []
        for r in range(2):
            b = d[q]; q += 1
            if b == 1:
                a = d[q]; q += 1
                assert a == 0x20, (hex(frame), a)
                hi = d[q]; q += 1
                b = d[q]; q += 1
            col.append((hi << 8) | b)
        cols.append(col)
    assert d[q] == 0xFF
    return [[cols[0][0], cols[1][0]], [cols[0][1], cols[1][1]]], palette, mode


def pixels(rom, tiles):
    out = [[0] * 32 for _ in range(32)]
    for r in range(2):
        for c in range(2):
            t = rom.sprite_tile(tiles[r][c])
            for y in range(16):
                for x in range(16):
                    out[r * 16 + y][c * 16 + x] = t[y][x]
    return out


def scale2x(px):
    h, w = len(px), len(px[0])
    out = [[0] * (w * 2) for _ in range(h * 2)]
    g = lambda y, x: px[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]
    for y in range(h):
        for x in range(w):
            P, A, B, C, D = px[y][x], g(y - 1, x), g(y, x + 1), g(y, x - 1), g(y + 1, x)
            out[2 * y][2 * x] = A if C == A and C != D and A != B else P
            out[2 * y][2 * x + 1] = B if A == B and A != C and B != D else P
            out[2 * y + 1][2 * x] = C if D == C and D != B and C != A else P
            out[2 * y + 1][2 * x + 1] = D if B == D and B != A and D != C else P
    return out


def rotate(px, deg):
    """px turned deg (clockwise +) about its top by RotSprite: {(x, y): index} in the frame's own coordinates."""
    for y in range(32):
        xs = [x for x in range(32) if px[y][x]]
        if xs:
            pv = (sum(xs) / len(xs), y)
            break
    big = scale2x(scale2x(scale2x(px)))
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = {}
    for Y in range(-ART_ORIGIN[1], 56 - ART_ORIGIN[1]):
        for X in range(-ART_ORIGIN[0], 64 - ART_ORIGIN[0]):
            dx, dy = X + 0.5 - pv[0], Y + 0.5 - pv[1]
            bx, by = int(math.floor((ca * dx + sa * dy + pv[0]) * 8)), int(math.floor((-sa * dx + ca * dy + pv[1]) * 8))
            if 0 <= bx < 256 and 0 <= by < 256 and big[by][bx]:
                out[(X, Y)] = big[by][bx]
    return out


def art(rom, frame, palette, px, deg):
    """The drawing at deg: ART's picture as painted, or (DRAWN) RotSprite's, written there."""
    import os
    from png_tiles import neo_to_rgb, write_indexed, read_indices
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, ART % (frame, deg))
    colours = [neo_to_rgb(int(w, 16)) for w in ART_COLOURS[palette].split()]
    assert len(set(colours[1:])) == 15, "goal bells: palette 0x%X has a colour twice - a picture can't name it" % palette
    if DRAWN or not os.path.exists(path):
        drawing = rotate(px, deg)
        rows = [[drawing.get((x - ART_ORIGIN[0], y - ART_ORIGIN[1]), 0) for x in range(64)] for y in range(56)]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_indexed(path, rows, colours)
        return drawing
    rows = read_indices(path, colours)
    return {(x - ART_ORIGIN[0], y - ART_ORIGIN[1]): v for y, row in enumerate(rows) for x, v in enumerate(row) if v}


def layout(art):
    """The fewest tiles: the grid's origin (even, px) and its cells {(col, row): 16 x 16 pixels}."""
    xs = [x for x, _ in art]; ys = [y for _, y in art]
    best = None
    for ox in [x for x in range(min(xs) - 15, min(xs) + 1) if x % 2 == 0]:
        for oy in [y for y in range(min(ys) - 15, min(ys) + 1) if y % 2 == 0]:
            cells = {((x - ox) // 16, (y - oy) // 16) for x, y in art}
            if best is None or len(cells) < len(best[2]):
                best = (ox, oy, cells)
    ox, oy, cells = best
    out = {}
    for c, r in cells:
        out[(c, r)] = [[art.get((ox + c * 16 + x, oy + r * 16 + y), 0) for x in range(16)] for y in range(16)]
    return ox, oy, out


def apply(rom):
    frames = {}                                    # (the frame each bell shows) -> its palette, tiles
    sites = []
    for site in HANGING:
        assert rom.u16(site) == 0x4EB9 and rom.u32(site + 2) == PARENT, hex(site)
        assert rom.u16(site - 20) == 0x3B7C and rom.u16(site - 16) == 8, hex(site)   # move.w #frame,8(a5)
        sites.append((site, rom.u16(site - 18)))
    shown = sorted({f for _, f in sites} | {TOP_FRAME})
    drawings = {}                                  # (tiles) -> {angle: (ox, oy, cells as tile numbers)}
    for f in shown:
        tiles, palette, mode = frame_tiles(rom, f)
        key = tuple(map(tuple, tiles))
        if key not in drawings:
            px = pixels(rom, tiles)
            drawings[key] = {}
            for a in ANGLES:
                ox, oy, cells = layout(art(rom, f, palette, px, a))
                drawings[key][a] = (ox, oy, {cr: rom.add_sprite_tile(cell, share=True,
                                                                     why="goal bell 0x%X turned %d" % (f, a))
                                             for cr, cell in cells.items()})
        frames[f] = (palette, key, mode)
    tilted = {}                                    # frame -> [frame at each of ANGLES]
    for f, (palette, key, mode) in frames.items():
        out = []
        for a in ANGLES:
            ox, oy, cells = drawings[key][a]
            body = bytearray([0, 0, mode, palette, 0, 0])         # (a blank 1 x 1 grid; the frame's own mode byte)
            for c in sorted({c for c, _ in cells}):
                rows = sorted(r for cc, r in cells if cc == c)
                top = rows[0]
                body += bytes([rows[-1] - top, ((ox + c * 16) // 2) & 0xFF, (-(oy + top * 16) // 2) & 0xFF, palette, 0])
                for r in range(top, rows[-1] + 1):
                    t = cells.get((c, r))
                    body += bytes([0]) if t is None else bytes([1, 0x20, t >> 8, t & 0xFF])
            body += b"\xff"
            at = rom.alloc(len(body))
            rom.data[at:at + len(body)] = body
            n = rom.next_frame
            rom.next_frame += 4
            rom.write(FRAME_TABLE + n, at.to_bytes(4, "big"), why="frame 0x%X -> goal bell 0x%X turned %d" % (n, f, a))
            out.append(n)
        tilted[f] = out

    table = lambda f: ",".join("0x%X" % x for x in tilted[f][:2] + [f] + tilted[f][2:])
    wrappers = "".join("""
hang%(k)d:
    jsr 0x%(parent)X
    movem.l %%d0-%%d5/%%a0-%%a3,-(%%sp)
    movea.l %%a0,%%a2                   | the hook: the segment
    moveq #0,%%d0                       | (its base: the segment's parent)
    move.b 0x4E(%%a0),%%d0
    lsl.w #7,%%d0
    lea 0x104000,%%a3
    adda.w %%d0,%%a3
    moveq #%(k)d,%%d5
    lea frames%(k)d(%%pc),%%a1
    bsr swing
    movem.l (%%sp)+,%%d0-%%d5/%%a0-%%a3
    tst.b 0x28(%%a0)
    rts
frames%(k)d:
    .word %(frames)s
""" % {"k": k, "parent": PARENT, "frames": table(f)} for k, (site, f) in enumerate(sites))
    top = tilted[TOP_FRAME]
    code = rom.place_code("""
    bra.w top
%(branches)s
top:                                    | (the swing's segments and the top bell: only the bell's frames)
    jsr 0x%(parent)X
    movem.l %%d0-%%d5/%%a0-%%a3,-(%%sp)
    move.w 8(%%a5),%%d0
    cmpi.w #0x%(top)X,%%d0
    beq 1f
    cmpi.w #0x%(first)X,%%d0
    bcs 9f
    cmpi.w #0x%(last)X,%%d0
    bhi 9f
1:  movea.l %%a5,%%a2                   | the hook: the bell itself; its base: its parent
    movea.l %%a0,%%a3
    moveq #6,%%d5
    lea frames_top(%%pc),%%a1
    bsr swing
9:  movem.l (%%sp)+,%%d0-%%d5/%%a0-%%a3
    tst.b 0x28(%%a0)
    rts
frames_top:
    .word %(top_frames)s
%(wrappers)s
| a bell's pendulum: a2 its hook, a3 the stalk's base, d5 the bell (0-6), a1 its 5 frames (-30, -15, as is, 15, 30)
swing:
    move.w 2(%%a2),%%d1
    sub.w 2(%%a3),%%d1                  | the hook's x against the base
    move.w %%d5,%%d0
    lsl.w #4,%%d0
    lea 0x%(state)X,%%a0
    adda.w %%d0,%%a0                    | a0: its state
    mulu #6,%%d5
    lea params(%%pc),%%a2
    adda.w %%d5,%%a2                    | a2: its pull, damping, push
    move.w 0x%(frame)X,%%d2
    subq.w #1,%%d2
    cmp.w (%%a0),%%d2
    beq 1f
    move.w %%d1,2(%%a0)                 | (just come into play: hanging still)
    clr.w 4(%%a0)
    clr.l 6(%%a0)
    clr.w 10(%%a0)
1:  move.w 0x%(frame)X,(%%a0)
    move.w %%d1,%%d2
    sub.w 2(%%a0),%%d2                  | the hook's speed
    move.w %%d1,2(%%a0)
    move.w %%d2,%%d3
    sub.w 4(%%a0),%%d3                  | its acceleration
    move.w %%d2,4(%%a0)
    cmpi.w #0x400,%%d3
    ble 2f
    move.w #0x400,%%d3
2:  cmpi.w #-0x400,%%d3
    bge 3f
    move.w #-0x400,%%d3
3:  move.w 8(%%a0),%%d4                 | the angle's speed:
    move.w 6(%%a0),%%d2
    muls (%%a2),%%d2
    asr.l #8,%%d2
    sub.w %%d2,%%d4                     | - pulled back to hanging
    move.w 8(%%a0),%%d2
    muls 2(%%a2),%%d2
    asr.l #8,%%d2
    sub.w %%d2,%%d4                     | - damped
    tst.w 10(%%a0)                      | (the push fades: FADE frames from the stalk's first move)
    bne 9f
    tst.w %%d3
    beq 10f
9:  cmpi.w #%(fade)d,10(%%a0)
    bcc 10f
    addq.w #1,10(%%a0)
    muls 4(%%a2),%%d3
    asr.l #8,%%d3
    move.w #%(fade)d,%%d2
    sub.w 10(%%a0),%%d2
    muls %%d2,%%d3
    divs #%(fade)d,%%d3
    sub.w %%d3,%%d4                     | - pushed the other way by the hook
10:
    move.w %%d4,8(%%a0)
    add.w 6(%%a0),%%d4                  | the angle (1/64 degree; + swung right)
    cmpi.w #3840,%%d4
    ble 4f
    move.w #3840,%%d4
4:  cmpi.w #-3840,%%d4
    bge 5f
    move.w #-3840,%%d4
5:  move.w %%d4,6(%%a0)
    moveq #0,%%d1                       | its drawing: swung right = turned anticlockwise (the first frames)
    move.w %%d4,%%d0
    bpl 6f
    neg.w %%d0
6:  cmpi.w #%(t15)d,%%d0
    bcs 7f
    addq.w #1,%%d1
    cmpi.w #%(t30)d,%%d0
    bcs 7f
    addq.w #1,%%d1
7:  tst.w %%d4
    bmi 8f
    neg.w %%d1
8:  addq.w #2,%%d1
    add.w %%d1,%%d1
    move.w (%%a1,%%d1.w),8(%%a5)
    rts
params:
    .word %(params)s
""" % {"branches": "".join("    bra.w hang%d\n" % k for k in range(len(sites))), "parent": PARENT,
       "top": TOP_FRAME, "first": min(top), "last": max(top), "top_frames": table(TOP_FRAME),
       "wrappers": wrappers, "state": STATE, "frame": FRAME, "t15": TILT_15 * 64, "fade": FADE, "t30": TILT_30 * 64,
       "params": ",".join("%d,%d,%d" % p for p in PARAMS)},
        why="goal bells: each a pendulum on its hook")
    for k, (site, f) in enumerate(sites):
        rom.write(site + 2, (code + 4 + 4 * k).to_bytes(4, "big"), expect=PARENT.to_bytes(4, "big"),
                  why="goal bell 0x%X: swings on its hook" % f)
    assert rom.u16(TOP_SITE) == 0x4EB9 and rom.u32(TOP_SITE + 2) == PARENT
    rom.write(TOP_SITE + 2, code.to_bytes(4, "big"), expect=PARENT.to_bytes(4, "big"),
              why="the top goal bell: swings on its hook")
