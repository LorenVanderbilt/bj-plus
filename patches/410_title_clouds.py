NAME = "title-clouds"
DESCRIPTION = "Title screen: the clouds drift slowly by behind the logo and cliffs (parallax)"

# The title's background (sta/aes/how_to_play.sta) is one 21-sprite chain from sprite 100 (sky, clouds, cliffs,
# waterfall; the foliage is another from 200, the logo sprites after it). Its rows 18-22 - the screen's top 80 px -
# are a plain sky tile (0x2A51) and cloud tiles painted on that sky, so a cloud tile can slide sideways over the sky
# without showing an edge. Now those rows (BANDS: one band) are drawn again, every frame, by a chain of sprites
# of its own (drawn after the background, before the foliage and logo) whose tiles are the
# background's (but PLAIN): scrolled left PIXELS px every FRAMES frames, looping over LOOP's columns (each a background column,
# maybe flipped). Two chains take turns (double buffering): the tiles are written only when the scroll reaches a
# new column, into the hidden chain, which is then shown and the other hidden in one go - rewriting the shown
# chain's tiles while the screen was being drawn made the band jump 16 px for a frame now and then. Hooked on the title loop's per-frame call
# (0x1AF94, title-menu's menu_frame) and on its end (0x1B026, title-menu's title_leave), where the bands are hidden
# and their count reset (so the next title starts as drawn).
FRAME_CALL = 0x1AF94         # jsr (title-menu's menu_frame)
LEAVE_CALL = 0x1B026         # jsr (title-menu's title_leave)
BACKGROUND = 100             # the background chain's first sprite (column 0 at x 0)
COLUMNS = 20
CHAIN = 21                   # 320 px and one to spare
CHAINS = (150, 171)          # the two chains (21 sprites each)
ROW, ROWS, Y = 18, 5, 0      # the background rows (the whole sky: two bands at different speeds tore the big
                             # clouds, which span all five), screen y
PIXELS, FRAMES = 1, 4        # the drift: PIXELS px every FRAMES frames
START_PX = 0                 # the sky starts this far right of where the title draws it
SKY = [   # the background's rows 18-22, columns 0-19 (tile numbers; attributes ATTR)
    [0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2B83, 0x2B84, 0x2B85, 0x2B86, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2B87, 0x2B88],
    [0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2A51, 0x2B80, 0x2B81, 0x2B82, 0x2A51, 0x2B89, 0x2B8A, 0x2B8B, 0x2B8C, 0x2B8D, 0x2B8E, 0x2B8F, 0x2B90, 0x2B91, 0x2B92],
    [0x2A58, 0x2A59, 0x2A5A, 0x2A5B, 0x2A5C, 0x2A5D, 0x2A5E, 0x2A5F, 0x2A70, 0x2A71, 0x2B93, 0x2B94, 0x2B95, 0x2B96, 0x2B97, 0x2B98, 0x2B99, 0x2B9A, 0x2B9B, 0x2B9C],
    [0x2A60, 0x2A61, 0x2A62, 0x2A63, 0x2A64, 0x2A65, 0x2A66, 0x2A67, 0x2A78, 0x2A79, 0x2B9D, 0x2B9E, 0x2B9F, 0x2BA0, 0x2BA1, 0x2BA2, 0x2BA3, 0x2BA4, 0x2BA5, 0x2BA6],
    [0x2A68, 0x2A69, 0x2A6A, 0x2BAA, 0x2BAB, 0x2BAC, 0x2A6C, 0x2A6D, 0x2A6E, 0x2A6F, 0x2BA7, 0x2BA8, 0x2BA9, 0x2A6B, 0x2A6B, 0x2A6B, 0x2A6B, 0x2A72, 0x2A73, 0x2A74],
]
ATTR = 0xF400                # palette 0xF4
PLAIN = {(4, 17): 0x2A6B, (4, 18): 0x2A6B, (4, 19): 0x2A6B}   # (row, column): plain haze instead - the right
                             # cloud's bottom, whose lower edge is painted into the (still) cliff row below: drifting
                             # off, it showed as a thin flat-bottomed sliver
# The loop's mirrored join runs through the right cloud's last column (19). ART (if there) is a hand-edited picture
# of the sky's columns ART_COLUMNS (tools/export_title_sky.py writes the starting one: indexed, in palette 0xF4 -
# PALETTE): each 16x16 tile in it that differs from the tile there becomes a new sprite tile, drawn instead.
ART = "art/title_sky.png"
ART_COLUMNS = range(15, 20)
PALETTE = [0x3060, 0xB06E, 0xB05E, 0xB04E, 0xB03E, 0x803E, 0xB00D, 0x800D, 0x7FFF, 0x7FFF, 0x7CDF, 0x1ACF, 0x67AF,
           0xA59F, 0xD28E, 0x8000]   # 0xF4 as the title has it


