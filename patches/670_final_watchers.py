NAME = "final-watchers"
DESCRIPTION = "Final fight: dinosaurs watching from the throne hall's balconies - they hop in horror when the boss is hit"

import os

# The throne hall of the final fight (stage STAGE) is one layer of full-height strips (sprites 23-43, 16 px apart,
# tile row r at y 16 * (r - 18)), and the floor is another (100-120). Sprites between them are drawn in front of the
# hall and behind the floor and the fight. The game fills them from 44 up as the fight needs (the boss's spinning
# blades use 45-50), so the watchers take the top ones, FIRST_SLOT to LAST_SLOT. They're drawn each frame of play in
# the hall (DRAW_CALL, after the game and elevator-spin have drawn their sprites). The hall is recognised by its
# rail's first tile, HALL_TILE, at row 21 of strip 25.
#
# WATCHERS are Jungle Zone 1's dinosaurs. On the left balcony two green ones stand facing right (CALM). On the right
# balcony is the pair that chats by the catfish, green and pink, facing each other: one talks (TALK_A / TALK_B, a
# frame every TALK_SWAP, for TALK_FOR frames) while the other holds still, then they swap.
#
# When the boss is hit, each one reacts as it does on spotting Blue. It turns to face the middle of the hall and hops
# in horror (HOPS, px up, a frame each) with the red mark and wide eyes (ALARM, for ALARM_FOR frames), stays
# wide-eyed (WIDE, for WIDE_FOR), then goes back to what it was doing, each LAG frames after the one before. After the
# last hit they stay wide-eyed, facing the middle, until the hall is gone. The boss keeps the hits it can still take
# in the byte at +0x4013 of its object (see boss-hits). Its object is in a5 when boss-hits' final-boss set-up runs
# (BOSS_SETUP), and is saved in BOSS.
#
# They use the green and pink dinosaurs' palettes (0x1E and 0x3E as the hall has them, GREEN and PINK) at DIM
# brightness, in DIM_PALETTES, which are unused during the fight. Darker, they read as further back.
#
# SECTIONS are the balcony rails and the curtains at their ends, which a raised tail can reach. They're drawn again
# after the watchers, in front of them, with only their own pixels so the dark wall stays see-through. Their tiles
# are made from the hall's (columns, each top down) through FRONT, a PNG of the block (16 px a tile) marking which
# pixels draw in front: any opaque pixel. The colours come from the tiles.
#
# The state starts over on the hall's first frame, since the game may not pass through DRAW_CALL on its way in.
# Outside the hall, or when the next scene is set up (CLEAR_LAYER), the slots are hidden once and the boss and its hit
# count are forgotten, so a leftover value is never read as a hit.
STAGE = 40
STAGE_AT = 0x103005
DRAW_CALL = 0x11804            # jsr <the gameplay loop's front objects, then elevator-spin>
BOSS_SETUP = 0x36158           # jsr <boss-hits' final-boss routine>, with a5 = the boss
CLEAR_LAYER = 0xA36E           # move.w 0x24A(a6),d0 ; bra 0xA37E: one of the routines that clear a sprite layer as a
CLEAR_LAYER_REST = 0xA37E      # scene is set up. The ending's set-up calls it after the fight, when DRAW_CALL no
                               # longer comes round, so the watchers are hidden there too
