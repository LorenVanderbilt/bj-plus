NAME = "water-tint"
DESCRIPTION = "Parked (both parts off): the water's wave line carried over the shore's grass, and a tint below the water line"

# The water's surface is in the background and the land is drawn in front of it, so where the land slopes into the
# water nothing showed it was submerged. Now, on the stages in STAGES, below the water line some colours are tinted
# TINT_K of the way toward TINT_TO: each stage's grass greens and water blues (picked by palette entry, the dirt's
# browns left alone - sta/aes/swim_flippers.sta: Empire Marsh 2). It's a split screen in time:
#   * at each vblank (a hook ahead of anim-speed's, on the vblank vector): last frame's original colours back; the
#     water line found (the water layer's sprites from WATER: its row of surface tiles SURFACE, its screen y, + the
#     stage's SPLIT_DY); the tinted copies made; the LSPC timer armed to interrupt at that line (counted in pixel
#     clocks, 384 a line, from the vblank - LINES_TO_TOP to the screen's first line); its enable / reload-at-vblank
#     bits put in the game's copy of the LSPC mode (0x1002C2: anim-speed writes it out each vblank). With the line
#     off the top (the camera under water: the water layer's tile mid-screen in the water's palette) the tint goes
#     on there and then, for the whole frame;
#   * the timer interrupt (vector 0x68; the game's own 0x9A0A, never used - its mode copy's timer bits stay clear - is
#     no longer called: it re-arms the timer every 0x2FF clocks) writes the
#     tinted colours: everything drawn below that line uses them.
# Parked for after the beta: SHORE, the wave line over the shore, is off (2026-10-15: its 56 sprite tiles went to the
# title banner), and the tint (TINT_K 0) too - so nothing of this goes in. Picking it up again: its code still has
# three "debug" reads of the raster line (into RAM), from tuning the split - out first.
SHORE = False
TINT_K = 0.0   # (tint off for now - 0.35 was the tried strength; at 0 none of its code goes in. NB the water's
               # shimmer turns colours round in place (0xD2-0xD4 10-15): check that against the restore if it's on)
TINT_TO = (1, 5, 15)          # 5-bit r, g, b: a deep blue
STAGES = {   # stage: (water layer's first sprite, surface tiles, split dy px, {palette: [entries]}, water palette)
    10: (23, (0x3480, 0x348F), 8, {0x90: [8, 9, 10, 11, 12], 0xD4: range(10, 16), 0xD3: range(10, 16),
                                   0xD2: range(10, 16)}, 0xD4),   # (the water deepens 0xD4, 0xD3, 0xD2)
}
LINES_TO_TOP = 59             # timer lines from its load (in the vblank) to the screen's first line (measured in MAME)
MODE_COPY = 0x1002C2
GAME_TIMER_WRITE = 0x99B6     # move.w #0x3C00,0x3C000A - the game's vblank sets the timer's low word, a timer it never
                              # turns on; with ours loaded on that write it reset ours every frame: skipped
TIMER_BITS = 0x30             # LSPC mode: timer interrupt on (bit 4), loaded when its low word is written (bit 5)
STAGE_AT = 0x103005
RAM = 0x10EC10                # +0 armed, +1 tinted now, +2 entries (word), +4 debug: the line the timer hit, +6 the
                              # shore line's sprites drawn last frame (word), +8 / +10 the water layer's top, the
                              # column being looked at (words), +12 its surface rows done (long, a bit each)
MAX_ENTRIES = 24
SAVE, TINTED_COLOURS, ADDRS = RAM + 0x10, RAM + 0x40, RAM + 0x70   # (MAX_ENTRIES each: to 0x10ECD0)


# The surface's wave line alone, for drawing over the shore: copies of the surface tiles (two 4-step animations,
# 0x3480-0x3483 / 0x3484-0x3487: the hardware animates them, attribute bit 2) keeping only the crest
# (CREST_COLOURS, LINE_DEPTH), the rest clear - at LINE_TILES, aligned so the hardware animates them the same.
SURFACE_TILES = range(0x3480, 0x3488)
LINE_TILES = 0x4FF8                 # (spare-tiles' last run: taken out of the pool)
LINE_DEPTH = 4
CREST_COLOURS = {1, 2, 3, 7}   # (the crest's light edge and dark outline; 4, 5, 6 and 8 are the flat band above)

# The wave line drawn over the shore. The land layer (LAND, chains of sprites) is looked at on the line's pixel row
# (LINE_Y below the surface row's top), each tile's opaque pixels there from a table (SPAN_TILES tiles: an index of
# 16-row profiles, first x << 4 | last x a row, 0xF0 none - see spans): where it turns from land to nothing (or back)
# is a shore, at that pixel. From there the water layer's columns reaching INTO_L / INTO_R pixels into the land (to
# the edge's left / right) and to a tile past the edge get a sprite with the line tile matching that column's surface
# tile (same attributes: it animates with it) - the last column into the land cut in 4-pixel steps (CUTS: copies with
# their left / right columns cleared), so the line's end slides with the scrolling. Sprites SHORE_SPRITES, up to
# SHORE_MAX. Done right after the game sets the layers' positions for the frame (0x117FE: jsr 0x556A4, at the top
# border - so the line keeps up with the scrolling: the water and the land scroll at different speeds), by taking
# over the call after it (0x11804).
SHORE_HOOK = 0x11804
LAND = (100, 131)
SPAN_TILES = 0x3200                 # (the land layers seen use tiles below this; past it: taken as solid)
OPEN_PALETTES = (0xEB, 0xEC, 0xEE)  # (the land layer's waterfall at Empire Marsh 2: the line goes on under it)
LINE_Y = 7
INTO_L, INTO_R = 24, 0
CUTS = (4, 8, 12)
WATER_COLUMNS = 21                  # (the water layer's sprites)
SHORE_SPRITES, SHORE_MAX = 350, 10
SLOT_COL = 0x10E9C0                 # (32 bytes: spare RAM)
COUNT = 0x10E9E0                    # +0 frames (word), +2 / +4 the water layer's x / y last frame, +6 / +8 a place,
                                    # places left, +10 / +12 each half's line sprites drawn up to, +14 the half's
                                    # last, +16 / +18 its land sprites, +20 the land chain's first (words; spare RAM)
