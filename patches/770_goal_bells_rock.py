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
# just after it's placed, TOP_PLACE - and before the stalk's touched, TOP_REST in its own routine - itself the hook,
# on the stalk's base; drawn as plain grids, its place shifted to match each one - plain ones, one high byte and a byte a tile: the stalk's drawer reads no more (drawn in
# pieces, as the hanging ones are, it came apart). Each bell's state (STATE, 16 bytes: the frame
# it was last updated - another means it's just come into play, and it starts hanging still - the hook's last x and
# speed, the angle and its speed: 1/64 degree, the frames since the stalk first moved, its clapper) is spare RAM. The
# stalk's push fades over FADE frames from its first move, so each swing of the bells is smaller and they settle.
# Each hanging bell has a clapper: an object of its own (made when the bell first swings) drawn behind it in brass
# (CLAPPER_PALETTE), hung at the bell's HANG point - turned with the bell's drawing - and a pendulum of its own
# driven by that point, so it lags the bell and swings across the mouth, knocking the sides (CLAPPER_ROOM: it
# bounces back), one step behind its bell (+0x28: the bell's body hides all but what drops below the rim). The bell
# places it each frame (the hanging ones' own place: their segment's, less their routine's offsets - read from the
# routine; the top one's as it's placed), so the two move together.
# The drawings are the bells' own art (3 shapes: the top one, and the left- and right-hooked hanging ones - each
# frame the shape in its own palette) turned about their top (the hook, or the top bell's knob) by RotSprite
# (Scale2x three times, turned, each pixel's centre sampled) - or, once painted, ART's pictures (each shape's in
# its first frame's colours, ART_COLOURS; DRAWN: the build writes them from RotSprite, and reads them as painted
# once it's False) - then laid on the tile grid where they need the fewest tiles (an even offset: pieces are
# placed in 2 px steps). A frame is a blank 1 x 1 grid and a piece per column of tiles - the same number of pieces in
# every drawing of a bell, hanging still too (its own tiles, a frame of its own), padded with blank ones: a sprite
# dropped from one frame to the next lingers (the top bell's knob came adrift). The bells hanging still are
# their own art - or UPRIGHT's pictures where they've been painted over (their 32 x 32: the rest stays clear).
PARENT = 0x5E036               # a0 = the object's parent (+0x4E); tst.b 0x28(a0)
HANGING = [0x52B52, 0x52B80, 0x52BAE, 0x52BDC, 0x52C0A, 0x52C38]
TOP_FRAME = 0x20D0
TOP_PLACE = 0x52A48            # (in SWINGING, 0x52A0C: jsr <placed from its parent> - goal-bend's)
TOP_REST = 0x528E6             # (its routine before the stalk's touched, 0x528D8: jsr <placed from its parent>)
TOP_PRIORITY = 0x81            # (+0x28 - was 0x7F, the hanging bells', in front of Blue, 0x80: the game writes sprites
                               # back to front, and at the goal it's late - the top bell's, at the screen's top, came
                               # after the beam had drawn its top rows and they showed the last frame's drawing: torn)
ANGLES = [-30, -15, 15, 30]    # (degrees: the drawings; 0 is the bell as it is)
TILT_15, TILT_30 = 8, 22       # (degrees swung: the drawing past each)
PARAMS = [(10, 15, 147), (13, 15, 230), (12, 15, 360), (12, 15, 147), (11, 15, 230), (14, 15, 360), (9, 15, 110)]
                               # (each bell, HANGING's order then the top one: its pull back to hanging, its damping,
                               # its push from the hook's acceleration - /256 a frame. Higher bells' hooks move more:
                               # the lower ones get more push)
FADE = 200                     # (frames: the stalk's push on the bells fades to nothing over them - each swing smaller)
STATE = 0x10E860               # 7 x 16 bytes (spare RAM, to 0x10E8CF)
NEW_OBJECT = 0xFFEC            # -> a1 (ne: none free)
CLAPPER = [".....111.....",    # (the clapper as drawn, its top at its hang point: 1 outline, 2 body, 3 highlight)
           ".....121.....",
           ".....121.....",
           ".....121.....",
           "....11211....",
           "...1233221...",
           "...1232221...",
           "...1222221...",
           "....11111...."]
CLAPPER_X = 6                  # (the drawing's middle column: under the hang point)
HANG = (15, 24)                # (the upright bell's hang point, px in its frame: the clapper's top - its ball
                               # then shows in the mouth's notch)
