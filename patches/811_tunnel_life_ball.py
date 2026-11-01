import os

from png_tiles import read_rgba, write_indexed, neo_to_rgb, rgb_to_neo

NAME = "tunnel-life-ball"
DESCRIPTION = "Lower Earth Empire 2's hidden tunnel: its reward, the white lily (+10 flowers), is a life ball (+1 heart)"

# The white lily at the end of Lower Earth Empire 2's hidden tunnel becomes a life ball.
#
# Placed white lilies start at LILY_START (reached from the object tables at LILY_KINDS). We hook that: a lily at
# LILY_AT in LILY_STAGE becomes a LIFE_BALL pickup, and every other lily is left alone. Its position is worked out from
# the level camera at 0x10021A / 0x10020E, the same way wall-moss does it.
#
# The only life ball in the game is the lottery prize (LOTTERY_BALL), a 64x48 frame that Blue bumps into instead of
# picking up. So we add a 16x16 one drawn from BALL_ART, as one new tile and frame with the lily's hit box. If
# BALL_ART is missing, a first draft is shrunk from the lottery ball and saved next to a full-size reference.
#
# The ball's colours go in BALL_PAL, which this stage doesn't use. They're copied in every frame from the vblank wait
# (FRAME_LOOP, chained ahead of round-clear-dim), except while the screen is blacked out or dimmed.
#
# Hardware-shrinking the lottery frame instead drew fine, but the shrunk sprite couldn't be picked up.
LILY_START = 0x50CB8            # move.b #1,0x4D(a5) ; move.w #0x20A0,8(a5) ... bra 0x51872
LILY_KINDS = [0x5F4DC, 0x5FCDC]   # object table entries that point to LILY_START
LILY_PICKUP = 0x51872           # shared pickup code
LILY_STAGE, LILY_AT = 4, (1072, -784)   # Lower Earth Empire 2; level x, y (y = y field / 128 + 0x10020E)
LIFE_BALL, LOTTERY_BALL, LILY_FRAME = 9, 0x326C, 0x20A0
BALL_PAL = 0xA8
BALL_ART = "art/life_ball/life_ball.png"   # 16x16, up to 15 colours; the build makes the tile from it
BALL_REFERENCE = "art/life_ball/lottery_ball_reference.png"
BALL_COLOURS = [0x0000, 0xE37D, 0xB58D, 0xF69D, 0xA8AE, 0xF9BE, 0x3BCE, 0x6CDF, 0x2EEF, 0x7FFF, 0x5FBC, 0x1F9B,
                0x1E7A, 0x6D49, 0x6C28, 0x0000]   # lottery palette 0xB2, used for the first draft
BOXES = 0x64772                 # hit box pointer per frame number
FRAME_LOOP = 0xE8AC             # jmp <round-clear-dim> in the vblank wait loop
STAGE = 0x103005


def small_life_ball(rom):
    """Add the small life ball's tile and frame from BALL_ART, drafting BALL_ART first if it doesn't exist.
    Returns the frame and BALL_PAL's 16 colours."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    art, reference = os.path.join(root, BALL_ART), os.path.join(root, BALL_REFERENCE)
    if not os.path.exists(art):
        tiles, _ = rom.frame_tiles(LOTTERY_BALL)
        big = [[0] * (16 * len(tiles[0])) for _ in range(16 * len(tiles))]
        for r, row in enumerate(tiles):
            for c, t in enumerate(row):
                if t is not None:
                    for y, line in enumerate(rom.sprite_tile(t)):
                        big[r * 16 + y][c * 16:c * 16 + 16] = line
        ys = [y for y, line in enumerate(big) if any(line)]
        xs = [x for x in range(len(big[0])) if any(line[x] for line in big)]
        top, left = ys[0], xs[0]
        h, w = ys[-1] - top + 1, xs[-1] - left + 1
        f = max(w, h) / 16              # each pixel takes its block's most common colour if the block is mostly solid
        top -= (max(w, h) - h) / 2
        left -= (max(w, h) - w) / 2
        px = [[0] * 16 for _ in range(16)]
        for y in range(16):
            for x in range(16):
                block = [big[sy][sx] if 0 <= sy < len(big) and 0 <= sx < len(big[0]) else 0
                         for sy in range(int(top + y * f), int(top + (y + 1) * f + 0.999))
                         for sx in range(int(left + x * f), int(left + (x + 1) * f + 0.999))]
                solid = [v for v in block if v]
                if 2 * len(solid) >= len(block):
                    px[y][x] = max(set(solid), key=solid.count)
        palette = [neo_to_rgb(c) for c in BALL_COLOURS]
        os.makedirs(os.path.dirname(art), exist_ok=True)
        write_indexed(art, px, palette)
        write_indexed(reference, [line[xs[0]:xs[-1] + 1] for line in big[ys[0]:ys[-1] + 1]], palette)
    pixels = read_rgba(art)
    assert (len(pixels[0]), len(pixels)) == (16, 16), "%s: not 16 x 16" % BALL_ART
    colours = sorted({rgb for row in pixels for rgb, a in row if a})
    assert len(colours) <= 15, "%s: %d colours (15 at most)" % (BALL_ART, len(colours))
    px = [[colours.index(rgb) + 1 if a else 0 for rgb, a in row] for row in pixels]
    words = [0] + [rgb_to_neo(c) for c in colours]
    tile = rom.add_sprite_tile(px, why="the small life ball (the hidden tunnel's reward)")
    return rom.add_frame([[tile]], BALL_PAL, why="the small life ball"), words + [0] * (16 - len(words))


def apply(rom):
    blackout, dim = rom.other_patch("screen-blackout"), rom.other_patch("round-clear-dim")
    ball_frame, ball_colours = small_life_ball(rom)
    assert rom.u16(FRAME_LOOP) == 0x4EF9, "tunnel-life-ball: needs round-clear-dim's hook at the vblank wait"
    next_frame = rom.u32(FRAME_LOOP + 2)
    code = rom.place_code("""
    bra.w frame                         | +0
    bra.w lily_start                    | +4

