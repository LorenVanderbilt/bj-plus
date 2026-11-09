NAME = "wheel-reflection"
DESCRIPTION = "Empire Marsh 1's half-sunken Ferris wheels reflected in the water (AES set only)"

import math
from collections import Counter

# The two Ferris wheels stand in the lake, their hubs on the waterline, but below it the water was plain: the wheel
# looked stuck on rather than standing in it (the user, 2026-11-08, with a mock-up). Now the water under each wheel
# shows it upside down, tinted towards the water.
#
# The wheels' rims and spokes are cells of the front layer's map (MAP_TABLE, blocks BLOCKS; the format is in
# tools/hackbuild.py, Rom.map_quarter), so the reflection is too: the water's three rows (WATER_ROWS) below a wheel
# get new tiles, each the cell the same distance above the waterline (mirror row = MIRROR - row), flipped and
# blended with the water under it. The game then draws them as it scrolls, like any other cell. The cells keep the
# water's attribute word: its palette, its collision type (bits 4-7: the front layer is Blue's collision map) and its
# 4-frame animation (bit 2), so each reflection is 4 tiles, one over each of the water's frames, and ripples with it.
# The surface row keeps the water's top SURFACE_EDGE pixel rows, the waterline's dark edge.
#
# The ripple is in those 4 frames too: the reflection's bands of RIPPLE_LINES lines are shifted sideways by up to
# RIPPLE_PX pixels, a wave RIPPLE_BANDS bands long moving down a quarter wave a frame, so the hardware's animation
# plays it. Shifted pixels can spill into the water cells either side of a wheel, which get tiles of their own.
#
# The hub's cone is an object drawn over the cells CONE (on the same 16 px grid, at the same place on both wheels),
# so their reflections are drawn with the cone on top.
#
# The gondolas are objects that move round, so their reflections are in their frames: one for each height of the
# gondola's bottom above the waterline (HEIGHTS), chosen just before it's drawn (GONDOLA_DRAW). Each frame is the
# gondola cut off at the waterline (its rows below it left out) and its reflection below, as extra one-column
# sprites ("pieces") in the water's palette, with the same ripple. Each new frame gets the gondola's hitbox
# (HITBOXES is looked up by frame number), or Blue falls through it. The gondolas used to go under behind a 4 x 3
# tile patch of water (a scenery object, kind PATCH_KIND), which would now cover their reflections: it does nothing.
#
# Colours: the reflection's pixels are blended (BLEND of the way to the water's pixel under them, then DARKEN) and
# fitted to the water's palette (0x8F, shared by stages 8-10, in the bank at PALETTE_BANK): its water colours, plus
# six new ones in entries 2-7, black and unused till now (only the water's tiles draw in 0x8F, with 1 and 8-15).
#
# The new tiles are in the AES set's added sprite space: the MVS set shows those cells blank.
MAP_TABLE = 0x878E4             # Empire Marsh 1's front layer
BLOCKS = (6, 7, 8)              # the wheels: block 6 col 3 - block 7 col 0, block 7 col 7 - block 8 col 4
WATER_ROWS, MIRROR = (13, 14, 15), 25
WATER_TILES = range(0x2E0, 0x2F0)
WHEEL_TILES = range(0x4C80, 0x4D00)
WATER_PALETTE, WHEEL_PALETTES, CONE_PALETTE = 0x8F, (0xF9, 0xFA), 0xFB
CONE = {0x4CAD: 0x4C80, 0x4CAE: 0x4C81, 0x4CAF: 0x4C82, 0x4CE8: 0x4C88,     # map cell under it: the cone's tile
        0x4CB5: 0x4CB8, 0x4CB6: 0x4CB9, 0x4CB7: 0x4CBA, 0x4CF0: 0x4CBB}
