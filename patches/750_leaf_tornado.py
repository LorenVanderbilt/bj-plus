NAME = "leaf-tornado"
DESCRIPTION = "Leaf level 3: the tornado redrawn as a funnel with an open top, spinning; it ends in curls of air instead of just vanishing"

import math
import random

# Once the level 3 leaf lands, it sends out a tornado. The leaf object (0x464B6) plays an animation script through
# 0x434A8 and ends at 0x45F6E when the script runs out. Frames 0x500-0x514 (player 2: 0xD00-0xD14) show the leaf on
# the ground plus two 2-tile columns of wind moving further out each frame: three drawings of a flat grey crescent,
# tiles 0x4D04-0x4D19.
#
# Another object's whirlwind (frames 0x2E44-0x2E54) shares those tiles, so the tornado gets its own tiles and frame
# definitions (OLD_DEFS), keeping the leaf and offsets:
#   * A funnel, bowed like the old crescent and as wide (SPINE, TOP_HALF), with its top open towards the camera: a
#     dark hollow inside a lit rim, and a ragged grey body narrowing to a thin tip with bright streaks wrapping
#     round it. Three spin drawings share one tip, 8 tiles in all.
#   * When the script ends on a tornado frame (END_HOOK, TORNADO_LAST), the funnel vanishes and four curls of air
#     (CURL) burst out of its top, moving out and up a step every CURL_HOLD frames. Then the leaf ends as before.
# Everything is drawn here in palette 0x61's greys (GREYS, light to dark).
OLD_DEFS = {   # leaf palette: the frame definitions, in script order
    0x56: [0x6DC00, 0x6DC1C, 0x6DC38, 0x6DC54, 0x6DC70, 0x6DC8C],
    0x57: [0x6E711, 0x6E72D, 0x6E749, 0x6E765, 0x6E781, 0x6E79D],
}
DRAWING = [0, 1, 2, 0, 1, 2]   # spin drawing per frame, as before
FRAME_TABLE, FRAMES = 0x60772, 0x4000
WIND_PALETTE = 0x61
GREYS = [15, 14, 8, 9, 10, 11, 12, 13]
END_HOOK = 0x464BC             # jsr 0x434A8 (steps the script, ne at its end) ; bne 0x45F6E (ends the object)
STEP, GONE = 0x434A8, 0x45F6E
TORNADO_LAST = (0x514, 0xD14)  # the script's last frame for players 1 and 2
CURL = ["..###..",
        ".#...#.",
        "#..#..#",
        "#.##..#",
        ".#...#.",
        "..##..."]
CURL_STEPS, CURL_HOLD = 4, 3
SPINE = (14, 6, 5)             # px: the top's x, how far it bows right, how far the tip curls back left
TOP_HALF = 12                  # half width at the top: 26 px across, like the original
CURL_PATHS = [(-1, 0.4), (1, 0.2), (-0.35, -1), (0.45, -0.9)]   # each curl's direction (x, y) from the funnel's top


def spine(t):
    """The funnel's centre x at height t (0 = top, 1 = tip), bowed out to the right like the original crescent."""
    return SPINE[0] + SPINE[1] * math.sin(math.pi * t) - SPINE[2] * t


def funnel(phase, W=32, H=32):
    """The tornado at spin phase 0-1, facing right, as rows of palette 0x61 indices (0 = clear)."""
    out = [[0] * W for _ in range(H)]
    rnd = random.Random(7)
    top_y, ry = 4, 3.4
    halves = []
    for y in range(H):
        t = y / (H - 1)
        half = TOP_HALF * (1 - t) ** 1.1 + 1.0
        halves.append(half)
        if y < top_y:
            continue
        cx = spine(t)
        ragged = rnd.choice((-1, 0, 0, 1)) if half > 3 else 0
        for x in range(W):
            u = (x + 0.5 - cx) / (half + ragged)
            if abs(u) <= 1:
                out[y][x] = 9 if abs(u) < 0.45 else (10 if abs(u) < 0.8 else 11)
    for y0 in range(9, H - 1, 4):                      # streaks round the body's front, sliding with the spin
        half, cx = halves[y0], spine(y0 / (H - 1))
        off = ((phase * 2 + y0 * 0.11) % 1.0) * 2 - 1
        for k in range(int(half * 2.2)):
            u = off - k / max(1.0, half) * 0.9
            if u < -1:
                u += 2
            x, y = int(round(cx + u * half)), int(round(y0 + (1 - u * u) * 1.6))
            if 0 <= x < W and 0 <= y < H and out[y][x]:
                out[y][x] = 15 if k < half * 0.6 else (14 if k < half * 1.3 else 8)
    half0, cx0 = halves[0], spine(top_y / (H - 1))
    for y in range(H):                                 # the open top: a rim around a dark hollow
        for x in range(W):
            u, v = (x + 0.5 - cx0) / (half0 + 0.5), (y + 0.5 - top_y) / ry
            d = u * u + v * v
            if d <= 1:
                if d > 0.62:
                    spin = (math.atan2(v, u) / (2 * math.pi) - phase) % 1.0
                    out[y][x] = 15 if spin < 0.16 else ((14 if u < 0.3 else 8) if v > 0 else (9 if u < 0 else 10))
                else:
                    out[y][x] = 12 if v < 0.1 else 11
    return out


def curl(thin):
    """A 16x16 curl of air. thin draws every other pixel, a shade darker."""
    out = [[0] * 16 for _ in range(16)]
    for y, line in enumerate(CURL):
        for x, ch in enumerate(line):
            if ch == "#" and (not thin or (x + y) % 2):
                out[5 + y][4 + x] = 14 if thin else 15
    return out