HITS_LEFT = 0x4013
HALL_TILE = (25 * 64 + 21 * 2, 0x282A)
FIRST_SLOT, LAST_SLOT = 80, 99
SECTIONS = [   # name, the hall's tiles (columns, each top down), their palettes, FRONT, slot, x, top y
    ("rail_left", [[0x282A], [0x282B], [0x282C], [0x282D]], [0xF1, 0xF0, 0xF0, 0xF0],
     "art/final_fight/rail_left_front.png", 88, 32, 48),                                # row 21
    ("rail_right", [[0x286E], [0x286F], [0x2928], [0x2929]], [0xF0, 0xF0, 0xF0, 0xF1],
     "art/final_fight/rail_right_front.png", 92, 224, 48),
    ("curtain_left", [[0x2819, 0x2821], [0x281A, 0x2822]], [0xF3, 0xF1],
     "art/final_fight/curtain_left_front.png", 96, 16, 16),                              # rows 19-20
    ("curtain_right", [[0x2919, 0x2921], [0x291A, 0x2922]], [0xF1, 0xF3],
     "art/final_fight/curtain_right_front.png", 98, 272, 16),
]
CALM, ALARM, WIDE, TALK_A, TALK_B = 0x1164, 0x135C, 0x1360, 0x1478, 0x147C   # frames: 2 x 2 tiles
CALMLY, TALKS_FIRST, TALKS_SECOND = 0, 1, 2
WATCHERS = [   # (slot, x, top y - feet on the balcony floor, y 64 -, palette, mirrored, does, frames after a hit,
               #  mirrored while it reacts)
    (80, 34, 32, 0x1E, True, CALMLY, 0, True),                 # left balcony
    (82, 66, 32, 0x1E, True, CALMLY, 4, True),
    (84, 226, 32, 0x1E, True, TALKS_FIRST, 8, False),          # right balcony
    (86, 252, 32, 0x3E, False, TALKS_SECOND, 12, False),       # x 252: its raised tail clear of the curtain
]
TALK_SWAP, TALK_FOR = 7, 40
ALARM_FOR, WIDE_FOR = 20, 10
HOPS = [0, 2, 3, 4, 5, 6, 6, 6, 6, 5, 4, 3, 2, 0]   # up 6 px over 14 frames
GREEN = [0x5040, 0x02E2, 0x01B1, 0x4091, 0x4071, 0x6FF6, 0x0FD3, 0x4EA0, 0x0000, 0x0000, 0x8DDF, 0x899B, 0x0E00,
         0x0B00, 0x7FFF]       # colours 1-15
PINK = [0x4603, 0x9E7D, 0x0E4A, 0x1D17, 0x8B05, 0xDBFD, 0x46CB, 0xB498, 0xCF00, 0xCF00, 0xFFFA, 0xD962, 0x0E00,
        0x9A03, 0x7FFF]
DIM = 0.7
DIM_PALETTES = {0x1E: (0x7A, GREEN), 0x3E: (0x7B, PINK)}
BOSS = 0x10EA82                # a long (spare RAM): the boss's object (0: not set up yet)
SINCE = 0x10EA86               # a word: frames since the last hit (to 0x7FFF)
TICK = 0x10EA88                # a word: frames in the hall
HITS = 0x10EA8A                # bytes: the boss's hits left last frame (0xFF: not known), beaten (the last hit taken),
BEATEN = 0x10EA8B              # the slots shown
SHOWN = 0x10EA8C


def dimmed(w):
    """A colour word DIM as bright (5 bits a channel; the dark bit off)."""
    r = ((w >> 7) & 0x1E) | ((w >> 14) & 1)
    g = ((w >> 3) & 0x1E) | ((w >> 13) & 1)
    b = ((w << 1) & 0x1E) | ((w >> 12) & 1)
    r, g, b = (int(v * DIM + 0.5) for v in (r, g, b))
    return ((r & 1) << 14) | ((g & 1) << 13) | ((b & 1) << 12) | ((r >> 1) << 8) | ((g >> 1) << 4) | (b >> 1)


