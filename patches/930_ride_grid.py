NAME = "ride-grid"
DESCRIPTION = "Travel agent's ride: the grid glides, and a diagonal chain of coloured squares sweeps across it with a fading trail"

# The ride after a destination is picked (the travel agent, room 5) flies between a floor and a ceiling of perspective
# grid - the level map engine's two layers, both from map table MAP_TABLE: the back one (sprites from 1, blocks 7-8)
# had the horizontal lines (a tile a row, the same across, in hardware auto-animation: 4 frames of the lines moving
# toward the camera, on the one animation clock anim-speed slows to 9 frames a step), the front one (sprites from 23,
# blocks 9-10) the slanted lines (a tile a row and column, still; the right half and the ceiling flipped copies).
# Now the colours do the moving:
#   * the back layer (blocks 7-8) gets the slanted lines (colour 0, see-through: the backdrop is set to their blue
#     while the ride is on) and, in the squares, colour slots 1-15 (in the slanted tiles' own slots, repainted). A
#     square pixel's diagonal d is its column (slanted lines crossed from the centre) minus its row (horizontal line
#     spacings from the horizon), and q which quarter of a spacing it lies in (the 4 frames' lines take turns); as
#     the lines step (phase p) the pixel's square is diagonal d + (q < p), = (u + p + 3) / 4 with u = 4d - q. So a
#     pixel needs only u: each tile takes a window of 15 u values (from 4 * base + shift: palette sets SETS - shift
#     0 or 2, exact; or, for the far rows whose squares are a few pixels and need more, a set by d alone, a pixel's
#     square taken as lit a quarter early at most), and a palette of its set (its base mod N): PALETTES + 15 * set
#     + base mod N.
#   * the front layer (blocks 9-10) gets the horizontal lines alone (the old line tiles, their dark filling made
#     see-through), without auto-animation: our routine steps their 4 frames itself, every STEP frames, in time with
#     the colours.
#   * each step, our routine (called from the ride's loop - RIDE_CALL, in place of its call to the ride's objects,
#     which it then makes) lights one diagonal - moving one a step - and the TRAIL behind it dimmer, in a colour from
#     COLOURS (the next each step), cycles = whole line spacings moved so far: a slot is its diagonal's place behind
#     the chain's (chain - diagonal - cycles, mod N) - lit (0), trail, or dark.
# The tiles are only the ride's.
MAP_TABLE = 0xABC12
BACK_BLOCKS, FRONT_BLOCKS = (7, 8), (9, 10)
H_TILES = [0x5560 + 8 * r for r in range(6)]          # floor row r's horizontal lines (4 frames from each)
V_TILES = [[0x555C + 8 * r + c if c < 4 else 0x5590 + 8 * r + (c - 4) for c in range(10)] for r in range(6)]
LINE_H, LINE_V, DARK = 8, 7, 15                        # palette 0x88: the lines' colours, the dark between them
PAL88 = 0x88
N = 15                                                 # diagonals between chains (the palettes a set)
SETS = (0, 2, None)                                    # the palette sets: u windows from a multiple of 4 + 0 / + 2,
                                                       # or by diagonal alone (None)
PALETTES = 0xA0                                        # N palettes a set, from here (unused while the ride is on)
STEP = 4                                               # frames a step (lines and chain)
EXACT_MISS = 8                                         # a tile's pixels an exact set may leave out (to the nearest slot)
COLOURS = [(0, 255, 197), (8, 238, 205), (8, 213, 213), (16, 205, 213), (24, 172, 222),
           (24, 156, 238), (32, 139, 246), (41, 106, 255), (32, 139, 246), (24, 156, 238),
           (24, 172, 222), (16, 205, 213), (8, 213, 213), (8, 238, 205)]   # the shimmering
                                               # floor's (Lower Earth's palette 0x90, its brightest): green to blue and back
# Other sets tried (2026-10-25) - to use one: COLOURS = COLOURS_COOL, say:
COLOURS_RAINBOW = [(230, 60, 60), (240, 150, 40), (240, 230, 60), (70, 220, 90), (60, 200, 230), (90, 110, 250),
                   (190, 90, 240)]                     # the first: red, orange, yellow, green, cyan, blue, purple
