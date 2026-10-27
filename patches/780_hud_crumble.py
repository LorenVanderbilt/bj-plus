import random

NAME = "hud-crumble"
DESCRIPTION = "Goal: the HUD crumbles away upwards (a ragged edge eating up each part, flecks drifting off) instead of switching off"

# At the goal the HUD went at once: `hud` hides it from the frame a hero grabs the goal (state GOAL_STATE) - every part
# clears its cells. Now, that frame, the HUD (its routine: HUD_ENTRY, hud's code) is skipped for STEPS frames instead -
# frozen as it was - while its cells are cleared a few at a time: each band (the top lines, ROWS_TOP; the item bar,
# ROWS_BAR) from its bottom row up, each column a little early or late (JITTER) so the edge is ragged. Each cell that
# had something in it (BLANKS: the fix tiles that are blank, from the S ROM) throws off a fleck: a cluster of specks
# (CLUSTERS, three patterns by the cell's column) in the HUD font's palette (PALETTE) - white, or its dark greys on a
# level whose background behind the HUD is light (LIGHT_AREAS) - drifting up and a little sideways, thinned out at its
# end (FLECK_THIN), gone after FLECK_LIFE frames. Then `hud` runs again and hides the HUD as before (its cells clear).
# The flecks aren't objects: objects are drawn before a level's front layer (the marsh's vine covered them), and each
# one's run and draw made the goal's sprites late (the bells tore - four at most were safe). Each is a sprite of its
# own, slots FLECK_SLOT on (above anything the game draws in play - drawn last, in front of everything; the pause's
# bubble borrows the first while paused), moved here each frame - at the HUD's turn, early in the frame - its state in
# FLECKS (8 bytes each: y, x in 1/16 px, rise, drift, age, its tiles; age 0: free).
HUD_ENTRY = 0x4E4B8            # jsr <hud's frame code> ; nop
NO_HUD = 0x10309B              # (the game's own: no HUD at all)
HIDDEN = 0x10E9FE              # (hud's: the HUD hidden)
HEROES = [0x104068, 0x1040E8]  # (each hero's state byte)
GOAL_STATE = 45
AREA = 0x103005
ROWS_TOP = range(2, 8)         # (fix rows: the score line to the hearts)
ROWS_BAR = range(25, 30)       # (the item bar)
COLUMNS = range(40)
STEPS = 26                     # frames, all told
JITTER = 4                     # frames a column may be early or late
BLANK_CELL = 0x0520            # (hud's blank)
FRAME_COUNT, NEXT = 0x10E8D0, 0x10E8D2     # spare RAM: the step (0: not crumbling), the next cell's entry (long)
FLECKS, FLECK_COUNT = 0x10E700, 32         # spare RAM (to 0x10E7FF: hero-big-art's debug marks only, off)
FLECK_SLOT = 300               # (sprite slots: FLECK_SLOT on)
PALETTE = 5                    # (the HUD font's: 1 white, 2-4 light greys, 12-15 dark greys)
SPECK = [[1, 2], [2, 3]]       # (a speck: 2 x 2 - palette 5's whites)
DARK = {1: 15, 2: 14, 3: 12}   # (its dark greys instead: on a light level)
CLUSTERS = [[(5, 3), (10, 5), (3, 8), (8, 9), (12, 12)],            # (each fleck: specks at these spots in its 16 x 16
            [(8, 2), (3, 6), (11, 7), (6, 11), (13, 13)],           # tile)
            [(4, 4), (12, 3), (8, 8), (2, 12), (10, 13)]]
LIGHT_AREAS = [0x03, 0x06, 0x07, 0x09, 0x0A, 0x0B, 0x18, 0x1B]     # (areas, AREA, whose background behind the HUD is
                               # light - the median of the screen's top band 100 or more, 2026-10-20: dark specks there)
FLECK_LIFE, FLECK_THIN = 18, 11    # (frames; thinned out from this one on)
RISE = (14, 30)                # (1/16 px a frame up: the slowest, the fastest)
DRIFT = 7                      # (1/16 px a frame sideways, at most, either way)


def schedule():
    """[(step, fix address)] for every cell of the two bands: bottom row first, up to the top, each column jittered."""
    rnd = random.Random(5)
    jitter = {c: rnd.uniform(0, JITTER) for c in COLUMNS}
    out = []
    for rows in (ROWS_TOP, ROWS_BAR):
        lo, hi = max(rows), min(rows)
        for c in COLUMNS:
            for r in rows:
                t = (lo - r) / max(1, lo - hi) * (STEPS - JITTER - 3) + jitter[c] + rnd.uniform(0, 2)
                out.append((1 + int(t), 0x7000 + c * 32 + r))
    return sorted(out)