def front_writes(rom):
    """SECTIONS' VRAM writes (address, word): their front tiles, made from FRONT."""
    from png_tiles import read_rgba
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    writes = []
    for name, columns, palettes, front, slot, x, y in SECTIONS:
        mask = read_rgba(os.path.join(root, front))
        rows = len(columns[0])
        assert (len(mask[0]), len(mask)) == (16 * len(columns), 16 * rows), \
            "%s: %d x %d" % (front, 16 * len(columns), 16 * rows)
        for c, column in enumerate(columns):
            s = slot + c
            for r, tile in enumerate(column):
                px = rom.sprite_tile(tile)
                made = rom.add_sprite_tile(
                    [[px[yy][xx] if mask[r * 16 + yy][c * 16 + xx][1] else 0 for xx in range(16)] for yy in range(16)],
                    why="final fight: the %s in front, column %d row %d" % (name, c, r), share=True)
                writes += [(s * 64 + 2 * r, made & 0xFFFF), (s * 64 + 2 * r + 1, palettes[c] << 8 | (made >> 16) << 4)]
            writes += [(0x8000 + s, 0x0FFF), (0x8200 + s, ((496 - y) & 511) << 7 | rows | (0x40 if c else 0)),
                       (0x8400 + s, x << 7)]
    return writes


def frame_words(rom, frame):
    """A 2 x 2 frame's tiles as {left column top, bottom; right column top, bottom} (as the built ROM has it)."""
    tiles, _ = rom.frame_tiles(frame)
    assert len(tiles) == 2 and len(tiles[0]) == 2 and all(t is not None for row in tiles for t in row)
    assert all(t <= 0xFFFF for row in tiles for t in row)
    return ",".join("0x%04X" % tiles[r][c] for c in range(2) for r in range(2))