PALETTE_BANK = 0x7000           # stages 8-10's palettes 0-0xFF, 32 bytes each
NEW_ENTRIES = range(2, 8)
SURFACE_EDGE = 2
BLEND, DARKEN = 0.5, 0.85
RIPPLE_LINES, RIPPLE_PX, RIPPLE_BANDS = 2, 2, 8
STAGE_AT, STAGE = 0x103005, 8
OBJECT_LISTS = 0x60502          # stage * 16: +0 counts (a byte a block), +4 the blocks' lists (see marsh2-step)
KINDS = 0x5F4D8                 # object kind * 4: flags (top byte) and code
PATCH_KIND, PATCH_CODE = 0x3C4, 0x31762
GONDOLA_DRAW = 0x31692          # jsr 0x1A49A: a gondola draws its frame (+8), unless it's under water
DRAW = 0x1A49A
HITBOXES = 0x64772              # frame number -> its hitbox (0x5E078): what Blue stands on and is hit by
GONDOLA_FRAMES = (0x2460, 0x2464)   # the two colours (the spawner gives every other gondola the second)
GONDOLA_PALETTES = (0xF7, 0xF8)
GONDOLA = [[(0x4CBC, 0), (0x4CBD, 0), (0x4CBE, 0)],    # its tiles (tile, flips): 3 x 2, as in both frames
           [(0x4CBF, 0), (0x4C90, 0), (0x4CBF, 1)]]
HEIGHTS = list(range(-32, 0)) + list(range(0, 48, 2))
                                # the gondola's bottom above the waterline, px: a frame for each (every pixel while
                                # the waterline cuts it, so it's cut at the right row; every other above the water)
DEPTH = 16 * len(WATER_ROWS)    # the water's depth, px: reflections end there


def colours(rom, palette):
    from png_tiles import neo_to_rgb
    return [neo_to_rgb(rom.u16(PALETTE_BANK + palette * 32 + 2 * i)) for i in range(16)]