def fleck_tiles(rom):
    """[(tile, thinned tile)] for each cluster: white ones, then dark ones."""
    out = []
    for dark in (False, True):
        for k, spots in enumerate(CLUSTERS):
            pair = []
            for thin in (False, True):
                px = [[0] * 16 for _ in range(16)]
                for n, (sx, sy) in enumerate(spots):
                    if thin and n % 2:
                        continue                               # (thinned out: every other speck gone, the rest halved)
                    for y in range(2):
                        for x in range(2):
                            if not thin or (x + y) % 2 == 0:
                                v = SPECK[y][x]
                                px[sy + y][sx + x] = DARK[v] if dark else v
                pair.append(rom.add_sprite_tile(px, why="HUD crumble: flecks %d%s%s" % (
                    k, " dark" if dark else "", " (thinned)" if thin else "")))
            out.append(tuple(pair))
    return out


def apply(rom):
    assert rom.u16(HUD_ENTRY) == 0x4EB9 and rom.u16(HUD_ENTRY + 6) == 0x4E71, "hud-crumble: needs hud's HUD_ENTRY hook"
    hud = rom.u32(HUD_ENTRY + 2)
    fix = rom.fix
    blanks = bytearray(len(fix) // 32 // 8)
    for t in range(len(fix) // 32):
        if not any(fix[t * 32:t * 32 + 32]):
            blanks[t >> 3] |= 1 << (t & 7)
    tiles = fleck_tiles(rom)
    n_clusters = len(CLUSTERS)
    pick = [(c % 4) % n_clusters for c in range(4)]             # (the column's two low bits -> its cluster)
    cells = schedule()
    rnd = random.Random(9)
    rises = [rnd.randint(*RISE) for _ in range(16)]
    drifts = [rnd.randint(-DRIFT, DRIFT) for _ in range(16)]
    code = rom.place_code("""
    bsr flecks                          | (the flecks: every frame, while any are out)
    tst.b 0x%(no_hud)X                  | (no HUD: as it was)
    bne 8f
    tst.w 0x%(count)X                   | crumbling?
    bne step
    tst.b 0x%(hidden)X                  | (already hidden: as it was)
    bne 8f
    cmpi.b #%(goal)d,0x%(hero1)X        | a hero grabbing the goal: the crumble starts
    beq 1f
    cmpi.b #%(goal)d,0x%(hero2)X
    bne 8f
1:  move.w #1,0x%(count)X
    move.l #cells,0x%(next)X
step:
    movem.l %%d0-%%d7/%%a0-%%a2,-(%%sp)
    movea.l 0x%(next)X,%%a0
    move.w 0x%(count)X,%%d7
2:  cmp.w (%%a0),%%d7                   | the cells due now
    bcs 4f
    move.w 2(%%a0),%%d1
    addq.l #4,%%a0
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w %%d1,0x3C0000
    move.w 0x3C0002,%%d0                | what's in it
    move.w %%d1,0x3C0000
    move.w #0x%(blank)X,0x3C0002        | gone
    move.w (%%sp)+,%%sr
    andi.w #0x0FFF,%%d0                 | (blank: nothing to throw off)
    move.w %%d0,%%d2
    lsr.w #3,%%d2
    lea blanks(%%pc),%%a1
    move.b (%%a1,%%d2.w),%%d3
    andi.w #7,%%d0
    btst %%d0,%%d3
    bne 2b
    bsr spawn
    bra 2b
4:  move.l %%a0,0x%(next)X
    addq.w #1,%%d7
    cmpi.w #%(total)d,%%d7
    bhi 7f
    move.w %%d7,0x%(count)X
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a2
    addq.l #4,%%sp                      | (the HUD's routine skipped: the rest stays as it was)
    rts
7:  clr.w 0x%(count)X                   | (done: hud hides the HUD from here, as before - this frame)
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a2
8:  jmp 0x%(hud)X

| a fleck from the cell d1 (its fix address): the first free one, if any
spawn:
    lea 0x%(flecks)X,%%a1
    moveq #%(n)d-1,%%d2
1:  tst.b 6(%%a1)
    beq 2f
    addq.l #8,%%a1
    dbf %%d2,1b
    rts
2:  move.w %%d1,%%d0                    | its place: on the cell's middle (column = (address - 0x7000) / 32, row)
    subi.w #0x7000,%%d0
    move.w %%d0,%%d3
    lsr.w #5,%%d0
    andi.w #31,%%d3
    lsl.w #3,%%d0
    subq.w #4,%%d0
    lsl.w #4,%%d0
    move.w %%d0,2(%%a1)                 | x (1/16 px: the sprite's left)
    subq.w #2,%%d3
    lsl.w #3,%%d3
    subq.w #4,%%d3
    lsl.w #4,%%d3
    move.w %%d3,(%%a1)                  | y (its top)
    move.w %%d1,%%d0                    | its rise and drift: from the address
    andi.w #15,%%d0
    lea rises(%%pc),%%a2
    move.b (%%a2,%%d0.w),4(%%a1)
    move.w %%d1,%%d0
    lsr.w #5,%%d0
    andi.w #15,%%d0
    lea drifts(%%pc),%%a2
    move.b (%%a2,%%d0.w),5(%%a1)
    move.b #1,6(%%a1)
    move.w %%d1,%%d0                    | its cluster: the column's; dark on a light level
    lsr.w #5,%%d0
    andi.w #3,%%d0
    lea pick(%%pc),%%a2
    move.b (%%a2,%%d0.w),%%d0
    moveq #0,%%d3
    move.b 0x%(area)X,%%d3
    andi.w #63,%%d3
    lea light(%%pc),%%a2
    tst.b (%%a2,%%d3.w)
    beq 3f
    addq.b #%(n_clusters)d,%%d0
3:  move.b %%d0,7(%%a1)
    moveq #%(n)d-1,%%d0                 | (its sprite: its tile, full size)
    sub.w %%d2,%%d0
    addi.w #%(slot)d,%%d0
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
    move.w %%d0,%%d3
    lsl.w #6,%%d3
    move.w %%d3,0x3C0000
    moveq #0,%%d3
    move.b 7(%%a1),%%d3
    add.w %%d3,%%d3
    add.w %%d3,%%d3
    lea fleck_tiles(%%pc),%%a2
    move.w (%%a2,%%d3.w),0x3C0002
    move.w #0x%(attr)X,0x3C0002
    addi.w #0x8000,%%d0
    move.w %%d0,0x3C0000
    move.w #0x0FFF,0x3C0002
    move.w (%%sp)+,%%sr
    rts

| the flecks out: each a frame older - risen, drifted, thinned, or gone
flecks:
    movem.l %%d0-%%d4/%%a1-%%a2,-(%%sp)
    lea 0x%(flecks)X,%%a1
    move.w #%(slot)d,%%d4
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
1:  tst.b 6(%%a1)
    beq 9f
    addq.b #1,6(%%a1)
    cmpi.b #%(life)d,6(%%a1)
    bcs 2f
    clr.b 6(%%a1)                       | gone: its sprite hidden
    move.w %%d4,%%d0
    addi.w #0x8200,%%d0
    move.w %%d0,0x3C0000
    move.w #0,0x3C0002
    bra 9f
2:  cmpi.b #%(thin)d,6(%%a1)            | thinned out
    bne 3f
    move.w %%d4,%%d0
    lsl.w #6,%%d0
    move.w %%d0,0x3C0000
    moveq #0,%%d3
    move.b 7(%%a1),%%d3
    add.w %%d3,%%d3
    add.w %%d3,%%d3
    lea fleck_tiles+2(%%pc),%%a2
    move.w (%%a2,%%d3.w),0x3C0002
3:  moveq #0,%%d0                       | risen
    move.b 4(%%a1),%%d0
    sub.w %%d0,(%%a1)
    move.b 5(%%a1),%%d0                 | drifted
    ext.w %%d0
    add.w %%d0,2(%%a1)
    move.w %%d4,%%d0                    | its place: SCB3 (496 - y, one tile tall), SCB4 (x)
    addi.w #0x8200,%%d0
    move.w %%d0,0x3C0000
    move.w (%%a1),%%d1
    asr.w #4,%%d1
    move.w #496,%%d2
    sub.w %%d1,%%d2
    andi.w #0x1FF,%%d2
    lsl.w #7,%%d2
    addq.w #1,%%d2
    move.w %%d2,0x3C0002
    addi.w #0x200,%%d0
    move.w %%d0,0x3C0000
    move.w 2(%%a1),%%d1
    asr.w #4,%%d1
    andi.w #0x1FF,%%d1
    lsl.w #7,%%d1
    move.w %%d1,0x3C0002
9:  addq.l #8,%%a1
    addq.w #1,%%d4
    cmpi.w #%(slot)d+%(n)d,%%d4
    bcs 1b
    move.w (%%sp)+,%%sr
    movem.l (%%sp)+,%%d0-%%d4/%%a1-%%a2
    rts

fleck_tiles:
    .word %(tiles)s
rises:
    .byte %(rises)s
drifts:
    .byte %(drifts)s
pick:
    .byte %(pick)s
light:
    .byte %(light)s
    .even
cells:
    .word %(cells)s
    .word 0xFFFF,0
blanks:
    .byte %(blanks)s
    .even
""" % {"no_hud": NO_HUD, "count": FRAME_COUNT, "hidden": HIDDEN, "goal": GOAL_STATE, "hero1": HEROES[0],
       "hero2": HEROES[1], "next": NEXT, "blank": BLANK_CELL, "total": max(t for t, _ in cells), "hud": hud,
       "flecks": FLECKS, "n": FLECK_COUNT, "slot": FLECK_SLOT, "attr": PALETTE << 8, "life": FLECK_LIFE,
       "thin": FLECK_THIN, "tiles": ",".join("0x%X,0x%X" % t for t in tiles), "area": AREA, "n_clusters": n_clusters,
       "rises": ",".join(str(r) for r in rises), "drifts": ",".join(str(d & 0xFF) for d in drifts),
       "pick": ",".join(str(p) for p in pick),
       "light": ",".join("1" if a in LIGHT_AREAS else "0" for a in range(64)),
       "cells": ",".join("%d,0x%X" % c for c in cells), "blanks": ",".join("0x%02X" % b for b in blanks)},
        why="HUD crumble: at the goal, the HUD crumbles away upwards")
    rom.write(HUD_ENTRY + 2, code.to_bytes(4, "big"), expect=hud.to_bytes(4, "big"),
              why="HUD: at the goal, crumbling first")