def quarter(px, col, row):
    return [r[col * 16:col * 16 + 16] for r in px[row * 16:row * 16 + 16]]


def apply(rom):
    # the tiles: 3 tops, the shared tip, 2 curls
    tops = []
    for i in range(3):
        px = funnel(i / 3)
        tops.append([rom.add_sprite_tile(quarter(px, c, 0), why="leaf tornado: spin %d, top %s" % (i, "LR"[c]))
                     for c in range(2)])
    px = funnel(0)
    tip = [rom.add_sprite_tile(quarter(px, c, 1), why="leaf tornado: its tip, %s" % "LR"[c]) for c in range(2)]
    curls = [rom.add_sprite_tile(curl(thin), why="leaf tornado: a curl of air%s" % (" (thinned)" if thin else ""))
             for thin in (False, True)]

    entry = lambda tile, flips: bytes([1, 0x20 | flips, tile >> 8, tile & 0xFF])
    remap, curl_frames = {}, {}
    for palette, defs in OLD_DEFS.items():
        for n, old in enumerate(defs):
            head = bytes(rom.data[old:old + 9])
            assert head == bytes([1, 1, 1, palette, 0x3B, 6, 0x0E, 7, 0x0F]), (hex(old), head.hex())
            a, b = rom.data[old + 10], rom.data[old + 19]          # the two wind columns' x; a is further out
            assert rom.data[old + 9] == 1 and rom.data[old + 18] == 1 and rom.data[old + 27] == 0xFF
            top, body = tops[DRAWING[n]], tip
            # facing right the object is mirrored, so column b (nearer the leaf) shows on the left
            new = head + bytes([1, a, 0, WIND_PALETTE, top[1] >> 8]) + entry(top[1], 1) + entry(body[1], 1) \
                + bytes([1, b, 0, WIND_PALETTE, top[0] >> 8]) + entry(top[0], 1) + entry(body[0], 1) + b"\xff"
            at = rom.alloc(len(new))
            rom.data[at:at + len(new)] = new
            rom.log.append("  0x%06X  %d byte(s)  leaf tornado: frame definition (palette 0x%X, %d)" % (at, len(new), palette, n))
            remap[old] = at
        # the curl frames: the leaf, then 4 curls around where the funnel's top was in the last frame
        a, b = rom.data[defs[-1] + 10], rom.data[defs[-1] + 19]
        centre = ((a - 256 if a > 127 else a) + (b - 256 if b > 127 else b)) / 2 + 4    # in 2 px units
        frames = []
        for s in range(CURL_STEPS):
            body = bytearray(rom.data[defs[-1]:defs[-1] + 9])
            tile = curls[1 if s >= 2 else 0]
            for k, (dx, dy) in enumerate(CURL_PATHS):
                x = int(round(centre - dx * (7 + s * 4) / 2 - 4))     # mirrored: + is towards the leaf
                up = int(round(-dy * (4 + s * 3) / 2 + 2))
                body += bytes([0, x & 0xFF, up & 0xFF, WIND_PALETTE, tile >> 8]) + entry(tile, 1 if dx > 0 else 0)
            body += b"\xff"
            at = rom.alloc(len(body))
            rom.data[at:at + len(body)] = body
            n = rom.next_frame
            rom.next_frame += 4
            rom.write(FRAME_TABLE + n, at.to_bytes(4, "big"), why="frame 0x%X -> leaf tornado's curls %d" % (n, s))
            frames.append(n)
        curl_frames[palette] = frames
    count = 0
    for fr in range(0, FRAMES, 4):
        p = rom.u32(FRAME_TABLE + fr)
        if p in remap:
            rom.write(FRAME_TABLE + fr, remap[p].to_bytes(4, "big"), why="frame 0x%X -> the new leaf tornado" % fr)
            count += 1
    assert count >= 12, count

    code = rom.place_code("""
    jsr 0x%(step)X
    bne 1f
    rts
1:  move.w 8(%%a5),%%d0                 | did the script end on a tornado frame?
    cmpi.w #0x%(last1)X,%%d0
    beq 2f
    cmpi.w #0x%(last2)X,%%d0
    beq 2f
    jmp 0x%(gone)X
2:  move.l #curls,4(%%a5)               | play the curls, then end
    clr.w 0x64(%%a5)                    | reuse the script position as the curl counter
curls:
    move.w 0x64(%%a5),%%d0
    cmpi.w #%(total)d,%%d0
    bcs 3f
    jmp 0x%(gone)X
3:  addq.w #1,0x64(%%a5)
    andi.l #0xFFFF,%%d0
    divu #%(hold)d,%%d0
    add.w %%d0,%%d0
    lea frames1(%%pc),%%a0
    tst.b 0x7E(%%a5)                    | player 2's leaf?
    beq 4f
    lea frames2(%%pc),%%a0
4:  move.w (%%a0,%%d0.w),8(%%a5)
    rts
frames1:
    .word %(frames1)s
frames2:
    .word %(frames2)s
""" % {"step": STEP, "gone": GONE, "last1": TORNADO_LAST[0], "last2": TORNADO_LAST[1],
       "total": CURL_STEPS * CURL_HOLD, "hold": CURL_HOLD,
       "frames1": ",".join("0x%X" % f for f in curl_frames[0x56]),
       "frames2": ",".join("0x%X" % f for f in curl_frames[0x57])},
        why="leaf tornado: its end - curls of air")
    rom.write(END_HOOK, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E754E71"),
              expect=bytes.fromhex("4EB9000434A86600FAAA"), why="leaf object's script: at a tornado's end, the curls")