WATER_NEAR = 0x10E96C               # (a long: spare RAM)
COLUMN_X = 0x10E940                 # the water layer's columns' x this frame (WATER_COLUMNS words: spare RAM to 0x10E96A)


def line_tiles(rom):
    """In each pixel column, LINE_DEPTH pixels from the crest's first light or outline pixel down (some columns' crest
    alone is a pixel thin: the grass showed through)."""
    lines = []
    for k, t in enumerate(SURFACE_TILES):
        px = rom.sprite_tile(t)
        line = [[0] * 16 for _ in px]
        for x in range(16):
            top = next(y for y, row in enumerate(px) if row[x] in CREST_COLOURS)
            for y in range(top, top + LINE_DEPTH):
                line[y][x] = px[y][x]
        n = LINE_TILES + k
        rom.tile_pool.remove(n)
        rom.put_sprite_tile(n, line, why="water tint: the surface's wave line alone")
        lines.append(line)
    return lines


def cut_tiles(rom, lines):
    """The line tiles with their left (or right) CUTS columns cleared, each set of 8 starting on a multiple of 4 (the
    hardware's animation steps the low 2 bits). Returns the sets' first tiles: whole, left cuts, right cuts."""
    pool = set(rom.tile_pool)
    starts = [t for t in sorted(pool) if t >= 0x100 and t % 4 == 0 and all(t + i in pool for i in range(8))]
    #   (not spare-tiles' low runs: they came later, and the tiles handed out before stay where they were)
    firsts = []
    for t in starts:
        if len(firsts) == 2 * len(CUTS):
            break
        if not firsts or t >= firsts[-1] + 8:
            firsts.append(t)
    assert len(firsts) == 2 * len(CUTS), "not enough spare tiles"
    for n, first in enumerate(firsts):
        cut, right = CUTS[n % len(CUTS)], n >= len(CUTS)
        for k in range(8):
            px = [[0 if (x >= 16 - cut if right else x < cut) else v for x, v in enumerate(row)] for row in lines[k]]
            rom.tile_pool.remove(first + k)
            rom.put_sprite_tile(first + k, px, why="water tint: the wave line, cut for the shore's end")
    return [LINE_TILES] + firsts


def spans(rom):
    """The land tiles' opaque pixels per row (see SPAN_TILES): returns the index's and the profiles' addresses."""
    profiles, index = {}, []
    for t in range(SPAN_TILES):
        rows = []
        for row in rom.sprite_tile(t):
            xs = [x for x, v in enumerate(row) if v]
            rows.append(xs[0] << 4 | xs[-1] if xs else 0xF0)
        index.append(profiles.setdefault(bytes(rows), len(profiles)))
    blob = b"".join(sorted(profiles, key=profiles.get))
    at_index = rom.alloc(2 * len(index))
    rom.write(at_index, b"".join(i.to_bytes(2, "big") for i in index), why="water tint: the land tiles' profiles (index)")
    at_rows = rom.alloc(len(blob))
    rom.write(at_rows, blob, why="water tint: the land tiles' opaque pixels per row (%d profiles)" % len(profiles))
    return at_index, at_rows


