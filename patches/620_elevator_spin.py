NAME = "elevator-spin"
DESCRIPTION = "The elevators' cone turns while they move - its stripes slide round (colour cycling), one way up, the other down"

import math

# The cone under the elevators' platforms (and under the final boss's platform) is one frame, 0x23CC: 4x2 tiles from
# CONE (tile 0x4D74 + column + 8 * row, its definition at 0x7363A - nothing else uses them), palette PALETTE. Its
# colours 1-9 shade the cone and the metal bands like a lit cylinder, A-E the green ring, F a glint. They're redrawn
# in place for colour cycling: each pixel keeps its brightness (metal 3 levels, the ring 2) and gets a stripe position
# (3) from where it sits round its row - STRIPES stripes round the shape, so they bunch at the edges - as colour
# 1 + 3 * level + stripe (metal) or 10 + 3 * level + stripe (ring). Each frame of play (after the front objects are
# drawn: DRAW_CALL) the first object showing the cone sets the palette: while it
# moves the stripes step every FRAME_TIME frames - forward going up, back going down; standing still they hold.
# Moving is measured, not read from its fields (the cone's three objects keep them differently; the one rising to the
# top keeps its speed after it parks): its height in the level, its y (+0, 8.8, up from the screen's bottom) plus the
# camera's (CAMERA_Y: one of its steps is 0x80 of an object's y), against last frame's (LAST, while SEEN) - so the
# camera scrolling (Blue walking up to it, jumping) isn't taken for the cone moving. A stripe's three positions are
# three
# tones of its level's colour (TONES, from CONTRAST).
CONE = 0x4D74
CONE_DEFINITION = 0x7363A      # 03 01 00 F7 4D 74 7C 75 7D 76 7E 77 7F FF
CONE_FRAME = 0x23CC
PALETTE = 0xF7
ORIGINAL = [0x3099, 0x79BC, 0x079A, 0x0578, 0x8467, 0x7245, 0xF134, 0x7023,       # (palette 0xF7 as the stages
            0x8023, 0xF012, 0xD5C8, 0xF3A6, 0x7184, 0x3062, 0x2041, 0xFCEF]       # load it - the same in both)
STRIPES = 15
CONTRAST = 0.30
TONES = [1 + CONTRAST * 0.4, 1 - CONTRAST * 0.3, 1 - CONTRAST]
FRAME_TIME = 6
DRAW_CALL = 0x11804            # jsr (the gameplay loop's front objects)
OBJECTS, OBJECT_SIZE, LAST_OBJECT = 0x104000, 0x80, 0x107F80
ACTIVE, FRAME = 0x28, 8
CAMERA_Y = 0x10020A
STAGE = 0x103005
STAGES = [28, 29, 31]          # the stages with the cone (the elevators - 28 up, 29 down; the final stage's
                               # mini-boss and boss
                               # platforms) - elsewhere the scan's cost (128 objects a frame) slowed busy scenes
TICK = 0x10EA7A                # bytes (spare RAM): frames since the last step, the stripes' step (0-2)
LAST = 0x10EA7C                # a long: the cone's height in the level last frame (8.8)
SEEN = 0x10EA80                # a byte: a cone was found last frame (LAST is good)


def group(v):
    """(ring?, brightness level) for an original colour, or None for clear."""
    if not v:
        return None
    if 10 <= v <= 14:
        return True, 0 if v <= 12 else 1
    return False, 2 if v == 15 or v >= 7 else 1 if v >= 4 else 0


def repainted(rom):
    """The cone's pixels (32 x 64) in the cycling colours."""
    old = [[0] * 64 for _ in range(32)]
    for c in range(4):
        for r in range(2):
            px = rom.sprite_tile(CONE + c + 8 * r)
            for y in range(16):
                old[r * 16 + y][c * 16:c * 16 + 16] = px[y]
    new = [[0] * 64 for _ in range(32)]
    for y in range(32):
        for ring in (False, True):
            xs = [x for x in range(64) if group(old[y][x]) and group(old[y][x])[0] == ring]
            if not xs:
                continue
            middle, half = (min(xs) + max(xs) + 1) / 2, (max(xs) - min(xs) + 1) / 2
            for x in xs:
                u = math.asin(max(-1.0, min(1.0, (x + 0.5 - middle) / half))) / math.pi + 0.5
                stripe = int(u * STRIPES) % 3
                new[y][x] = (10 if ring else 1) + 3 * group(old[y][x])[1] + stripe
    return new


def rgb(word):
    from png_tiles import neo_to_rgb
    return neo_to_rgb(word)