def apply(rom):
    from png_tiles import rgb_to_neo, neo_to_rgb
    water = colours(rom, WATER_PALETTE)
    wheel = {p: colours(rom, p) for p in WHEEL_PALETTES + (CONE_PALETTE,)}
    for i in NEW_ENTRIES:
        assert rom.u16(PALETTE_BANK + WATER_PALETTE * 32 + 2 * i) == 0x8000, "wheel-reflection: palette 0x8F changed"
    grids = {b: rom.map_block(MAP_TABLE, b) for b in BLOCKS}

    # the reflection's rows, across the blocks: each mirrored cell flipped, as colours (None = clear)
    width = 256 * len(BLOCKS)
    mirrored = {}
    for r in WATER_ROWS:
        lines = [[None] * width for _ in range(16)]
        for k, b in enumerate(BLOCKS):
            for c in range(16):
                sattr, src = grids[b][MIRROR - r][c]
                if src not in WHEEL_TILES:
                    continue
                assert sattr >> 8 in WHEEL_PALETTES and sattr & 0x0F == 0, "wheel-reflection: unexpected cell"
                px = [[wheel[sattr >> 8][v] if v else None for v in row] for row in rom.sprite_tile(src)]
                if src in CONE:
                    for y, row in enumerate(rom.sprite_tile(CONE[src])):
                        for x, v in enumerate(row):
                            if v:
                                px[y][x] = wheel[CONE_PALETTE][v]
                for y in range(16):
                    lines[15 - y][16 * (16 * k + c):16 * (16 * k + c) + 16] = px[y]
        mirrored[r] = lines

    def shift(r, y, f):
        """The ripple: band (y // RIPPLE_LINES, counted from the waterline)'s sideways shift in frame f."""
        band = ((r - WATER_ROWS[0]) * 16 + y) // RIPPLE_LINES
        return round(RIPPLE_PX * math.sin(2 * math.pi * (band / RIPPLE_BANDS - f / 4)))

    # each reflection cell: its 4 frames as pixels, either a water index or a colour to fit to the palette
    cells = {}
    for k, b in enumerate(BLOCKS):
        for r in WATER_ROWS:
            for c in range(16):
                attr, tile = grids[b][r][c]
                if attr >> 8 != WATER_PALETTE or tile not in WATER_TILES:
                    continue
                frames, any_shown = [], False
                for f in range(4):
                    under = rom.sprite_tile((tile & ~3) + f)
                    out = []
                    for y in range(16):
                        line, s = [], shift(r, y, f)
                        for x in range(16):
                            w, gx = under[y][x], 16 * (16 * k + c) + x - s
                            p = mirrored[r][y][gx] if 0 <= gx < width else None
                            if p is None or (r == WATER_ROWS[0] and y < SURFACE_EDGE):
                                line.append(w)
                            else:
                                line.append(tuple(min(255, (a + (b2 - a) * BLEND) * DARKEN)
                                                  for a, b2 in zip(p, water[w])))
                                any_shown = True
                        out.append(line)
                    frames.append(out)
                if any_shown:
                    cells[(b, r, c)] = frames

    # the gondolas' frames at each height: the gondola clipped at the waterline, and its reflection, 3 columns of
    # 2 tiles from REFLECTED_TOP, as 4 frames of colours (None = clear), each column a piece
    art = []
    for row in GONDOLA:
        art.append([])
        for t, flips in row:
            px = rom.sprite_tile(t)
            art[-1].append([[px[y][15 - x if flips & 1 else x] for x in range(16)] for y in range(16)])
    gondola_px = [[art[y // 16][x // 16][y % 16][x % 16] for x in range(48)] for y in range(32)]
    under = {d: rom.sprite_tile(WATER_TILES[0] if d < 16 else WATER_TILES[8])[d % 16] for d in range(DEPTH)}
    average = {d: tuple(sum(water[v][j] for v in under[d]) / 16 for j in range(3)) for d in range(DEPTH)}
    reflected = {}                   # (palette, height) -> [column][frame] 32 x 16 colours
    for pal in GONDOLA_PALETTES:
        cols = colours(rom, pal)
        for o in HEIGHTS:
            pieces = [[[[None] * 16 for _ in range(32)] for _ in range(4)] for _ in range(3)]
            for f in range(4):
                for i in range(32):                  # the reflection's row i is the gondola's row 31 - i, at depth o + i
                    d = o + i
                    if not SURFACE_EDGE <= d < DEPTH:
                        continue
                    s_ = round(RIPPLE_PX * math.sin(2 * math.pi * (d // RIPPLE_LINES / RIPPLE_BANDS - f / 4)))
                    for x in range(48):
                        sx = x - s_
                        v = gondola_px[31 - i][sx] if 0 <= sx < 48 else 0
                        if v:
                            pieces[x // 16][f][i][x % 16] = tuple(
                                min(255, (a + (b2 - a) * BLEND) * DARKEN) for a, b2 in zip(cols[v], average[d]))
            reflected[pal, o] = pieces

    # six new colours: the reflection's colours clustered, the water's own colours staying as they are
    fixed = [(i, water[i]) for i in range(1, 16) if i not in NEW_ENTRIES]
    samples = Counter(v for fr in cells.values() for f in fr for row in f for v in row if isinstance(v, tuple))
    samples.update(v for p in reflected.values() for col in p for f in col for row in f for v in row if v)
    d2 = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b))
    free = []
    for _ in NEW_ENTRIES:            # start from the samples furthest from every colour so far
        free.append(max(samples, key=lambda s: min(d2(s, c) for c in [c for _, c in fixed] + free)))
    for _ in range(20):
        sums = [[0, 0, 0, 0] for _ in free]
        for s, n in samples.items():
            k = min(range(len(free) + len(fixed)), key=lambda k: d2(s, (free + [c for _, c in fixed])[k]))
            if k < len(free):
                for j in range(3):
                    sums[k][j] += s[j] * n
                sums[k][3] += n
        free = [tuple(t[j] / t[3] for j in range(3)) if t[3] else f for f, t in zip(free, sums)]
    words = [rgb_to_neo(tuple(int(v + 0.5) for v in f)) for f in free]
    rom.write(PALETTE_BANK + WATER_PALETTE * 32 + 2 * NEW_ENTRIES[0], b"".join(w.to_bytes(2, "big") for w in words),
              expect=b"\x80\x00" * len(NEW_ENTRIES), why="wheel-reflection: the reflection's colours in palette 0x8F")
    palette = dict(fixed + [(i, neo_to_rgb(w)) for i, w in zip(NEW_ENTRIES, words)])
    fit = {}

    def index(v):
        if not isinstance(v, tuple):
            return v
        if v not in fit:
            fit[v] = min(palette, key=lambda i: d2(v, palette[i]))
        return fit[v]

    # the tiles (shared where two cells come out the same), then the map
    made = {}
    for (b, r, c), frames in sorted(cells.items()):
        tiles = [[[index(v) for v in row] for row in f] for f in frames]
        key = bytes(v for f in tiles for row in f for v in row)
        if key not in made:
            made[key] = rom.add_aes_tile_run(tiles, why="wheel-reflection: under map cell %04X" %
                                                       grids[b][MIRROR - r][c][1])
        attr, tile = grids[b][r][c]
        grids[b][r][c] = (attr, made[key] | (tile & 3))
    for b, g in grids.items():
        for q in range(4):
            oy, ox = (8 if q & 1 else 0), (8 if q & 2 else 0)
            new = [g[oy + i // 8][ox + i % 8] for i in range(64)]
            if rom.map_quarter(rom.u32(MAP_TABLE + 16 * b + 4 * q)) != new:
                rom.put_map_quarter(MAP_TABLE, b, q, new, why="wheel-reflection: block %d quarter %d" % (b, q))

    # the gondolas' frames: per height, the gondola's tile rows above the water as they were, the one the waterline
    # crosses clipped (a new tile), the ones below left out; then the reflection's columns as pieces (palette 0x8F,
    # animated), from the reflection's top (2 x height + 32 px below the gondola's top: up = -(height + 16))
    def entry(t, attr):
        return bytes([1, 0x20 | attr, t >> 8, t & 0xFF]) if t is not None else b"\0"
    clipped, runs, tables = {}, {}, []
    for pal, base in zip(GONDOLA_PALETTES, GONDOLA_FRAMES):
        table = []
        for o in HEIGHTS:
            body = bytearray([2, 1, 0, pal, GONDOLA[0][0][0] >> 8])
            for c in range(3):
                for r in range(2):
                    t, flips = GONDOLA[r][c]
                    keep = 32 + o - 16 * r           # the tile's rows above the waterline
                    if keep <= 0:
                        body += entry(None, 0)
                    elif keep >= 16:
                        body += entry(t, flips)
                    else:
                        px = [[gondola_px[16 * r + y][16 * c + x] if y < keep else 0 for x in range(16)]
                              for y in range(16)]
                        key = bytes(v for row in px for v in row)
                        if key not in clipped:
                            clipped[key] = rom.add_aes_tile_run([px], why="wheel-reflection: a gondola at the "
                                                                          "waterline")
                        body += entry(clipped[key], 0)
            for c, frames in enumerate(reflected[pal, o]):
                tiles = []
                for r in range(2):
                    run = [[[index(v) or 0 for v in row] for row in f[16 * r:16 * r + 16]] for f in frames]
                    if not any(v for f in run for row in f for v in row):
                        tiles.append(None)
                        continue
                    key = bytes(v for f in run for row in f for v in row)
                    if key not in runs:
                        runs[key] = rom.add_aes_tile_run(run, why="wheel-reflection: a gondola's reflection")
                    tiles.append(runs[key])
                up = -(o + 16)
                while tiles and tiles[0] is None:
                    tiles, up = tiles[1:], up - 8
                while tiles and tiles[-1] is None:
                    tiles = tiles[:-1]
                if tiles:
                    body += bytes([len(tiles) - 1, 8 * c & 0xFF, up & 0xFF, WATER_PALETTE, tiles[0] >> 8])
                    body += b"".join(entry(t, 4) for t in tiles)
            body.append(0xFF)
            n = rom.add_frame_body(bytes(body), why="wheel-reflection: gondola %02X, %d px above the water" % (pal, o))
            rom.write(HITBOXES + n, rom.data[HITBOXES + base:HITBOXES + base + 4],
                      why="frame 0x%X's hitbox: the gondola's (Blue stands on it)" % n)
            table.append(n)
        tables.append(table)
    a, b = tables
    assert b[0] > a[-1] and b[-1] - b[0] == 4 * (len(HEIGHTS) - 1)
    by_height = [HEIGHTS.index(o if o < 0 else o & ~1) for o in range(HEIGHTS[0], HEIGHTS[-1] + 2)]
    assert rom.data[GONDOLA_DRAW:GONDOLA_DRAW + 6] == bytes.fromhex("4EB9") + DRAW.to_bytes(4, "big")
    code = rom.place_code("""
| a gondola, before it's drawn: its frame for its height above the waterline, in its colour (the waterline is at
| 384 - its spawner's y / 128 on screen, and the gondola's 32 px tall frame's top at 352 - its own y / 128, so the
| frame's bottom is the difference of the two y / 128 above it); the original frame when it's well above the water
    movem.l %%d0-%%d2/%%a0-%%a1,-(%%sp)
    movea.l 0x4010(%%a5),%%a0
    move.w (%%a5),%%d0
    lsr.w #7,%%d0
    move.w (%%a0),%%d1
    lsr.w #7,%%d1
    sub.w %%d1,%%d0
    lea first(%%pc),%%a1
    move.w #0x%(base0)X,%%d2
    move.w 8(%%a5),%%d1
    cmpi.w #0x%(base1)X,%%d1
    beq 1f
    cmpi.w #0x%(b0)X,%%d1
    bcs 2f
    cmpi.w #0x%(b1)X,%%d1
    bhi 2f
1:  lea second(%%pc),%%a1
    move.w #0x%(base1)X,%%d2
2:  cmpi.w #%(top)d,%%d0
    bge 4f
    cmpi.w #%(bottom)d,%%d0
    bge 3f
    moveq #%(bottom)d,%%d0
3:  subi.w #%(bottom)d,%%d0
    add.w %%d0,%%d0
    move.w (%%a1,%%d0.w),%%d2
4:  move.w %%d2,8(%%a5)
    movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    jmp 0x%(draw)X
first:
    .word %(first)s
second:
    .word %(second)s
""" % {"base0": GONDOLA_FRAMES[0], "base1": GONDOLA_FRAMES[1], "b0": b[0], "b1": b[-1], "top": HEIGHTS[-1] + 2,
       "bottom": HEIGHTS[0], "draw": DRAW, "first": ",".join("0x%X" % a[k] for k in by_height),
       "second": ",".join("0x%X" % b[k] for k in by_height)}, why="wheel-reflection: the gondolas' frames by height")
    rom.write(GONDOLA_DRAW + 2, code.to_bytes(4, "big"), expect=DRAW.to_bytes(4, "big"),
              why="gondola: its frame from wheel-reflection, then drawn")

    # the water patches aren't needed now (the gondolas clip themselves): their kind does nothing
    assert rom.u32(KINDS + 4 * PATCH_KIND) == PATCH_CODE
    idle = rom.place_code("""
| the water patches over the gondolas: nothing to do (wheel-reflection)
    rts
""", why="wheel-reflection: the water patches idle")
    rom.write(KINDS + 4 * PATCH_KIND, idle.to_bytes(4, "big"), expect=PATCH_CODE.to_bytes(4, "big"),
              why="the water patches' kind: idle")