def apply(rom):
    assert rom.u16(DRAW_CALL) == 0x4EB9 and rom.u16(BOSS_SETUP) == 0x4EB9
    draw_before, setup = rom.u32(DRAW_CALL + 2), rom.u32(BOSS_SETUP + 2)
    writes = front_writes(rom)
    for palette, (to, colours) in DIM_PALETTES.items():
        assert len(colours) == 15
    entries = "".join("    .word %d,%d,%d,0x%04X,0x%04X\n    .byte %d,%d\n" % (
        slot, x, y, DIM_PALETTES[pal][0] << 8 | int(mirrored), DIM_PALETTES[pal][0] << 8 | int(reacting), does, lag)
        for slot, x, y, pal, mirrored, does, lag, reacting in WATCHERS)
    code = rom.place_code("""
    bra.w frame
    bra.w setup
    bra.w scene

scene:                                  | a scene set up: the watchers hidden, if they're shown
    bsr hide
    move.w 0x24A(%%a6),%%d0
    jmp 0x%(clear_rest)X

hide:
    tst.b 0x%(shown)X
    beq 1f
    movem.l %%d0-%%d1,-(%%sp)
    clr.b 0x%(shown)X
    move.w #1,0x3C0004
    move.w #0x8200+%(first)d,%%d0
    moveq #%(count)d,%%d1
0:  move.w %%d0,0x3C0000
    move.w #0,0x3C0002
    addq.w #1,%%d0
    dbf %%d1,0b
    movem.l (%%sp)+,%%d0-%%d1
1:  rts

setup:                                  | a5: the final boss, its hits just set
    jsr 0x%(setup)X
    move.l %%a5,0x%(boss)X
    st 0x%(hits)X                       | its count not known yet: no hit to see in it
    rts

frame:
    jsr 0x%(draw_before)X
    cmpi.b #%(stage)d,0x%(stage_at)X
    beq 0f
    clr.l 0x%(boss)X                    | another stage: no boss of ours
    rts
0:  movem.l %%d0-%%d7/%%a0-%%a2,-(%%sp)
    move.w #1,0x3C0004
    move.w #0x%(hall_addr)X,0x3C0000    | in the hall?
    cmpi.w #0x%(hall_tile)X,0x3C0002
    beq 2f
    bsr hide                            | no: the watchers hidden (once), the state starts over
    clr.l 0x%(boss)X                    | nothing left over to read a false hit from
    st 0x%(hits)X
    clr.b 0x%(beaten)X
    move.w #0x7FFF,0x%(since)X
    bra 9f

2:  tst.b 0x%(shown)X                   | its first frame: the state starts over (the frames before the hall
    bne 0f                              | may not come through here)
    st 0x%(shown)X
    st 0x%(hits)X
    clr.b 0x%(beaten)X
    move.w #0x7FFF,0x%(since)X
    clr.w 0x%(tick)X
0:  lea dims(%%pc),%%a0                 | the dimmed colours
    lea 0x%(dim_a)X,%%a1
    moveq #14,%%d0
0:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,0b
    lea 0x%(dim_b)X,%%a1
    moveq #14,%%d0
0:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,0b
    addq.w #1,0x%(tick)X
    cmpi.w #0x7FFF,0x%(since)X
    beq 0f
    addq.w #1,0x%(since)X
0:  move.l 0x%(boss)X,%%d0              | the boss hit: its hits left one fewer
    beq 3f
    movea.l %%d0,%%a0
    moveq #0,%%d1
    move.b %(hits_left)d(%%a0),%%d1
    moveq #0,%%d2
    move.b 0x%(hits)X,%%d2
    cmpi.b #0xFF,%%d2
    beq 0f
    subq.w #1,%%d2
    cmp.w %%d1,%%d2
    bne 0f
    clr.w 0x%(since)X
    tst.b %%d1
    seq 0x%(beaten)X
0:  move.b %%d1,0x%(hits)X
3:  lea watchers(%%pc),%%a2
    moveq #%(watchers)d,%%d7
0:  bsr watcher
    lea 12(%%a2),%%a2
    dbf %%d7,0b
    lea fronts(%%pc),%%a0               | the rails and curtains, in front
    move.w #%(writes)d,%%d0
0:  move.w (%%a0)+,0x3C0000
    move.w (%%a0)+,0x3C0002
    dbf %%d0,0b
9:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a2
    rts

watcher:                                | a2: its entry - slot, x, y, its attributes, reacting, what it does, lag
    lea calm(%%pc),%%a0
    tst.b 10(%%a2)
    beq 1f
    lea talk_b(%%pc),%%a0               | chatting: talking or listening
    moveq #0,%%d1
    move.w 0x%(tick)X,%%d1
    divu #%(talk_period)d,%%d1
    clr.w %%d1
    swap %%d1                           | the frame in the exchange
    cmpi.w #%(talk_for)d,%%d1
    scs %%d2                            | the first's turn
    cmpi.b #%(talks_first)d,10(%%a2)
    seq %%d3
    cmp.b %%d2,%%d3
    bne 1f
    cmpi.w #%(talk_for)d,%%d1
    bcs 0f
    subi.w #%(talk_for)d,%%d1
0:  divu #%(talk_swap)d,%%d1
    btst #0,%%d1
    bne 1f
    lea talk_a(%%pc),%%a0
1:  move.w 6(%%a2),%%d3                 | its attributes (palette, mirrored)
    moveq #0,%%d4                       | up
    move.w 0x%(since)X,%%d5             | a hit: frames since it, for this one
    moveq #0,%%d6
    move.b 11(%%a2),%%d6
    sub.w %%d6,%%d5
    bmi 8f
    tst.b 0x%(beaten)X
    bne 0f
    cmpi.w #%(react_for)d,%%d5
    bcc 8f
0:  move.w 8(%%a2),%%d3                 | reacting: facing the middle
    cmpi.w #%(alarm_for)d,%%d5
    bcc 0f
    lea alarm(%%pc),%%a0                | the red mark, a hop
    cmpi.w #%(hop_for)d,%%d5
    bcc 8f
    lea hops(%%pc),%%a1
    move.b (%%a1,%%d5.w),%%d4
    bra 8f
0:  lea wide(%%pc),%%a0                 | wide-eyed
8:  move.w #496,%%d5                    | SCB3: its top, 2 tiles
    sub.w 4(%%a2),%%d5
    add.w %%d4,%%d5
    and.w #511,%%d5
    lsl.w #7,%%d5
    addq.w #2,%%d5
    movea.l %%a0,%%a1                   | a0: the left column on screen, a1: the right - swapped if mirrored
    lea 4(%%a0),%%a0
    btst #0,%%d3
    bne 0f
    exg %%a0,%%a1
0:  move.w (%%a2),%%d0                  | the left column
    move.w %%d0,%%d1
    lsl.w #6,%%d1
    move.w %%d1,0x3C0000
    move.w (%%a0),0x3C0002
    move.w %%d3,0x3C0002
    move.w 2(%%a0),0x3C0002
    move.w %%d3,0x3C0002
    move.w %%d0,%%d1
    add.w #0x8000,%%d1
    move.w %%d1,0x3C0000
    move.w #0x0FFF,0x3C0002
    add.w #0x200,%%d1
    move.w %%d1,0x3C0000
    move.w %%d5,0x3C0002
    add.w #0x200,%%d1
    move.w %%d1,0x3C0000
    move.w 2(%%a2),%%d2
    lsl.w #7,%%d2
    move.w %%d2,0x3C0002
    addq.w #1,%%d0                      | the right column, stuck to it
    move.w %%d0,%%d1
    lsl.w #6,%%d1
    move.w %%d1,0x3C0000
    move.w (%%a1),0x3C0002
    move.w %%d3,0x3C0002
    move.w 2(%%a1),0x3C0002
    move.w %%d3,0x3C0002
    move.w %%d0,%%d1
    add.w #0x8000,%%d1
    move.w %%d1,0x3C0000
    move.w #0x0FFF,0x3C0002
    add.w #0x200,%%d1
    move.w %%d1,0x3C0000
    ori.w #0x40,%%d5
    move.w %%d5,0x3C0002
    rts

watchers:
%(entries)s    .even
calm:
    .word %(calm)s
alarm:
    .word %(alarm)s
wide:
    .word %(wide)s
talk_a:
    .word %(talk_a)s
talk_b:
    .word %(talk_b)s
dims:
    .word %(dims)s
fronts:
    .word %(fronts)s
hops:
    .byte %(hops)s
    .even
""" % {"setup": setup, "boss": BOSS, "draw_before": draw_before, "stage": STAGE, "stage_at": STAGE_AT,
       "hall_addr": HALL_TILE[0], "hall_tile": HALL_TILE[1], "shown": SHOWN, "first": FIRST_SLOT,
       "count": LAST_SLOT - FIRST_SLOT, "clear_rest": CLEAR_LAYER_REST, "hits": HITS, "beaten": BEATEN, "since": SINCE, "tick": TICK,
       "dim_a": 0x400000 + DIM_PALETTES[0x1E][0] * 32 + 2, "dim_b": 0x400000 + DIM_PALETTES[0x3E][0] * 32 + 2,
       "hits_left": HITS_LEFT, "watchers": len(WATCHERS) - 1, "writes": len(writes) - 1, "entries": entries,
       "talk_period": 2 * TALK_FOR, "talk_for": TALK_FOR, "talks_first": TALKS_FIRST, "talk_swap": TALK_SWAP,
       "react_for": ALARM_FOR + WIDE_FOR, "alarm_for": ALARM_FOR, "hop_for": len(HOPS),
       "calm": frame_words(rom, CALM), "alarm": frame_words(rom, ALARM), "wide": frame_words(rom, WIDE),
       "talk_a": frame_words(rom, TALK_A), "talk_b": frame_words(rom, TALK_B),
       "dims": ",".join("0x%04X" % dimmed(w) for w in DIM_PALETTES[0x1E][1] + DIM_PALETTES[0x3E][1]),
       "fronts": ",".join("0x%04X,0x%04X" % w for w in writes), "hops": ",".join(str(h) for h in HOPS)},
        why="final fight: the dinosaurs watching")
    rom.write(DRAW_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + draw_before.to_bytes(4, "big"), why="each frame of play: the final fight's watchers")
    rom.write(CLEAR_LAYER, bytes.fromhex("4EF9") + (code + 8).to_bytes(4, "big"), expect=bytes.fromhex("302E024A600A"),
              why="a scene set up: the final fight's watchers hidden")
    rom.write(BOSS_SETUP, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + setup.to_bytes(4, "big"), why="final boss: its object kept for the watchers")