def tables():
    """Palette PALETTE's colours 1-15 for each of the 3 steps."""
    from png_tiles import rgb_to_neo
    def base(ring, level):
        vs = [v for v in range(1, 16) if group(v) == (ring, level)]
        cs = [rgb(ORIGINAL[v]) for v in vs]
        return [sum(c[i] for c in cs) / len(cs) for i in range(3)]
    out = []
    for step in range(3):
        words = []
        for ring, levels in ((False, 3), (True, 2)):
            for level in range(levels):
                for stripe in range(3):
                    tone = TONES[(stripe + step) % 3]
                    words.append(rgb_to_neo(tuple(max(0, min(255, round(v * tone))) for v in base(ring, level))))
        out.append(words)                                  # 9 metal, then 6 ring: colours 1-15
    return out


def apply(rom):
    assert bytes(rom.data[CONE_DEFINITION:CONE_DEFINITION + 5]) == bytes.fromhex("030100F74D")
    px = repainted(rom)
    for c in range(4):
        for r in range(2):
            rom.redraw_sprite_tile(CONE + c + 8 * r, [row[c * 16:c * 16 + 16] for row in px[r * 16:r * 16 + 16]],
                                   why="elevator cone repainted for its spin, column %d row %d" % (c, r))
    before = rom.u32(DRAW_CALL + 2)
    assert rom.u16(DRAW_CALL) == 0x4EB9
    steps = tables()
    code = rom.place_code("""
    jsr 0x%(before)X
    movem.l %%d0-%%d1/%%a0-%%a1,-(%%sp)
%(stages)s    bra 9f
0:  lea 0x%(objects)X,%%a0              | the first object showing the cone
1:  tst.b %(active)d(%%a0)
    beq 2f
    cmpi.w #0x%(frame)X,%(frame_at)d(%%a0)
    beq 3f
2:  lea %(size)d(%%a0),%%a0
    cmpa.l #0x%(last)X,%%a0
    bls 1b
    clr.b 0x%(seen)X                    | (none: next time LAST starts again)
    bra 9f
3:  moveq #0,%%d1                       | its height in the level: y + the camera's
    move.w 0x%(camera)X,%%d1
    lsl.l #7,%%d1
    moveq #0,%%d0
    move.w (%%a0),%%d0
    add.l %%d1,%%d0
    tst.b 0x%(seen)X                    | seen last frame: how far it moved since
    beq 8f
    move.l %%d0,%%d1
    sub.l 0x%(last_height)X,%%d1
    move.l %%d0,0x%(last_height)X
    tst.l %%d1
    beq 5f                              | (still: the stripes hold)
    addq.b #1,0x%(tick)X                | moving: a step every FRAME_TIME frames, its way
    cmpi.b #%(frame_time)d,0x%(tick)X
    bcs 5f
    clr.b 0x%(tick)X
    move.b 0x%(tick)X+1,%%d0
    tst.l %%d1
    bmi 4f
    addq.b #1,%%d0                      | going up
    cmpi.b #3,%%d0
    bcs 6f
    moveq #0,%%d0
    bra 6f
4:  subq.b #1,%%d0                      | going down
    bpl 6f
    moveq #2,%%d0
6:  move.b %%d0,0x%(tick)X+1
    bra 5f
8:  move.l %%d0,0x%(last_height)X        | (first seen: from now on)
    st 0x%(seen)X
5:  moveq #0,%%d1                       | its colours for this step
    move.b 0x%(tick)X+1,%%d1
    mulu #30,%%d1
    lea steps(%%pc),%%a1
    adda.l %%d1,%%a1
    lea 0x%(palette_ram)X+2,%%a0
    moveq #14,%%d1
7:  move.w (%%a1)+,(%%a0)+
    dbf %%d1,7b
9:  movem.l (%%sp)+,%%d0-%%d1/%%a0-%%a1
    rts
steps:
    .word %(steps)s
""" % {"before": before, "objects": OBJECTS, "active": ACTIVE, "frame": CONE_FRAME, "frame_at": FRAME,
       "size": OBJECT_SIZE, "last": LAST_OBJECT, "tick": TICK, "frame_time": FRAME_TIME, "camera": CAMERA_Y,
       "last_height": LAST, "seen": SEEN,
       "stages": "".join("    cmpi.b #%d,0x%X\n    beq 0f\n" % (n, STAGE) for n in STAGES),
       "palette_ram": 0x400000 + PALETTE * 32, "steps": ",".join("0x%04X" % w for s in steps for w in s)},
        why="elevator cone: its colours, stepping while it moves")
    rom.write(DRAW_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + before.to_bytes(4, "big"), why="each frame of play: the elevator cone's spin")