| once a frame (d1-a5 free): refresh the ball's colours in its stage, then chain on
frame:
    cmpi.b #%(lily_stage)d,0x%(stage)X
    bne 0f
    tst.b 0x%(black)X
    bne 0f
    tst.b 0x%(dimmed)X
    bne 0f
    lea ball_colours(%%pc),%%a0
    lea 0x%(ball_pal)X,%%a1
    moveq #7,%%d1
1:  move.l (%%a0)+,(%%a1)+
    dbf %%d1,1b
0:  jmp 0x%(next)X
ball_colours:
    .word %(ball_colours)s

| a placed white lily starting: turn the one at the tunnel's end into a life ball
lily_start:
    cmpi.b #%(lily_stage)d,0x%(stage)X
    bne 9f
    move.l %%d0,-(%%sp)
    move.w 2(%%a5),%%d0                 | level x
    sub.w #0x4000,%%d0
    asr.w #7,%%d0
    add.w 0x10021A,%%d0
    sub.w #%(lily_x)d-8,%%d0
    cmp.w #16,%%d0
    bhi 8f
    move.w (%%a5),%%d0                  | level y
    asr.w #7,%%d0
    add.w 0x10020E,%%d0
    sub.w #%(lily_y)d-8,%%d0
    cmp.w #16,%%d0
    bhi 8f
    move.l (%%sp)+,%%d0
    move.b #%(life_ball)d,0x4D(%%a5)
    move.w #0x%(ball_frame)X,8(%%a5)
    move.b #0x40,0x28(%%a5)
    move.l #0x%(lily_pickup)X,4(%%a5)
    jmp 0x%(lily_pickup)X
8:  move.l (%%sp)+,%%d0
9:  jmp 0x%(lily_start)X
""" % {"lily_stage": LILY_STAGE, "stage": STAGE, "black": blackout.BLACK, "dimmed": dim.ACTIVE,
       "ball_pal": 0x400000 + BALL_PAL * 32, "ball_colours": ",".join("0x%04X" % c for c in ball_colours),
       "next": next_frame, "lily_x": LILY_AT[0], "lily_y": LILY_AT[1], "life_ball": LIFE_BALL,
       "ball_frame": ball_frame, "lily_pickup": LILY_PICKUP, "lily_start": LILY_START},
        why="the hidden tunnel's life ball")
    rom.write(FRAME_LOOP + 2, code.to_bytes(4, "big"), expect=next_frame.to_bytes(4, "big"),
              why="vblank wait, each frame: the life ball's colours first")
    assert rom.data[LILY_START:LILY_START + 10] == bytes.fromhex("1B7C0001004D3B7C20A0")
    rom.write(BOXES + ball_frame, rom.u32(BOXES + LILY_FRAME).to_bytes(4, "big"),
              expect=rom.data[BOXES + ball_frame:BOXES + ball_frame + 4], why="the small life ball: the lily's hit box")
    for at in LILY_KINDS:
        rom.write(at, (code + 4).to_bytes(4, "big"), expect=LILY_START.to_bytes(4, "big"),
                  why="a placed white lily: a life ball at the hidden tunnel's end")