CLAPPER_PALETTE = 0x7E         # (empty in play: the title's; pause-menu borrows it and puts it back)
CLAPPER_COLOURS = [(96, 56, 8), (214, 160, 40), (255, 232, 128)]   # brass: outline, body, highlight
CLAPPER_PARAMS = (30, 10, 420) # (its pull back to hanging, damping, push - as PARAMS: a short, quick pendulum)
CLAPPER_ROOM = 18              # (degrees it can swing from the bell's middle before it knocks the side and bounces)
CLAPPER_SPAN = 12              # (px from the hang point to the ball: how far a swing moves it)
FRAME = 0x100206               # (a word counted each frame)
FRAME_TABLE = 0x60772
ART = "art/goal_bells/bell_%04X_%+d.png"   # (a shape's first frame, the angle) - 64 x 56: the frame's (0, 0) at (16, 8)
ART_ORIGIN = (16, 8)
UPRIGHT = "art/goal_bells/upright_%04X.png"   # (a shape's first frame) - the bell hanging still, as ART: painted
                                             # over, its own tiles (only the bells use them) are redrawn in place
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


def upright(rom, frame, palette, tiles):
    """The bell hanging still: its own art, or UPRIGHT's picture painted over it - its tiles redrawn to match."""
    import os
    from png_tiles import neo_to_rgb, read_indices
    px = pixels(rom, tiles)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, UPRIGHT % frame)
    if not os.path.exists(path):
        return px
    colours = [neo_to_rgb(int(w, 16)) for w in ART_COLOURS[palette].split()]
    rows = read_indices(path, colours)
    ox, oy = ART_ORIGIN
    assert not any(v for y, row in enumerate(rows) for x, v in enumerate(row)
                   if v and not (ox <= x < ox + 32 and oy <= y < oy + 32)), \
        "goal bells: %s - the bell hanging still has only its 32 x 32 (its own tiles)" % UPRIGHT % frame
    new = [[rows[oy + y][ox + x] for x in range(32)] for y in range(32)]
    for r in range(2):
        for c in range(2):
            cell = [row[c * 16:c * 16 + 16] for row in new[r * 16:r * 16 + 16]]
            if cell != rom.sprite_tile(tiles[r][c]):
                rom.redraw_sprite_tile(tiles[r][c], cell, why="goal bell 0x%X hanging still, as painted" % frame)
    return new


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
    shown = sorted({f for _, f in sites}) + [TOP_FRAME]   # (the top bell's last: its tiles all from the placeholders')
    drawings = {}                                  # (tiles) -> {angle: (ox, oy, cells as tile numbers)}
    pivots = {}                                    # (tiles) -> the shape's top: what its drawings turn about
    for f in shown:
        tiles, palette, mode = frame_tiles(rom, f)
        key = tuple(map(tuple, tiles))
        if key not in drawings:
            px = upright(rom, f, palette, tiles)
            pivots[key] = next((sum(xs) / len(xs), y) for y in range(32) for xs in [[x for x in range(32) if px[y][x]]] if xs)
            drawings[key] = {}
            for a in ANGLES:
                ox, oy, cells = layout(art(rom, f, palette, px, a))
                drawings[key][a] = (ox, oy, {cr: rom.add_sprite_tile(cell, share=True,
                                                                     why="goal bell 0x%X turned %d" % (f, a))
                                             for cr, cell in cells.items()})
        frames[f] = (palette, key, mode)
    tilted = {}                                    # frame -> [frame at -30, -15, as is, 15, 30]
    shift = {}                                     # the top bell's frames -> its place's shift (x, y: 1/128 px)
    for f, (palette, key, mode) in frames.items():
        out = []
        if f == TOP_FRAME:                         # (a plain grid, its place shifted: see TOP_PLACE)
            span_c = max(max(c for c, _ in drawings[key][a][2]) - min(c for c, _ in drawings[key][a][2]) for a in ANGLES) + 1
            span_r = max(max(r for _, r in drawings[key][a][2]) - min(r for _, r in drawings[key][a][2]) for a in ANGLES) + 1
        for a in ANGLES:
            ox, oy, cells = drawings[key][a]
            if f == TOP_FRAME:
                c0, r0 = min(c for c, _ in cells), min(r for _, r in cells)
                his = {t >> 8 for t in cells.values()}
                assert len(his) == 1 and all(t & 0xFF > 1 for t in cells.values()), \
                    "goal bells: the top bell's drawing needs its tiles in one 256 (its drawer reads plain bytes)"
                body = bytearray([span_c - 1, span_r - 1, mode, palette, his.pop()])
                for c in range(c0, c0 + span_c):
                    for r in range(r0, r0 + span_r):
                        t = cells.get((c, r))
                        body += bytes([0 if t is None else t & 0xFF])
            else:
                body = bytearray([0, 0, mode, palette, 0, 0])     # (a blank 1 x 1 grid; the frame's own mode byte)
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
            if f == TOP_FRAME:
                shift[n] = ((ox + c0 * 16) * 128, (oy + r0 * 16) * 128)
        if f == TOP_FRAME:                         # (hanging still: its own tiles in a grid as big as the rest's - a
            tiles = frame_tiles(rom, f)[0]         # column dropped from one frame to the next lingers on screen)
            body = bytearray([span_c - 1, span_r - 1, mode, palette, tiles[0][0] >> 8])
            for c in range(span_c):
                for r in range(span_r):
                    body += bytes([tiles[r][c] & 0xFF if r < 2 and c < 2 else 0])
            body += b"\xff"
            at = rom.alloc(len(body))
            rom.data[at:at + len(body)] = body
            still = rom.next_frame
            rom.next_frame += 4
            rom.write(FRAME_TABLE + still, at.to_bytes(4, "big"), why="frame 0x%X -> the top goal bell hanging still" % still)
            shift[still] = (0, 0)
            out = out[:2] + [still] + out[2:]
        else:
            out = out[:2] + [f] + out[2:]
        tilted[f] = out

    table = lambda f: ",".join("0x%X" % x for x in tilted[f])
    from png_tiles import rgb_to_neo
    clap_px = [[0] * 16 for _ in range(16)]
    for y, row in enumerate(CLAPPER):
        for x, ch in enumerate(row):
            if ch != ".":
                clap_px[y][x + 8 - CLAPPER_X] = int(ch)
    clap_frame = rom.add_frame([[rom.add_sprite_tile(clap_px, why="goal bells: the clapper")]], CLAPPER_PALETTE,
                               why="goal bells: the clapper")
    def clap_table(site, f):
        """The bell's routine's y, x offsets (subi.w #y,0(a5) ; subi.w #x / addi.w #-x,2(a5)), then its hang point
        (x, y: 1/128 px - y down the frame) at each drawing: -30, -15, as is, 15, 30."""
        if site is None:                                                   # (the top bell: placed as it is)
            out = [0, 0]
        else:
            assert rom.u16(site + 12) == 0x046D and rom.u16(site + 16) == 0 and rom.u16(site + 18) in (0x046D, 0x066D) \
                and rom.u16(site + 22) == 2, hex(site)                    # (subi / addi.w #x,2(a5))
            x = rom.u16(site + 20)
            out = [rom.u16(site + 14), x if rom.u16(site + 18) == 0x046D else (-x) & 0xFFFF]
        pv = pivots[frames[f][1]]
        for a in ANGLES[:2] + [0] + ANGLES[2:]:
            r = math.radians(a)
            dx, dy = HANG[0] - pv[0], HANG[1] - pv[1]
            hx = pv[0] + math.cos(r) * dx - math.sin(r) * dy
            hy = pv[1] + math.sin(r) * dx + math.cos(r) * dy
            out += [int(round(hx * 128)) & 0xFFFF, int(round(hy * 128)) & 0xFFFF]
        return ",".join("0x%X" % v for v in out)
    wrappers = "".join("""
hang%(k)d:
    jsr 0x%(parent)X
    movem.l %%d0-%%d7/%%a0-%%a4,-(%%sp)
    movea.l %%a0,%%a2                   | the hook: the segment
    movea.l %%a0,%%a4
    moveq #0,%%d0                       | (its base: the segment's parent)
    move.b 0x4E(%%a0),%%d0
    lsl.w #7,%%d0
    lea 0x104000,%%a3
    adda.w %%d0,%%a3
    moveq #%(k)d,%%d5
    lea frames%(k)d(%%pc),%%a1
    bsr swing
    lea clap%(k)d(%%pc),%%a1
    bsr clapper
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a4
    tst.b 0x28(%%a0)
    rts
frames%(k)d:
    .word %(frames)s
clap%(k)d:
    .word %(clap)s
""" % {"k": k, "parent": PARENT, "frames": table(f), "clap": clap_table(site, f)} for k, (site, f) in enumerate(sites))
    top = tilted[TOP_FRAME]
    code = rom.place_code("""
    bra.w top
%(branches)s
    bra.w top_rest
top:                                    | (the swing's segments and the top bell, placed: only the bell's frames)
    jsr 0x%(place)X                     | (what the jsr was: goal-bend's placing)
    bra.s top_placed
top_rest:                               | (the top bell before the stalk's touched: its own routine's placing)
    jsr 0x%(rest_place)X
top_placed:
    movem.l %%d0-%%d7/%%a0-%%a4,-(%%sp)
    move.w 8(%%a5),%%d0
    cmpi.w #0x%(top)X,%%d0
    beq 1f
    cmpi.w #0x%(first)X,%%d0
    bcs 9f
    cmpi.w #0x%(last)X,%%d0
    bhi 9f
1:  move.b #0x%(top_pri)X,0x28(%%a5)     | (behind Blue: its sprite's then written before the screen's top is drawn)
    movea.l %%a5,%%a2                   | the hook: the bell as placed; its base: its parent
    moveq #0,%%d0
    move.b 0x4E(%%a5),%%d0
    lsl.w #7,%%d0
    lea 0x104000,%%a3
    adda.w %%d0,%%a3
    moveq #6,%%d5
    lea frames_top(%%pc),%%a1
    bsr swing
    movea.l %%a5,%%a4                   | its clapper (placed from where it was put, before the shift)
    lea clap_top(%%pc),%%a1
    bsr clapper
    lea shifts_top(%%pc),%%a1           | its drawing's shift
    add.w %%d1,%%d1
    move.w 0(%%a1,%%d1.w),%%d0
    add.w %%d0,2(%%a5)
    move.w 2(%%a1,%%d1.w),%%d0
    sub.w %%d0,(%%a5)
9:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a4
    rts
shifts_top:
    .word %(shifts)s
clap_top:
    .word %(clap_top)s
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

| a hanging bell's clapper: a5 the bell, a4 its segment, a3 the stalk's base, a0 its state, d1 its drawing (x2: -30,
| -15, as is, 15, 30), d4 its angle, a1 its table (the routine's y, x offsets; the hang point at each drawing: x, y)
clapper:
    movea.l 12(%%a0),%%a2
    move.l %%a2,%%d0
    beq 1f
    cmpi.l #clapper_object,4(%%a2)
    bne 1f
    cmpa.l 0x58(%%a2),%%a5
    beq 2f
1:  movem.l %%d1/%%d4/%%a0-%%a1,-(%%sp)  | a new one
    jsr 0x%(new)X
    movea.l %%a1,%%a2
    movem.l (%%sp)+,%%d1/%%d4/%%a0-%%a1
    bne 9f
    move.l #clapper_object,4(%%a2)
    move.l %%a5,0x58(%%a2)
    move.w #0x%(clap_frame)X,8(%%a2)
    move.b #0x%(clap_pal)X,0x20(%%a2)
    move.b 0x28(%%a5),%%d0              | (one behind its bell)
    addq.b #1,%%d0
    move.b %%d0,0x28(%%a2)
    clr.l 0x50(%%a2)
    clr.w 0x5C(%%a2)
    move.l %%a2,12(%%a0)
2:  move.w (%%a4),%%d2                  | the bell's place: its segment's, less its routine's offsets
    sub.w (%%a1),%%d2
    move.w 2(%%a4),%%d3
    sub.w 2(%%a1),%%d3
    move.w %%d1,%%d0                    | the hang point, at this drawing
    add.w %%d0,%%d0
    add.w 4(%%a1,%%d0.w),%%d3
    sub.w 6(%%a1,%%d0.w),%%d2
    move.w %%d3,%%d5                    | its pendulum: driven by the point's x against the base
    sub.w 2(%%a3),%%d5
    tst.w 0x5C(%%a2)
    bne 3f
    move.w %%d5,0x54(%%a2)
    clr.w 0x56(%%a2)
    move.w #1,0x5C(%%a2)
3:  move.w %%d5,%%d6
    sub.w 0x54(%%a2),%%d6
    move.w %%d5,0x54(%%a2)
    move.w %%d6,%%d7
    sub.w 0x56(%%a2),%%d7
    move.w %%d6,0x56(%%a2)
    cmpi.w #0x400,%%d7
    ble 4f
    move.w #0x400,%%d7
4:  cmpi.w #-0x400,%%d7
    bge 5f
    move.w #-0x400,%%d7
5:  move.w 0x52(%%a2),%%d6              | its speed: pulled back, damped, pushed
    move.w 0x50(%%a2),%%d0
    muls #%(cw)d,%%d0
    asr.l #8,%%d0
    sub.w %%d0,%%d6
    move.w 0x52(%%a2),%%d0
    muls #%(cc)d,%%d0
    asr.l #8,%%d0
    sub.w %%d0,%%d6
    muls #%(cg)d,%%d7
    asr.l #8,%%d7
    sub.w %%d7,%%d6
    move.w %%d6,0x52(%%a2)
    add.w 0x50(%%a2),%%d6               | its angle
    move.w %%d6,%%d0                    | (against the bell's sides: it bounces back)
    sub.w %%d4,%%d0
    cmpi.w #%(room)d,%%d0
    ble 6f
    move.w %%d4,%%d6
    addi.w #%(room)d,%%d6
    bra 7f
6:  cmpi.w #-%(room)d,%%d0
    bge 8f
    move.w %%d4,%%d6
    subi.w #%(room)d,%%d6
7:  move.w 0x52(%%a2),%%d0
    asr.w #1,%%d0
    neg.w %%d0
    move.w %%d0,0x52(%%a2)
8:  move.w %%d6,0x50(%%a2)
    muls #%(span)d,%%d6                 | its place: under the hang point, swung across
    asr.l #8,%%d6
    add.w %%d6,%%d3
    subi.w #%(cx)d,%%d3
    move.w %%d2,(%%a2)
    move.w %%d3,2(%%a2)
9:  rts

clapper_object:                         | (each frame: its colours; gone with its bell)
    movea.l 0x58(%%a5),%%a0
    tst.b 0x28(%%a0)
    beq 1f
    move.w 8(%%a0),%%d0
    cmpi.w #0x%(bell_first)X,%%d0
    bcs 1f
    cmpi.w #0x%(bell_last)X,%%d0
    bls 2f
    cmpi.w #0x%(first_all)X,%%d0
    bcs 1f
    cmpi.w #0x%(last_all)X,%%d0
    bhi 1f
2:  lea 0x%(pal_ram)X,%%a0
    move.w #0x%(c1)04X,(%%a0)+
    move.w #0x%(c2)04X,(%%a0)+
    move.w #0x%(c3)04X,(%%a0)+
    rts
1:  clr.b 0x28(%%a5)
    rts
""" % {"branches": "".join("    bra.w hang%d\n" % k for k in range(len(sites))), "parent": PARENT,
       "top": TOP_FRAME, "first": min(top), "last": max(top), "top_frames": table(TOP_FRAME),
       "place": rom.u32(TOP_PLACE + 2), "top_pri": TOP_PRIORITY, "rest_place": rom.u32(TOP_REST + 2), "clap_top": clap_table(None, TOP_FRAME), "shifts": ",".join("0x%X,0x%X" % (shift[x][0] & 0xFFFF, shift[x][1] & 0xFFFF) for x in tilted[TOP_FRAME]),
       "wrappers": wrappers, "state": STATE, "frame": FRAME, "t15": TILT_15 * 64, "fade": FADE, "t30": TILT_30 * 64,
       "params": ",".join("%d,%d,%d" % p for p in PARAMS), "new": NEW_OBJECT, "clap_frame": clap_frame,
       "clap_pal": CLAPPER_PALETTE, "cw": CLAPPER_PARAMS[0], "cc": CLAPPER_PARAMS[1],
       "cg": CLAPPER_PARAMS[2], "room": CLAPPER_ROOM * 64,
       "span": int(round(CLAPPER_SPAN * 128 * math.pi / 180 / 64 * 256)), "cx": CLAPPER_X * 128,
       "bell_first": 0x20D0, "bell_last": 0x20E8, "first_all": min(min(v) for v in tilted.values()),
       "last_all": max(max(v) for v in tilted.values()), "pal_ram": 0x400000 + CLAPPER_PALETTE * 32 + 2,
       "c1": rgb_to_neo(CLAPPER_COLOURS[0]), "c2": rgb_to_neo(CLAPPER_COLOURS[1]), "c3": rgb_to_neo(CLAPPER_COLOURS[2])},
        why="goal bells: each a pendulum on its hook")
    for k, (site, f) in enumerate(sites):
        rom.write(site + 2, (code + 4 + 4 * k).to_bytes(4, "big"), expect=PARENT.to_bytes(4, "big"),
                  why="goal bell 0x%X: swings on its hook" % f)
    assert rom.u16(TOP_REST) == 0x4EB9
    rom.write(TOP_REST + 2, (code + 4 + 4 * len(sites)).to_bytes(4, "big"), expect=rom.u32(TOP_REST + 2).to_bytes(4, "big"),
              why="the top goal bell, before the stalk's touched: its clapper, its place")
    assert rom.u16(TOP_PLACE) == 0x4EB9
    rom.write(TOP_PLACE + 2, code.to_bytes(4, "big"), expect=rom.u32(TOP_PLACE + 2).to_bytes(4, "big"),
              why="the top goal bell: swings on its hook")