def shore_line(rom, lines):
    tiles = cut_tiles(rom, lines)
    original = rom.u32(SHORE_HOOK + 2)
    span_index, span_rows = spans(rom)
    stages = ""
    for i, (stage, (water, (lo, hi), _, _, _)) in enumerate(sorted(STAGES.items())):
        stages += r"""
    cmpi.b #%(stage)d,0x%(stage_at)X
    bne 9%(i)df
    move.w #%(water)d,%%a3              | a3 = the water layer's first sprite
    move.l #0x%(range)X,%%a4            | a4 = its surface tiles' range
    bra found
9%(i)d:""" % {"i": i, "stage": stage, "stage_at": STAGE_AT, "water": water, "range": lo << 16 | hi}
    code = rom.place_code(r"""
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    move.w %%sr,-(%%sp)
    ori.w #0x0100,%%sr                  | (no vblank in between: it reads the video RAM too)
    move.w 0x3C0006,%%d1                | (debug: the raster line it started on)
    lsr.w #7,%%d1
    move.w %%d1,0x%(ram)X+2
    lea 0x3C0000,%%a0
    lea 0x3C0002,%%a1
    moveq #0,%%d7                       | d7 = line sprites drawn
%(stages)s
    bra end

found:
    move.w %%a3,%%d1                    | the water layer's y / height
    add.w #0x8200,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),%%d0
    move.w %%d0,%%d1
    andi.w #63,%%d1
    beq end
    lsr.w #7,%%d0
    neg.w %%d0
    add.w #496,%%d0
    move.w %%d0,0x%(ram)X+8             | its top's screen y
    addq.w #1,0x%(count)X               | 1 frame in 4 worked out afresh; the others, last frame's line moved with the
    move.w 0x%(count)X,%%d1             | water layer (it's in step with it; the land drifts from it by less than a
    andi.w #3,%%d1                      | pixel a frame) - and on the others the columns' table made / surface rows
    move.w %%a3,%%d4                    | looked for, a frame each (no frame does much)                    | d4 / d5 = how far it moved across / down (its first sprite starts a chain)
    add.w #0x8400,%%d4
    move.w %%d4,(%%a0)
    move.w (%%a1),%%d4
    lsr.w #7,%%d4
    move.w %%d4,%%d1
    sub.w 0x%(count)X+2,%%d4
    move.w %%d1,0x%(count)X+2
    move.w %%d0,%%d5
    sub.w 0x%(count)X+4,%%d5
    move.w %%d0,0x%(count)X+4
    lsl.w #7,%%d4
    lsl.w #7,%%d5
    moveq #2*%(half)d-1,%%d3            | (all the line's sprites: the hidden ones don't mind)
    move.w #%(first)d,%%d6
54: move.w %%d6,%%d1
    add.w #0x8400,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),%%d2
    add.w %%d4,%%d2
    move.w %%d2,(%%a1)
    sub.w #0x200,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),%%d2
    sub.w %%d5,%%d2
    move.w %%d2,(%%a1)
    addq.w #1,%%d6
    dbf %%d3,54b
55: move.w 0x%(count)X,%%d1             | frame 0: the table; 1: the land's first half's shores; 2: the surface
    andi.w #3,%%d1                      | rows; 3: the land's second half's shores
    bne 57f
    bsr table
    bra leave
57: btst #0,%%d1
    bne 56f
    clr.l 0x%(ram)X+12                  | (the rows found: a bit each)
    move.w %%a3,0x%(ram)X+10            | each of its columns: its row of surface tiles
40: move.w 0x%(ram)X+10,%%d2
    move.w %%d2,%%d1                    | (off the screen: not looked at)
    sub.w %%a3,%%d1
    add.w %%d1,%%d1
    lea 0x%(column_x)X,%%a2
    move.w 0(%%a2,%%d1.w),%%d1
    cmpi.w #320,%%d1
    bcs 45f
    cmpi.w #496,%%d1
    bls 41f
45: lsl.w #6,%%d2
    move.w %%d2,%%d6                    | d6 = the column's tiles
    move.w 0x%(ram)X+8,%%d3             | its rows on the screen: from the one at the top, 15
    neg.w %%d3
    andi.w #511,%%d3
    lsr.w #4,%%d3
    moveq #14,%%d4
    move.l %%a4,%%d5
    swap %%d5                           | d5 = the first surface tile
1:  andi.w #31,%%d3
    move.w %%d3,%%d2
    add.w %%d2,%%d2
    add.w %%d6,%%d2
    move.w %%d2,(%%a0)
    move.w (%%a1),%%d1
    cmp.w %%d5,%%d1
    bcs 2f
    cmp.w %%a4,%%d1
    bls 3f
2:  addq.w #1,%%d3
    dbf %%d4,1b
    bra 41f
3:  move.l 0x%(ram)X+12,%%d1
    bset %%d3,%%d1
    move.l %%d1,0x%(ram)X+12
41: addq.w #3,0x%(ram)X+10             | (every 3rd column: a pool's wider than that)
    move.w %%a3,%%d1
    add.w #%(columns)d,%%d1
    cmp.w 0x%(ram)X+10,%%d1
    bhi 40b
    bra leave
56: move.w %%a3,%%d4                    | (frame 1: the table, made last frame, moved with the layer since)
    add.w #0x8400,%%d4
    move.w %%d4,(%%a0)
    move.w (%%a1),%%d4
    lsr.w #7,%%d4
    sub.w 0x%(column_x)X,%%d4
    lea 0x%(column_x)X,%%a2
    moveq #%(columns)d-1,%%d3
58: add.w %%d4,(%%a2)
    andi.w #511,(%%a2)+
    dbf %%d3,58b
    move.w #%(land_first)d,%%d6         | the land layer: the longest chain among LAND's sprites (the others are
    moveq #0,%%d2                       | objects - the waterfall's foam: not land), d3 = its first, d4 its length
    moveq #0,%%d3
    moveq #0,%%d4
67: move.w %%d6,%%d5
    add.w #0x8200,%%d5
    move.w %%d5,(%%a0)
    move.w (%%a1),%%d5
    btst #6,%%d5
    bne 68f
    move.w %%d6,%%a2                    | (a chain's first: a2 = it, d2 = its length so far)
    moveq #0,%%d2
68: addq.w #1,%%d2
    cmp.w %%d4,%%d2
    bls 69f
    move.w %%d2,%%d4
    move.w %%a2,%%d3
69: addq.w #1,%%d6
    cmpi.w #%(land_last)d+1,%%d6
    bne 67b
    move.w %%d3,0x%(count)X+20
    moveq #0,%%d7                       | the half: its land sprites, its line sprites (d7 = drawn: from its first)
    move.w #%(half)d,0x%(count)X+14
    lsr.w #1,%%d4
    move.w %%d3,0x%(count)X+16
    add.w %%d4,%%d3
    move.w %%d3,0x%(count)X+18
    cmpi.w #1,%%d1
    beq 59f
    moveq #%(half)d,%%d7
    move.w #2*%(half)d,0x%(count)X+14
    subq.w #1,%%d3
    move.w %%d3,0x%(count)X+16
    add.w %%d4,%%d3
    addq.w #1,%%d3
    move.w %%d3,0x%(count)X+18
59: move.w %%d1,-(%%sp)
    moveq #0,%%d3                       | each surface row found: its shores
48: move.l 0x%(ram)X+12,%%d1
    btst %%d3,%%d1
    beq 49f
    move.w %%d3,-(%%sp)
    move.w %%d3,%%d2
    add.w %%d2,%%d2                     | d2 = the row's offset in a sprite's tiles
    move.w %%d3,%%d0
    lsl.w #4,%%d0
    add.w 0x%(ram)X+8,%%d0
    andi.w #511,%%d0                    | d0 = the surface row's screen y
    bsr pass
    move.w (%%sp)+,%%d3
49: addq.w #1,%%d3
    cmpi.w #32,%%d3
    bne 48b
    move.w (%%sp)+,%%d1                 | its line sprites not drawn this time: hidden
    lea 0x%(count)X+10,%%a2
    cmpi.w #1,%%d1
    beq 60f
    addq.l #2,%%a2
60: move.w (%%a2),%%d1
    move.w %%d7,(%%a2)
    cmp.w 0x%(count)X+14,%%d1           | (no further than the half's: the RAM may hold anything at first)
    bls 61f
    move.w 0x%(count)X+14,%%d1
61: sub.w %%d7,%%d1
    ble leave
    move.w #0x8200+%(first)d,%%d2
    add.w %%d7,%%d2
    subq.w #1,%%d1
66: move.w %%d2,(%%a0)
    move.w #0,(%%a1)
    addq.w #1,%%d2
    dbf %%d1,66b
    bra leave

| the water layer's columns' x (COLUMN_X) and places (SLOT_COL)
table:
    move.w %%a3,%%d6                    | its columns' x: a table (COLUMN_X)
    moveq #0,%%d5
    lea 0x%(column_x)X,%%a2
    moveq #%(columns)d-1,%%d3
42: move.w %%d6,%%d1
    add.w #0x8200,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),%%d1
    btst #6,%%d1
    bne 43f
    move.w %%d6,%%d5
    add.w #0x8400,%%d5
    move.w %%d5,(%%a0)
    move.w (%%a1),%%d5
    lsr.w #7,%%d5
    bra 44f
43: add.w #16,%%d5
44: andi.w #511,%%d5
    move.w %%d5,(%%a2)+
    addq.w #1,%%d6
    dbf %%d3,42b
    lea 0x%(slot_col)X,%%a2             | and which column is at each 16-pixel place from the first's x (SLOT_COL;
    moveq #-1,%%d1                      | -1 none)
    move.l %%d1,(%%a2)+
    move.l %%d1,(%%a2)+
    move.l %%d1,(%%a2)+
    move.l %%d1,(%%a2)+
    move.l %%d1,(%%a2)+
    move.l %%d1,(%%a2)+
    move.l %%d1,(%%a2)+
    move.l %%d1,(%%a2)+
    lea 0x%(column_x)X,%%a2
    moveq #0,%%d3
53: move.w %%d3,%%d1
    add.w %%d1,%%d1
    move.w 0(%%a2,%%d1.w),%%d1
    sub.w (%%a2),%%d1
    andi.w #511,%%d1
    lsr.w #4,%%d1
    lea 0x%(slot_col)X,%%a6
    move.b %%d3,0(%%a6,%%d1.w)
    addq.w #1,%%d3
    cmpi.w #%(columns)d,%%d3
    bne 53b
    rts

| the land layer on that row's line: its shores get the line
pass:
    move.w %%a3,%%d6                    | the water columns with the surface on this row: WATER_NEAR, a bit for each
    moveq #0,%%d5                       | 16 pixels, widened by 2 (land further from them is not looked at)
    moveq #0,%%d3
50: move.w %%d6,%%d1
    lsl.w #6,%%d1
    add.w %%d2,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),%%d1
    move.l %%a4,%%d4
    swap %%d4
    cmp.w %%d4,%%d1
    bcs 51f
    cmp.w %%a4,%%d1
    bhi 51f
    move.w %%d3,%%d1                    | (its place, 16 pixels each from the first column's x, round the 512)
    add.w %%d1,%%d1
    lea 0x%(column_x)X,%%a2
    move.w 0(%%a2,%%d1.w),%%d1
    sub.w (%%a2),%%d1
    andi.w #511,%%d1
    lsr.w #4,%%d1
    bset %%d1,%%d5
51: addq.w #1,%%d6
    addq.w #1,%%d3
    cmpi.w #%(columns)d,%%d3
    bne 50b
    tst.l %%d5
    beq 52f
    move.l %%d5,%%d1
    rol.l #1,%%d1
    or.l %%d1,%%d5
    rol.l #1,%%d1
    or.l %%d1,%%d5
    move.l %%d5,%%d1
    ror.l #2,%%d1
    or.l %%d1,%%d5
    ror.l #1,%%d1
    or.l %%d1,%%d5
    move.l %%d5,0x%(water_near)X
    move.w 0x%(count)X+20,%%d1          | (the chain's first: x and y to start from - the half may start mid-chain)
    move.w %%d1,%%d3
    add.w #0x8400,%%d3
    move.w %%d3,(%%a0)
    move.w (%%a1),%%d3
    lsr.w #7,%%d3
    move.w %%d1,%%d5
    add.w #0x8200,%%d5
    move.w %%d5,(%%a0)
    move.w (%%a1),%%d5
    lsr.w #7,%%d5
    neg.w %%d5
    add.w #496,%%d5
    movea.w %%d5,%%a5
    move.w 0x%(count)X+16,%%d6
    sub.w %%d1,%%d6
    subq.w #1,%%d6
    lsl.w #4,%%d6
    add.w %%d6,%%d3
    move.w 0x%(count)X+16,%%d6          | the land layer's sprites (the half's): d6 = sprite, d3 = x, a5 = y, d4 = the last one on
    moveq #-1,%%d4                      | the line's pixel row: its land's right end (x), -2 nothing there, -1 none yet
    movea.w %%d4,%%a2
4:  move.w %%d6,%%d1
    add.w #0x8200,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),%%d1
    btst #6,%%d1
    bne 5f
    move.w %%d6,%%d3                    | (a chain's first sprite: its own x and y)
    add.w #0x8400,%%d3
    move.w %%d3,(%%a0)
    move.w (%%a1),%%d3
    lsr.w #7,%%d3
    lsr.w #7,%%d1
    neg.w %%d1
    add.w #496,%%d1
    movea.w %%d1,%%a5
    moveq #-1,%%d4
    movea.w %%d4,%%a2
    bra 6f
5:  add.w #16,%%d3
6:  move.w %%d3,%%d1                    | (well off the screen: not looked at, nothing carried over)
    andi.w #511,%%d1
    cmpi.w #336,%%d1
    bcs 64f
    cmpi.w #480,%%d1
    bhi 64f
    moveq #-1,%%d4
    movea.w %%d4,%%a2
    bra 8f
64: move.w %%d3,%%d1                    | (not near the water: not looked at, nothing carried over)
    sub.w 0x%(column_x)X,%%d1
    andi.w #511,%%d1
    lsr.w #4,%%d1
    move.l 0x%(water_near)X,%%d5
    btst %%d1,%%d5
    bne 65f
    moveq #-1,%%d4
    movea.w %%d4,%%a2
    bra 8f
65: bsr span                            | d1 = its land on the line's pixel row: first x << 4 | last x
    cmpi.w #0xF1,%%d1                   | (the waterfall: a run of it gets the line all along, a2 = where it began)
    bne 62f
    cmpa.w #-1,%%a2
    bne 63f
    movea.w %%d3,%%a2
    bra 63f
62: cmpa.w #-1,%%a2
    beq 63f
    movem.l %%d3-%%d4,-(%%sp)
    move.w %%d3,%%d4
    move.w %%a2,%%d3
    bsr near
    movem.l (%%sp)+,%%d3-%%d4
    movea.w #-1,%%a2
63: move.w %%d1,%%d5
    lsr.w #4,%%d5
    andi.w #15,%%d1
    cmp.w %%d1,%%d5
    bls 7f
    tst.w %%d4                          | nothing there: after land, a shore (the land to its left)
    bmi 61f
    movem.l %%d3-%%d4,-(%%sp)
    move.w %%d4,%%d3
    sub.w #%(into_l)d,%%d3
    add.w #16,%%d4
    bsr near
    movem.l (%%sp)+,%%d3-%%d4
61: moveq #-2,%%d4
    bra 8f
7:  cmpi.w #-2,%%d4                     | land: after nothing, a shore (the land to its right)
    bne 71f
    movem.l %%d3-%%d4,-(%%sp)
    add.w %%d5,%%d3
    move.w %%d3,%%d4
    add.w #%(into_r)d,%%d4
    sub.w #16,%%d3
    bsr near
    movem.l (%%sp)+,%%d3-%%d4
71: move.w %%d3,%%d4
    add.w %%d1,%%d4
    addq.w #1,%%d4
8:  addq.w #1,%%d6
    cmp.w 0x%(count)X+18,%%d6
    bls 4b
52: rts

end:                                    | (no water here: the line's sprites hidden)
    tst.l 0x%(count)X+10
    beq leave
    clr.l 0x%(count)X+10
    move.w #0x8200+%(first)d,%%d2
    moveq #2*%(half)d-1,%%d1
10: move.w %%d2,(%%a0)
    move.w #0,(%%a1)
    addq.w #1,%%d2
    dbf %%d1,10b
leave:
    move.w 0x3C0006,%%d1                | (debug: the raster line it finished on)
    lsr.w #7,%%d1
    move.w %%d1,0x%(ram)X+4
    move.w (%%sp)+,%%sr
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
    jmp 0x%(original)X

| d1 = land layer sprite d6's (top a5) opaque pixels on the line's pixel row: first x << 4 | last x (0xF0: none)
span:
    move.l %%d3,-(%%sp)
    move.w %%d0,%%d1
    add.w #%(line_y)d,%%d1
    sub.w %%a5,%%d1
    andi.w #511,%%d1
    move.w %%d1,%%d5
    lsr.w #4,%%d5
    add.w %%d5,%%d5
    andi.w #15,%%d1                     | d1 = the pixel row in the tile
    move.w %%d6,%%d3
    lsl.w #6,%%d3
    add.w %%d5,%%d3
    move.w %%d3,(%%a0)
    move.w (%%a1),%%d5                  | its tile
    addq.w #1,%%d3
    move.w %%d3,(%%a0)
    move.w (%%a1),%%d3                  | and attributes
    move.w %%d3,-(%%sp)
    lsr.w #8,%%d3
%(open_palettes)s    move.w (%%sp)+,%%d3
    btst #1,%%d3
    beq 1f
    eori.w #15,%%d1                     | (flipped up-down)
1:  cmpi.w #%(span_tiles)d,%%d5
    bcc 3f
    add.w %%d5,%%d5
    movea.l #0x%(span_index)X,%%a6
    move.w 0(%%a6,%%d5.w),%%d5
    andi.l #0xFFFF,%%d5
    lsl.l #4,%%d5
    movea.l #0x%(span_rows)X,%%a6
    adda.l %%d5,%%a6
    move.b 0(%%a6,%%d1.w),%%d1
    andi.w #0xFF,%%d1
    btst #0,%%d3
    beq 2f
    ror.b #4,%%d1                       | (flipped sideways: first / last swapped and mirrored)
    eori.b #0xFF,%%d1
2:  move.l (%%sp)+,%%d3
    rts
3:  moveq #0x0F,%%d1                    | (past the table: solid)
    bra 2b
4:  addq.w #2,%%sp                     | (a palette that isn't land - the waterfall's: nothing there, 0xF1)
    move.w #0xF1,%%d1
    bra 2b

| x d3 to d4: the water layer's columns there (on the screen) get the line, the end ones cut to it in 4-pixel steps
near:
    movem.l %%d1/%%d3-%%d6/%%a2,-(%%sp)
    andi.w #511,%%d3
    andi.w #511,%%d4
    move.w %%d3,%%d1                    | the places from a tile before the start to the end (SLOT_COL)
    sub.w #16,%%d1
    sub.w 0x%(column_x)X,%%d1
    andi.w #511,%%d1
    lsr.w #4,%%d1
    move.w %%d1,0x%(count)X+6
    move.w %%d4,%%d1
    sub.w %%d3,%%d1
    andi.w #511,%%d1
    lsr.w #4,%%d1
    addq.w #2,%%d1
    move.w %%d1,0x%(count)X+8
12: cmp.w 0x%(count)X+14,%%d7           | (all the half's sprites used: no more)
    bge 18f
    move.w 0x%(count)X+6,%%d1
    andi.w #31,%%d1
    lea 0x%(slot_col)X,%%a2
    move.b 0(%%a2,%%d1.w),%%d1
    bmi 16f
    ext.w %%d1
    move.w %%a3,%%d6
    add.w %%d1,%%d6                     | d6 = the column there
    add.w %%d1,%%d1
    lea 0x%(column_x)X,%%a2
    move.w 0(%%a2,%%d1.w),%%d5          | d5 = its x
    move.w %%d5,%%d1                    | (off the screen, x 320-496: none)
    cmpi.w #320,%%d1
    bcs 34f
    cmpi.w #496,%%d1
    bls 16f
34: move.w %%d5,%%d1                    | d1 = the column's x - the start's (-256 to 255)
    sub.w %%d3,%%d1
    add.w #256,%%d1
    andi.w #511,%%d1
    sub.w #256,%%d1
    cmpi.w #-16,%%d1
    ble 16f
    tst.w %%d1
    bpl 35f
    neg.w %%d1                          | (over the start: its left columns cut)
    addq.w #2,%%d1
    lsr.w #2,%%d1
    cmpi.w #%(n_cuts)d+1,%%d1
    beq 16f
    bra 33f
35: move.w %%d4,%%d1                    | d1 = the end's x - the column's
    sub.w %%d5,%%d1
    add.w #256,%%d1
    andi.w #511,%%d1
    sub.w #256,%%d1
    tst.w %%d1
    ble 16f
    cmpi.w #16,%%d1
    bge 36f
    neg.w %%d1                          | (over the end: its right columns cut)
    add.w #16+2,%%d1
    lsr.w #2,%%d1
    beq 33f
    cmpi.w #%(n_cuts)d+1,%%d1
    beq 16f
    addq.w #%(n_cuts)d,%%d1
    bra 33f
36: moveq #0,%%d1
33: cmp.w 0x%(count)X+14,%%d7
    bge 16f
    add.w %%d1,%%d1
    move.w %%d1,-(%%sp)
    move.w %%d6,%%d1                    | its surface tile
    lsl.w #6,%%d1
    add.w %%d2,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),%%d4
    move.l %%a4,%%d1
    swap %%d1
    sub.w %%d1,%%d4
    move.w (%%sp)+,%%d1
    cmpi.w #8,%%d4
    bcc 17f
    lea cuts(%%pc),%%a2
    add.w 0(%%a2,%%d1.w),%%d4
    move.w %%d6,%%d1                    | (its attributes)
    lsl.w #6,%%d1
    add.w %%d2,%%d1
    addq.w #1,%%d1
    move.w %%d1,(%%a0)
    move.w (%%a1),-(%%sp)
    move.w #%(first)d,%%d1              | the line sprite: tile, attributes, full size, y and height 1, x
    add.w %%d7,%%d1
    lsl.w #6,%%d1
    move.w %%d1,(%%a0)
    move.w %%d4,(%%a1)
    addq.w #1,%%d1
    move.w %%d1,(%%a0)
    move.w (%%sp)+,(%%a1)
    move.w #0x8000+%(first)d,%%d1
    add.w %%d7,%%d1
    move.w %%d1,(%%a0)
    move.w #0x0FFF,(%%a1)
    add.w #0x200,%%d1
    move.w %%d1,(%%a0)
    move.w #496,%%d4
    sub.w %%d0,%%d4
    andi.w #511,%%d4
    lsl.w #7,%%d4
    addq.w #1,%%d4
    move.w %%d4,(%%a1)
    add.w #0x200,%%d1
    move.w %%d1,(%%a0)
    move.w %%d5,%%d4
    andi.w #511,%%d4
    lsl.w #7,%%d4
    move.w %%d4,(%%a1)
    addq.w #1,%%d7
17: move.l 8(%%sp),%%d4                 | (d4 back: the end)
16: addq.w #1,0x%(count)X+6
    subq.w #1,0x%(count)X+8
    bpl 12b
18: movem.l (%%sp)+,%%d1/%%d3-%%d6/%%a2
    rts
cuts:
    .word %(cuts)s
""" % {"stages": stages, "ram": RAM, "first": SHORE_SPRITES, "max": SHORE_MAX, "line_y": LINE_Y,
       "into_l": INTO_L, "into_r": INTO_R, "n_cuts": len(CUTS), "land_first": LAND[0], "land_last": LAND[1], "land_mid": (LAND[0] + LAND[1]) // 2, "half": SHORE_MAX // 2,
       "open_palettes": "".join("    cmpi.b #0x%X,%%d3\n    beq 4f\n" % p for p in OPEN_PALETTES),
       "span_tiles": SPAN_TILES, "span_index": span_index, "span_rows": span_rows,
       "cuts": ",".join("0x%X" % t for t in tiles), "column_x": COLUMN_X, "water_near": WATER_NEAR, "slot_col": SLOT_COL, "count": COUNT, "columns": WATER_COLUMNS, "original": original},
        why="water tint: the wave line over the shore")
    rom.write(SHORE_HOOK, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + original.to_bytes(4, "big"),
              why="each frame, after the layers are placed: the wave line over the shore first")