COLOURS_COOL = [(60, 200, 240), (60, 230, 200), (70, 220, 120), (60, 150, 250), (120, 110, 250), (170, 100, 250),
                (90, 230, 240)]                        # cool ones: sky, aqua, green, blue, indigo, violet, cyan
TRAIL = [1.0, 0.55, 0.25]                              # the lit diagonal, then the two before it
RIDE_ON = 0x1078AE                                     # set as the ride starts, cleared as it ends (its loop's test)
RIDE_CALL = 0x2788A                                    # jsr 0x2790E (the ride's objects), in its loop
BACKDROP = 0x401FFE
RAM = 0x10ECF0                                         # +0 on (byte), +2 the step (word), +4 frames to the next step
                                                       # (word), +6 the backdrop before (word)


def neo(rgb):
    r, g, b = (min(31, (v * 31 + 127) // 255) for v in rgb)
    return (r & 1) << 14 | (g & 1) << 13 | (b & 1) << 12 | (r >> 1) << 8 | (g >> 1) << 4 | (b >> 1)


def rgb(w):
    return tuple((((w >> s) & 15) << 1 | (w >> lo) & 1) * 255 // 31 for s, lo in ((8, 14), (4, 13), (0, 12)))


def slot_term(s, i, p):
    """A slot's diagonal past its palette's base, at phase p: set s (a shift, or None), slot i (1-15)."""
    if s is None:
        return i - 1 + (1 if p >= 1 else 0)
    return (s + i + p + 2) // 4


def tiles(rom):
    """The new tiles: back[(row, col)] (pixels), pal[(row, col)] (its palette's number from PALETTES),
    front[(row, frame)]."""
    # s(y): the index of the last horizontal line (of all 4 frames) at or above floor pixel row y
    lines = sorted((16 * r + yy, f) for r in range(6) for f in range(4)
                   for yy, row in enumerate(rom.sprite_tile(H_TILES[r] + f)) if LINE_H in row)
    assert all(f == i % 4 for i, (y, f) in enumerate(lines)), "ride-grid: the lines' frames don't take turns"
    s_of = [max(i for i, (ly, f) in enumerate(lines) if ly <= y) for y in range(96)]
    slant = [[False] * 160 for _ in range(96)]
    for r in range(6):
        for c in range(10):
            for yy, row in enumerate(rom.sprite_tile(V_TILES[r][c])):
                for xx, v in enumerate(row):
                    slant[16 * r + yy][16 * c + xx] = v == LINE_V

    def column(x, y):                                  # slanted lines crossed between x and the centre
        n, prev = 0, False
        for xx in range(159, x - 1, -1):
            if slant[y][xx] and not prev:
                n += 1
            prev = slant[y][xx]
        return n
    back, pal = {}, {}
    for r in range(6):
        for c in range(10):
            cells = [(xx, yy, column(16 * c + xx, 16 * r + yy) - s_of[16 * r + yy] // 4 + 100, s_of[16 * r + yy] % 4)
                     for yy in range(16) for xx in range(16) if not slant[16 * r + yy][16 * c + xx]]
            exact, approx = None, None                 # (pixels in the window, set, base)
            for k, s in enumerate(SETS):
                if s is None:
                    vals = [d for _, _, d, _ in cells]
                    for b in range(min(vals) - 14, max(vals) + 1):
                        n = sum(1 for v in vals if 1 <= v - b + 1 <= 15)
                        if approx is None or n > approx[0]:
                            approx = (n, k, b)
                else:
                    us = [4 * d - q for _, _, d, q in cells]
                    for b in range(min(us) // 4 - 5, max(us) // 4 + 2):
                        n = sum(1 for u in us if 1 <= u - (4 * b + s) + 1 <= 15)
                        if exact is None or n > exact[0]:
                            exact = (n, k, b)
            best = exact if len(cells) - exact[0] <= EXACT_MISS or approx[0] <= exact[0] else approx
            n, k, b = best
            s = SETS[k]
            px = [[0] * 16 for _ in range(16)]
            for xx, yy, d, q in cells:
                i = d - b + 1 if s is None else 4 * d - q - (4 * b + s) + 1
                px[yy][xx] = min(15, max(1, i))        # (outside the window: the nearest slot)
            back[(r, c)], pal[(r, c)] = px, N * k + b % N
    front = {(r, f): [[LINE_H if v == LINE_H else 0 for v in row] for row in rom.sprite_tile(H_TILES[r] + f)]
             for r in range(6) for f in range(4)}
    return back, pal, front


def apply(rom):
    back, pal, front = tiles(rom)
    where = {V_TILES[r][c]: (r, c) for r in range(6) for c in range(10)}
    for (r, c), px in back.items():
        rom.redraw_sprite_tile(V_TILES[r][c], px, why="ride grid: slanted lines and the squares' colour slots")
    for (r, f), px in front.items():
        rom.redraw_sprite_tile(H_TILES[r] + f, px, why="ride grid: horizontal lines, see-through between")

    # the maps: the back blocks get the old front blocks' cells (slanted tiles), each in its square's palette; the
    # front blocks the old back blocks' (horizontal line tiles), their auto-animation off
    def quarters(block):
        return [rom.map_quarter(rom.u32(MAP_TABLE + 16 * block + 4 * q)) for q in range(4)]
    old = {b: quarters(b) for b in BACK_BLOCKS + FRONT_BLOCKS}
    new = {}
    for nb, ob in zip(BACK_BLOCKS, FRONT_BLOCKS):
        new[nb] = [[((((PALETTES + pal[where[t]]) << 8) | (a & 0xFF)) if t in where else a, t) for a, t in cells]
                   for cells in old[ob]]
    for nb, ob in zip(FRONT_BLOCKS, BACK_BLOCKS):
        new[nb] = [[((a & ~0x0C) if (t & ~3) in H_TILES else a, t) for a, t in cells] for cells in old[ob]]
    for b, qs in new.items():
        for q, cells in enumerate(qs):
            rom.put_map_quarter(MAP_TABLE, b, q, cells, why="ride grid: map block %d quarter %d" % (b, q))

    # the routine
    dark = 0x4111
    colours = [[neo(tuple(int(rgb(dark)[i] + (c[i] - rgb(dark)[i]) * f) for i in range(3))) for f in TRAIL]
               for c in COLOURS]
    terms = [slot_term(s, i, p) for p in range(4) for s in SETS for i in range(1, 16)]   # [phase][set][slot]
    assert max(terms) < N * 2
    fb = [H_TILES[5 - k] for k in range(6)] + [H_TILES[k] for k in range(6)]   # front rows: ceiling 18-23, floor 26-31
    code = rom.place_code("""
    tst.b 0x%(ride_on)X
    bne 1f
    tst.b 0x%(on)X                      | the ride over: the backdrop back
    beq 9f
    move.w 0x%(saved)X,0x%(backdrop)X
    clr.b 0x%(on)X
9:  jmp 0x%(objects)X
1:  tst.b 0x%(on)X
    bne 2f
    move.b #1,0x%(on)X                  | the ride starts: the backdrop the slanted lines' blue
    move.w 0x%(backdrop)X,0x%(saved)X
    move.w 0x%(linev_addr)X,0x%(backdrop)X
    clr.w 0x%(step)X
    clr.w 0x%(wait)X
2:  subq.w #1,0x%(wait)X
    bpl 9b
    move.w #%(step_frames_1)d,0x%(wait)X
    movem.l %%d0-%%d7/%%a0-%%a4,-(%%sp)
    lea -%(lit_bytes)d(%%sp),%%sp       | the step's colours by place behind the chain (N words)
    move.w 0x%(step)X,%%d7              | d7 = the step
    addq.w #1,0x%(step)X
    moveq #0,%%d1
    move.w %%d7,%%d1
    divu #%(ncol)d,%%d1
    swap %%d1                           | d1 = step mod the colours (its colour)
    moveq #3,%%d2
    and.w %%d7,%%d2                     | d2 = the phase
    moveq #0,%%d0
    move.w %%d7,%%d0
    move.w %%d7,%%d3
    lsr.w #2,%%d3                       | d3 = cycles
    sub.w %%d3,%%d0                     | step - cycles
    add.w #%(n100)d,%%d0
    divu #%(n)d,%%d0
    swap %%d0                           | d0 = (chain - cycles) mod N
    | the colours by place: lit, trail, then dark
    move.l %%sp,%%a0
    moveq #0,%%d4
3:  cmp.w #%(trail)d,%%d4
    bcc 4f
    move.w %%d1,%%d5                    | (step - place) mod the colours
    sub.w %%d4,%%d5
    bpl 5f
    add.w #%(ncol)d,%%d5
5:  mulu #%(trail2)d,%%d5
    add.w %%d4,%%d5
    add.w %%d4,%%d5
    lea colours(%%pc),%%a1
    move.w (%%a1,%%d5.w),(%%a0)+
    bra 6f
4:  move.w 0x%(dark_addr)X,(%%a0)+
6:  addq.w #1,%%d4
    cmp.w #%(n)d,%%d4
    bcs 3b
    | the front layer: its lines' frame
    move.w #2,0x3C0004
    move.w 0x10024A,%%d4                | (the front layer's first sprite)
    lsl.w #6,%%d4
    moveq #20,%%d5
7:  lea front_rows(%%pc),%%a1
    move.w %%d4,%%d6
    add.w #36,%%d6
    move.w %%d6,0x3C0000
    moveq #5,%%d6
8:  move.w (%%a1)+,%%a2
    add.w %%d2,%%a2
    move.w %%a2,0x3C0002
    dbra %%d6,8b
    move.w %%d4,%%d6
    add.w #52,%%d6
    move.w %%d6,0x3C0000
    moveq #5,%%d6
10: move.w (%%a1)+,%%a2
    add.w %%d2,%%a2
    move.w %%a2,0x3C0002
    dbra %%d6,10b
    add.w #64,%%d4
    dbra %%d5,7b
    move.w #1,0x3C0004
    | the palettes: set by set, base by base, slot by slot - place = (chain - cycles) - base - the slot's term
    lea 0x%(pal0)X,%%a0
    lea terms(%%pc),%%a1
    move.w %%d2,%%d4
    mulu #%(set_terms)d,%%d4
    add.w %%d4,%%a1                     | a1 = this phase's terms
    lea modn(%%pc),%%a3
    moveq #%(sets_1)d,%%d6
11: moveq #0,%%d5                       | d5 = the base
12: lea 2(%%a0),%%a4
    move.w %%d0,%%d4
    sub.w %%d5,%%d4
    add.w #%(n3)d,%%d4                  | (kept positive)
    moveq #14,%%d7
13: move.w %%d4,%%d3
    sub.b (%%a1,%%d7.w),%%d3
    move.b (%%a3,%%d3.w),%%d3
    ext.w %%d3
    add.w %%d3,%%d3
    move.w %%d7,%%d2
    add.w %%d2,%%d2
    move.w (%%sp,%%d3.w),(%%a4,%%d2.w)
    dbra %%d7,13b
    lea 32(%%a0),%%a0
    addq.w #1,%%d5
    cmp.w #%(n)d,%%d5
    bcs 12b
    lea 15(%%a1),%%a1
    dbra %%d6,11b
    lea %(lit_bytes)d(%%sp),%%sp
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a4
    jmp 0x%(objects)X
front_rows:
    .word %(front_rows)s
colours:
    .word %(colours)s
terms:
    .byte %(terms)s
modn:
    .byte %(modn)s
    .even
""" % {"ride_on": RIDE_ON, "on": RAM, "step": RAM + 2, "wait": RAM + 4, "saved": RAM + 6, "backdrop": BACKDROP,
       "objects": rom.u32(RIDE_CALL + 2), "dark_addr": 0x400000 + PAL88 * 32 + DARK * 2,
       "linev_addr": 0x400000 + PAL88 * 32 + LINE_V * 2, "pal0": 0x400000 + PALETTES * 32, "n": N, "ncol": len(COLOURS),
       "n100": 100 * N, "n3": 3 * N, "step_frames_1": STEP - 1, "trail": len(TRAIL), "trail2": len(TRAIL) * 2,
       "lit_bytes": 2 * N, "set_terms": 15 * len(SETS), "sets_1": len(SETS) - 1,
       "front_rows": ",".join("0x%04X" % t for t in fb),
       "colours": ",".join("0x%04X" % w for row in colours for w in row),
       "terms": ",".join(str(t) for t in terms),
       "modn": ",".join(str(v % N) for v in range(5 * N))},
        why="ride grid: the lines' frame and the squares' colours each step")
    assert rom.u16(RIDE_CALL) == 0x4EB9
    rom.write(RIDE_CALL + 2, code.to_bytes(4, "big"), expect=rom.u32(RIDE_CALL + 2).to_bytes(4, "big"),
              why="the ride's loop: the grid's step first, then its objects")