def find_tile(rom, px):
    """[the number of an identical tile anywhere in the original sprite ROMs] or []."""
    planes = []
    for blk in range(4):                 # (hackbuild's sprite_tile layout, encoded)
        bx, by = (8 if blk < 2 else 0), (0 if blk % 2 == 0 else 8)
        for y in range(8):
            row = px[by + y][bx:bx + 8]
            planes.append([sum(((v >> k) & 1) << x for x, v in enumerate(row)) for k in range(4)])
    a = bytes(b for p in planes for b in (p[0], p[1]))
    b = bytes(b for p in planes for b in (p[2], p[3]))
    for pair, base in ((0, 0), (2, rom.SPRITE_TILES_PER_PAIR)):
        A = rom.sprites_orig[sorted(rom.sprites_orig)[pair]]
        B = rom.sprites_orig[sorted(rom.sprites_orig)[pair + 1]]
        at = A.find(a)
        while at >= 0:
            if at % 64 == 0 and B[at:at + 64] == b:
                return [base + at // 64]
            at = A.find(a, at + 1)
    return []


def shown(r, c):
    """The tile the sky shows at row r, column c (before ART)."""
    return PLAIN.get((r, c), SKY[r][c])


LOOP = [(c, 0) for c in range(COLUMNS)] + [(c, 1) for c in reversed(range(COLUMNS))]   # (column, flipped)
COUNT = 0x10E82A             # (word) frames on the title
SHOWN_COL = 0x10E82C         # (word) the loop column the shown chain starts at, + 1 (0: none yet)
SHOWN = 0x10E82E             # (byte) which chain is shown
H_FLIP = 1                   # (tile attribute bit)


def apply(rom):
    frame_before = rom.u32(FRAME_CALL + 2)
    leave_before = rom.u32(LEAVE_CALL + 2)
    tiles = {}
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ART)
    if os.path.exists(path):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(path), "..", "tools"))
        from png_tiles import read_indices
        from export_title_sky import rgb
        art = read_indices(path, [rgb(w) for w in PALETTE])
        existing = sorted({t for row in SKY for t in row} | set(PLAIN.values()))
        for r in range(ROWS):
            for k, c in enumerate(ART_COLUMNS):
                px = [art[r * 16 + y][k * 16:k * 16 + 16] for y in range(16)]
                if px == rom.sprite_tile(shown(r, c)):
                    continue
                same = [t for t in existing if rom.sprite_tile(t) == px] or find_tile(rom, px)
                tiles[(r, c)] = same[0] if same else rom.add_sprite_tile(     # (an existing tile: free)
                    px, why="title clouds: %s, row %d column %d" % (ART, r, c), share=True)
    loop = ",".join("0x%04X" % (c * 2 * ROWS | flip << 15) for c, flip in LOOP)
    sky = ",".join("0x%04X" % tiles.get((r, c), shown(r, c)) for c in range(COLUMNS) for r in range(ROWS))
    hides = "".join("    move.w #0x8200+%d,0x3C0000\n    move.w #0,0x3C0002\n" % c for c in CHAINS)
    code = rom.place_code(r"""
    bra.w frame
    bra.w leave

frame:
    jsr 0x%(frame_before)X
    movem.l %%d0-%%d7/%%a0-%%a1,-(%%sp)
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004                  | (VRAM writes step by 1)
    moveq #0,%%d0                       | d0 = px scrolled, round the loop
    move.w 0x%(count)X,%%d0
    mulu #%(pixels)d,%%d0
    divu #%(frames)d,%%d0
    and.l #0xFFFF,%%d0
    add.l #%(start)d,%%d0               | (from START_PX)
    divu #%(loop_px)d,%%d0
    swap %%d0
    move.w %%d0,%%d4                    | d4 = the fine x (0-15)
    and.w #15,%%d4
    neg.w %%d4
    and.w #511,%%d4
    lsl.w #7,%%d4
    lsr.w #4,%%d0                       | d0 = the first loop column
    lea chains(%%pc),%%a1               | a1 -> the shown chain's first sprite
    tst.b 0x%(shown)X
    beq 1f
    addq.l #2,%%a1
1:  move.w %%d0,%%d1                    | (stored + 1: 0 = none drawn yet)
    addq.w #1,%%d1
    cmp.w 0x%(shown_col)X,%%d1
    beq 9f                              | (the same column: just the x)
    move.w %%d1,0x%(shown_col)X
    eori.b #1,0x%(shown)X               | the hidden chain: a1 -> it
    lea chains(%%pc),%%a1
    tst.b 0x%(shown)X
    beq 2f
    addq.l #2,%%a1
2:  move.w (%%a1),%%d5                  | d5 = its sprite's tiles
    lsl.w #6,%%d5
    moveq #%(chain)d-1,%%d6
3:  move.w %%d0,%%d1                    | the loop column: its sky column's tiles, flipped?
    add.w %%d1,%%d1
    lea loop(%%pc),%%a0
    move.w (%%a0,%%d1.w),%%d1
    move.w #%(attr)d,%%d3
    tst.w %%d1
    bpl 4f
    eor.w #%(flip)d,%%d3
    and.w #0x7FFF,%%d1
4:  lea sky(%%pc),%%a0
    adda.w %%d1,%%a0
    move.w %%d5,0x3C0000
    moveq #%(rows)d-1,%%d7
5:  move.w (%%a0)+,0x3C0002             | tile, attributes
    move.w %%d3,0x3C0002
    dbf %%d7,5b
    move.w %%d5,%%d2                    | full size; chained to the one before (not the first)
    lsr.w #6,%%d2
    move.w %%d2,%%d1
    add.w #0x8000,%%d2
    move.w %%d2,0x3C0000
    move.w #0x0FFF,0x3C0002
    cmp.w (%%a1),%%d1
    beq 6f
    add.w #0x8200,%%d1
    move.w %%d1,0x3C0000
    move.w #0x40,0x3C0002
6:  add.w #64,%%d5
    addq.w #1,%%d0                      | the next loop column
    cmp.w #%(loop_cols)d,%%d0
    bcs 7f
    moveq #0,%%d0
7:  dbf %%d6,3b
    move.w (%%a1),%%d1                  | its x, then shown and the other hidden
    add.w #0x8400,%%d1
    move.w %%d1,0x3C0000
    move.w %%d4,0x3C0002
    move.w (%%a1),%%d1
    add.w #0x8200,%%d1
    move.w %%d1,0x3C0000
    move.w #%(scb3)d,0x3C0002
    lea chains(%%pc),%%a0
    move.w (%%a0),%%d1
    cmp.w (%%a1),%%d1
    bne 8f
    move.w 2(%%a0),%%d1
8:  add.w #0x8200,%%d1
    move.w %%d1,0x3C0000
    move.w #%(scb3_hidden)d,0x3C0002   | (height 0, its y kept: a line being drawn as it's hidden still
                                        | takes the right row - with y 0 it took the one 16 px down)
    bra 10f
9:  move.w (%%a1),%%d1                  | the shown chain's x
    add.w #0x8400,%%d1
    move.w %%d1,0x3C0000
    move.w %%d4,0x3C0002
10: move.w (%%sp)+,%%sr
    addq.w #1,0x%(count)X
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a1
    rts

leave:
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
%(hides)s
    move.w (%%sp)+,%%sr
    clr.w 0x%(count)X
    clr.w 0x%(shown_col)X
    jmp 0x%(leave_before)X

chains:
    .word %(chain_a)d,%(chain_b)d
loop:
    .word %(loop)s
sky:
    .word %(sky)s
""" % {"frame_before": frame_before, "leave_before": leave_before, "hides": hides, "count": COUNT,
       "pixels": PIXELS, "frames": FRAMES, "loop_px": 16 * len(LOOP), "start": (-START_PX) % (16 * len(LOOP)), "loop_cols": len(LOOP), "shown": SHOWN, "shown_col": SHOWN_COL,
       "chain": CHAIN, "flip": H_FLIP, "row": ROW, "rows": ROWS, "scb3": ((496 - Y) & 511) << 7 | ROWS,
       "chain_a": CHAINS[0], "chain_b": CHAINS[1], "loop": loop, "sky": sky, "attr": ATTR,
       "scb3_hidden": ((496 - Y) & 511) << 7},
        why="title screen: drifting clouds")
    rom.write(FRAME_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + frame_before.to_bytes(4, "big"), why="title: the clouds every frame")
    rom.write(LEAVE_CALL, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + leave_before.to_bytes(4, "big"), why="title: the clouds hidden as it ends")