def apply(rom):
    if SHORE:
        shore_line(rom, line_tiles(rom))
    if not TINT_K:
        return                          # (no tint: the palettes left alone)
    original_vblank = rom.u32(0x64)
    original_timer = rom.u32(0x68)
    k = int(TINT_K * 256)
    stage_code = ""
    tables = ""
    for i, (stage, (water, (lo, hi), dy, entries, water_pal)) in enumerate(sorted(STAGES.items())):
        addrs = [0x400000 + pal * 32 + e * 2 for pal, es in sorted(entries.items()) for e in es]
        assert len(addrs) <= MAX_ENTRIES, stage
        tables += "addrs%d:\n    .long %s\n" % (i, ",".join("0x%X" % a for a in addrs))
        stage_code += r"""
    cmpi.b #%(stage)d,0x%(stage_at)X
    bne 9%(i)df
    lea addrs%(i)d(%%pc),%%a0
    moveq #%(count)d,%%d7
    move.w #%(water)d*64,%%d6           | d6: the water layer's first sprite's tiles
    move.w #0x8200+%(water)d,%%d5
    move.l #0x%(range)X,%%d4
    move.w #%(dy)d,%%d3
    move.w #%(water_pal)d,%%d2
    bra found_stage
9%(i)d:""" % {"i": i, "stage": stage, "stage_at": STAGE_AT, "count": len(addrs), "water": water, "lo": lo, "hi": hi,
              "dy": dy, "water_pal": water_pal, "range": lo << 16 | hi}
    code = rom.place_code(r"""
    bra.w vblank
    bra.w timer

| ---- each vblank: the originals back, then (a stage with water) the line found, the tint made, the timer armed
vblank:
    movem.l %%d0-%%d7/%%a0-%%a3,-(%%sp)
    tst.b 0x%(ram)X+1                   | (tinted last frame: the originals back)
    beq 1f
    clr.b 0x%(ram)X+1
    move.w 0x%(ram)X+2,%%d0
    lea 0x%(save)X,%%a1
    lea 0x%(addrs)X,%%a2
    lea 0x%(tinted)X,%%a3
    subq.w #1,%%d0
0:  movea.l (%%a2)+,%%a0
    move.w (%%a1)+,%%d1
    move.w (%%a0),%%d2
    cmp.w (%%a3)+,%%d2                  | (only where it's still the tint: the game may have put in new colours -
    bne 16f                             | coming out of a shop - and they stay)
    move.w %%d1,(%%a0)
16: dbf %%d0,0b
1:  clr.b 0x%(ram)X                     | not armed
    andi.w #0xFF0F,0x%(mode)X           | (timer off unless armed below)
%(stage_code)s
    bra done

| a0 = the stage's palette entries (addresses), d7 = how many; d6 / d5 = the water layer's tiles / y-height word;
| d4 = the surface tiles' range; d3 = the split's dy; d2 = the water's palette
found_stage:
    move.w %%d7,0x%(ram)X+2
    lea 0x%(addrs)X,%%a1                | (the entries' addresses noted, for the restore)
    move.w %%d7,%%d0
    subq.w #1,%%d0
2:  move.l (%%a0)+,(%%a1)+
    dbf %%d0,2b
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w %%d5,0x3C0000                | the water layer's y
    move.w 0x3C0002,%%d1
    lsr.w #7,%%d1
    neg.w %%d1
    add.w #496,%%d1                     | d1 = its top's screen y
    moveq #31,%%d0                      | its row of surface tiles
3:  move.w %%d6,0x3C0000
    move.w 0x3C0002,%%d5
    swap %%d4
    cmp.w %%d4,%%d5
    swap %%d4
    bcs 4f
    cmp.w %%d4,%%d5
    bhi 4f
    bra 5f
4:  add.w #2,%%d6
    add.w #16,%%d1
    dbf %%d0,3b
    | (no surface row on screen: under water if the layer's tile at mid-screen is in the water's palette)
    move.w %%d5,0x3C0000
    move.w 0x3C0002,%%d1
    lsr.w #7,%%d1
    neg.w %%d1
    add.w #496,%%d1                     | its top's screen y
    move.w #112,%%d0
    sub.w %%d1,%%d0
    and.w #511,%%d0
    lsr.w #4,%%d0                       | the row at screen y 112
    add.w %%d0,%%d0
    sub.w #64,%%d6                      | (back to the sprite's first tile: the loop went 32 rows on)
    add.w %%d0,%%d6
    addq.w #1,%%d6
    move.w %%d6,0x3C0000
    move.w 0x3C0002,%%d0
    move.w (%%sp)+,%%sr
    lsr.w #8,%%d0
    cmp.w %%d2,%%d0
    beq whole
    bra done
5:  move.w (%%sp)+,%%sr
    and.w #511,%%d1
    cmp.w #400,%%d1                     | (just above the top: negative)
    blt 51f
    sub.w #512,%%d1
51: add.w %%d3,%%d1                     | d1 = the split line
    cmp.w #224,%%d1
    bge done                            | (below the screen: nothing)
    tst.w %%d1
    ble whole
    bsr make_tint
    add.w #%(to_top)d,%%d1              | the timer: (lines from the vblank) x 384 pixel clocks
    mulu #384,%%d1
    swap %%d1
    move.w %%d1,0x3C0008
    swap %%d1
    move.w %%d1,0x3C000A
    ori.w #%(bits)d,0x%(mode)X
    st 0x%(ram)X
    bra done
whole:
    bsr make_tint
    bsr put_tint
done:
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a3
    jmp 0x%(original_vblank)X

| the originals saved and the tinted copies made (k/256 toward TINT_TO)
make_tint:
    movem.l %%d0-%%d7/%%a0-%%a3,-(%%sp)
    move.w 0x%(ram)X+2,%%d7
    subq.w #1,%%d7
    lea 0x%(addrs)X,%%a2
    lea 0x%(save)X,%%a1
    lea 0x%(tinted)X,%%a0
6:  movea.l (%%a2)+,%%a3
    move.w (%%a3),%%d0
    move.w %%d0,(%%a1)+
    move.w %%d0,%%d1                    | r: bits 11-8 and 14
    lsr.w #7,%%d1
    and.w #0x1E,%%d1
    btst #14,%%d0
    beq 7f
    addq.w #1,%%d1
7:  moveq #%(tr)d,%%d2
    bsr blend
    move.w %%d1,%%d3
    move.w %%d0,%%d1                    | g: bits 7-4 and 13
    lsr.w #3,%%d1
    and.w #0x1E,%%d1
    btst #13,%%d0
    beq 8f
    addq.w #1,%%d1
8:  moveq #%(tg)d,%%d2
    bsr blend
    move.w %%d1,%%d4
    move.w %%d0,%%d1                    | b: bits 3-0 and 12
    add.w %%d1,%%d1
    and.w #0x1E,%%d1
    btst #12,%%d0
    beq 10f
    addq.w #1,%%d1
10: moveq #%(tb)d,%%d2
    bsr blend
    move.w %%d1,%%d5
    and.w #0x8000,%%d0                  | packed again (the dark bit kept)
    move.w %%d3,%%d1
    lsr.w #1,%%d1
    lsl.w #8,%%d1
    or.w %%d1,%%d0
    move.w %%d4,%%d1
    lsr.w #1,%%d1
    lsl.w #4,%%d1
    or.w %%d1,%%d0
    move.w %%d5,%%d1
    lsr.w #1,%%d1
    or.w %%d1,%%d0
    btst #0,%%d3
    beq 11f
    bset #14,%%d0
11: btst #0,%%d4
    beq 12f
    bset #13,%%d0
12: btst #0,%%d5
    beq 13f
    bset #12,%%d0
13: move.w %%d0,(%%a0)+
    dbf %%d7,6b
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a3
    rts
blend:                                  | d1 = d1 + (d2 - d1) x k / 256
    sub.w %%d1,%%d2
    muls #%(k)d,%%d2
    asr.l #8,%%d2
    add.w %%d2,%%d1
    rts

| the tinted colours into the palettes
put_tint:
    movem.l %%d0/%%a0-%%a2,-(%%sp)
    move.w 0x%(ram)X+2,%%d0
    subq.w #1,%%d0
    lea 0x%(tinted)X,%%a0
    lea 0x%(addrs)X,%%a1
14: movea.l (%%a1)+,%%a2
    move.w (%%a0)+,(%%a2)
    dbf %%d0,14b
    st 0x%(ram)X+1
    movem.l (%%sp)+,%%d0/%%a0-%%a2
    rts

| ---- the timer interrupt: armed - the tint on; else the game's own handler
timer:
    move.w #2,0x3C000C                  | (acknowledged)
    tst.b 0x%(ram)X
    bne 15f
    rte                                 | (not ours: the game never turns the timer on itself - its own handler,
15:                                     | 0x9A0A, reloads it every 0x2FF clocks, so it can't run here)
    clr.b 0x%(ram)X
    move.l %%d0,-(%%sp)
    move.w 0x3C0006,%%d0                | (debug: the line it hit)
    lsr.w #7,%%d0
    move.w %%d0,0x%(ram)X+4
    move.l (%%sp)+,%%d0
    bsr put_tint
    rte

%(tables)s""" % {"ram": RAM, "save": SAVE, "tinted": TINTED_COLOURS, "addrs": ADDRS, "mode": MODE_COPY,
                 "stage_code": stage_code, "to_top": LINES_TO_TOP, "bits": TIMER_BITS,
                 "original_vblank": original_vblank, "original_timer": original_timer, "k": k,
                 "tr": TINT_TO[0], "tg": TINT_TO[1], "tb": TINT_TO[2], "tables": tables},
        why="water tint: the colours below the water line")
    rom.write(GAME_TIMER_WRITE, bytes.fromhex("4E714E714E714E71"), expect=bytes.fromhex("33FC3C00003C000A"),
              why="vblank: the game's (unused) timer reload skipped - the water tint's timer is set here")
    rom.write(0x64, code.to_bytes(4, "big"), expect=original_vblank.to_bytes(4, "big"),
              why="vblank: the water tint's set-up first")
    rom.write(0x68, (code + 4).to_bytes(4, "big"), expect=original_timer.to_bytes(4, "big"),
              why="timer interrupt: the water tint")
