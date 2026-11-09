NAME = "title-banner"
DESCRIPTION = "Title screen: the bird tows a PLUS banner across under the logo and lets it go where it pops the balloon"

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The title's bird (object BIRD, with x at +2 and y at +0, a 32x32 sprite) flies right to left under the logo at
# 1.5 px a frame and pops Blue's balloon as its left edge passes screen x 140. On the title, its screen x is
# 2 * (+2 / 256) - 127 and the sprite's top is +0 / 256 - 20.
#
# Every frame of the title (title-menu's per-frame call, FRAME_CALL), ART is drawn just behind the bird, rope first
# and then the cloth, with its left edge GAP px right of the bird's. When it reaches STOP_X it stays there and the bird
# flies on. It uses sprites SLOTS, one chained 16 px column each, above everything the title draws (the title's last
# sprite is 280). As the title ends (LEAVE_CALL) they're hidden and the state is cleared, so the next title tows it
# in again. Its colours, COLOURS, are a GIMP palette (index 0 clear, then up to 15) written into palette PALETTE,
# which is empty on the title, while it's drawn; nothing changes the palettes until the title ends and the next
# scene loads them all. Without the pictures it draws a placeholder in fix palette 1, since palettes 0-15 never
# change.
#
# The cloth flutters through ARTS' pictures in SEQUENCE's order (0 = the first), FRAME_TIME frames each, on a loop
# counted by TICK.
#
# When the bird lets go, the ropes fall slack. The banner switches to its pictures without ropes (ROPE_CLEAR clears
# those columns), and the ropes become their own sprite in slot SLOT - 1, behind the banner: one 16x32 column
# ROPE_TOP px below the banner's top. It plays ROPES' poses (ROPE_POSES) in turn: the fall (FALL, ROPE_TIME frames
# each), where they swing down, past and back, then the sway (SWAY, SWAY_TIME frames each) on a loop. Each rope keeps
# a short stub on the cloth (STUB px, at its KNOTS angle) and swings from where that bends. While ROPES_DRAWN is
# True, each build draws ROPES from the settings; set it to False to paint it by hand.
#
# The bird has to be in front of the rope it holds. The title draws its sprites before the per-frame call, with the
# bird (2 columns, 2 tiles tall) below SLOT. So while it tows, the bird's columns, found by position, are copied to
# the 2 slots after the banner's and the originals are hidden.
ARTS = ["art/title/bannerA1C%d.png" % n for n in range(1, 7)]   # all one size, up to 128 x 32, in
                               # COLOURS' colours (index 0 clear) - else the placeholder (one picture)
COLOURS = "art/title/banner_palette.gpl"
PAINTED = ["art/title/banner_coloured/bannerA1C%d.png" % n for n in range(1, 7)]
LETTER_SWATCH = "art/title/banner_coloured/letter_colours.png"   # each letter's four colours, a row each
FRAME_TIME = 6
SEQUENCE = [0, 1, 2, 3, 4, 5]
FRAME_CALL = 0x1AF94           # jsr (the title's per-frame chain: title-menu, title-clouds)
LEAVE_CALL = 0x1B026           # jsr (the title's end chain)
BIRD = 0x1BF2E
OBJECTS, OBJECT_SIZE, LAST_OBJECT = 0x104000, 0x80, 0x107F80
ACTIVE = 0x28
GAP = 21                       # the rope starts behind the bird: its body reaches x 20-21 at the lower rope, 26-30 at the upper
DROP = 6                      # (the banner's top, below the bird's)
STOP_X = 172                   # where it is as the bird pops the balloon
SLOT = 330
ROPES = "art/title/banner_ropes.png"   # the slack ropes' poses side by side, 16 x 32 each, in COLOURS' colours
ROPE_CLEAR = 10                # the pictures' columns 0-9 are the ropes (the cloth from 10)
ROPE_TOP = 4
ROPE_TIME = 4
ROPE_STATE = 0x10EA78          # bytes (spare RAM): the ropes' pose, frames shown of it
ROPES_DRAWN = False            # True: each build draws ROPES from the settings below (and rewrites it) - False once
                               # it's painted by hand: the build reads it as it is
KNOTS = [(9.5, 7.5, 67), (9.5, 22.5, 80)]     # where each rope's tied (x, y in the picture) and its stub's angle
                                               # (degrees from hanging straight down, + towards the left: the top
                                               # one as it was towed, the bottom one out and drooping a little)
ROPE_POSES = [(37, 65), (-13, -24), (0, 0), (7, 8.5), (10, 12), (-7, -8.5), (-10, -12)]
                               # ROPES' poses: (top rope, bottom rope) angles - the first drop, the overshoot,
                               # hanging, half right, full right, half left, full left
FALL = [0, 3, 1, 6, 5]         # the fall: poses in turn, ROPE_TIME frames each
SWAY = [2, 3, 4, 3, 2, 5, 6, 5]   # then the sway, round and round, SWAY_TIME frames each
SWAY_TIME = 6


def angles():
    """Each pose's (top rope, bottom rope) angles."""
    return ROPE_POSES
ROPE_LENGTH = 14                # the stub plus the part below the bend
STUB = 2                       # (the stub left on the cloth, before the bend)
PALETTE = 0x7E
# PLUS in colour: the pictures' letters are painted in LETTER_INK; the build colours each like the logo's letters -
# its own ramp (RAMPS: the logo's, palettes 0xEB-0xEF on the title), the main colour, the top / left edges SHADE steps
# lighter, the bottom / right edges SHADE darker, and (LETTER_OUTLINE) a 1-px ring round it on the cloth in the
# ramp's darkest. 16 colours is more than one palette holds with the cloth's, so the letters are in two groups (P and
# U in LETTER_SLOTS[0], L and S in [1]) and the tiles with U or S use a second palette, SECOND_PALETTE (nothing on
# the title draws with it): PALETTE has P's and L's colours there, SECOND_PALETTE U's and S's. (No tile holds L and U,
# or P / L with U / S - the build checks.) LETTERS = None: the letters as painted.
#
# PAINTED: the pictures with their letters already coloured, for editing by hand (2026-11-08: PLUS redrawn in the
# logo's letters - L, U and S shrunk from BLUE'S, P from its B without the bottom bowl). Where they're there they're
# used instead of colouring ARTS' ink: each pixel is clear (magenta), a COLOURS colour (the cloth), or one of a
# letter's four colours (light, main, dark, outline - as letter_palettes() makes them, shown in LETTER_SWATCH), which
# also says which letter it belongs to.
LETTERS = {"P": "pink", "L": "green", "U": "orange", "S": "yellow"}
LETTER_INK = 1
SHADE = 2
LETTER_OUTLINE = True
RAMPS = {   # light to dark, the last the darkest (an outline)
    "pink": "ffeeff ffd5ff ffc5ff ffacff ff9cff e683e6 cd6acd b452b4 9c399c 832083 731073 6a086a",
    "orange": "ffeec5 ffde8b ffcd52 ffc54a ffb441 e69c29 cd8310 b46a00 9c5200 833900 7b3100 6a2000",
    "green": "bdffde acffc5 94f6b4 83f69c 6aee8b 4acd6a 29ac4a 088b29 007310 005a00 004a00 004100",
    "blue": "b4eeff acdeff 9cc5ff 94b4ff 839cff 738bee 627bde 526acd 415abd 314aac 20399c 10298b",
    "yellow": "ffff62 f6f65a f6e64a eede41 e6d531 cdbd18 b4a400 9c8b00 837300 6a5a00 625200 524100",
    "red": "ffd0c4 ffb0a0 f58a7a ea6a5a dc4a40 c52929 9c1818 8a1414 7b1010 6a0c0c 5a0a0a 520808",
}
RAMP_MAIN = 5
LETTER_SLOTS = ([10, 11, 12, 13], [14, 15, 2, 3])    # (light, main, dark, outline) for P / U, then L / S
GROUPS = {"P": 0, "L": 1, "U": 0, "S": 1}
SECOND_PALETTE = 0x7D
FIXED_PALETTE = 1              # the placeholder's
STATE = 0x10EA70               # a byte (spare RAM): 0 = not shown yet, 1 = towed, 2 = let go
BANNER_X = 0x10EA72            # two words: its x, y on screen once let go
TICK = 0x10EA76                # bytes: frames shown of this picture, the step in SEQUENCE
WHITE, RED, DARK, ROPE = 15, 13, 14, 5
FONT = {
    "P": ["11110", "11011", "11011", "11110", "11000", "11000", "11000"],
    "L": ["11000", "11000", "11000", "11000", "11000", "11000", "11111"],
    "U": ["11011", "11011", "11011", "11011", "11011", "11011", "01110"],
    "S": ["01111", "11000", "11000", "01110", "00011", "00011", "11110"],
}


def placeholder():
    """96 x 24: a rope (x 0-9), then the cloth - white, a red border, PLUS in red letters twice the font's size."""
    w, h = 96, 24
    px = [[0] * w for _ in range(h)]
    for x in range(0, 10):
        px[11][x] = px[12][x] = ROPE
    left, right = 10, 89
    for y in range(h):
        for x in range(left, right + 1):
            edge = y < 2 or y >= h - 2 or x < left + 2 or x > right - 2
            px[y][x] = RED if edge else WHITE
    for y in range(h):
        px[y][left] = px[y][left + 1] = DARK                   # the pole the rope's tied to
    x = left + (right - left + 1 - (4 * 10 + 3 * 2)) // 2
    for c in "PLUS":
        for r, row in enumerate(FONT[c]):
            for i, bit in enumerate(row):
                if bit == "1":
                    for dy in range(2):
                        for dx in range(2):
                            px[5 + 2 * r + dy][x + 2 * i + dx] = RED
        x += 12
    return px


def own_colours():
    """COLOURS' 16 colours as RGB (a GIMP palette: one 'r g b name' a line after its header)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = []
    for line in open(os.path.join(root, COLOURS)):
        parts = line.split()
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            out.append(tuple(int(p) for p in parts[:3]))
    assert 2 <= len(out) <= 16, "%s: 2-16 colours" % COLOURS
    return out + [(0, 0, 0)] * (16 - len(out))


def pictures(rom):
    """ARTS' pixels (fix palette 1 entries; 0 = clear), those that are there - else [the placeholder]."""
    from png_tiles import read_indices
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = [read_indices(os.path.join(root, a), own_colours()) for a in ARTS if os.path.exists(os.path.join(root, a))]
    for px in out:
        assert len(px) == len(out[0]) and len(px[0]) == len(out[0][0]), "the banner's pictures differ in size"
        assert len(px) <= 32 and len(px[0]) <= 128, "the banner: at most 128 x 32"
    assert not out or max(SEQUENCE) < len(out), "SEQUENCE names a picture that isn't there"
    return out or [placeholder()]


def colour_letters(px):
    """A picture with its LETTER_INK letters coloured (see LETTERS), and each pixel's letter (its own or its
    outline's; None for the rest)."""
    h, w = len(px), len(px[0])
    owner = [[None] * w for _ in range(h)]
    shapes = []
    for y in range(h):
        for x in range(w):
            if px[y][x] == LETTER_INK and owner[y][x] is None:
                todo, shape = [(y, x)], []
                owner[y][x] = len(shapes)
                while todo:
                    cy, cx = todo.pop()
                    shape.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and px[ny][nx] == LETTER_INK and owner[ny][nx] is None:
                            owner[ny][nx] = len(shapes)
                            todo.append((ny, nx))
                shapes.append(shape)
    assert len(shapes) == 4, "the banner: %d letter shapes in a picture, not P, L, U, S" % len(shapes)
    order = sorted(range(4), key=lambda i: sum(x for _, x in shapes[i]) / len(shapes[i]))
    for letter, i in zip("PLUS", order):
        for y, x in shapes[i]:
            owner[y][x] = letter
    ink = lambda y, x: 0 <= y < h and 0 <= x < w and px[y][x] == LETTER_INK
    out = [row[:] for row in px]
    for y in range(h):
        for x in range(w):
            if ink(y, x):
                light, main, dark, _ = LETTER_SLOTS[GROUPS[owner[y][x]]]
                out[y][x] = (dark if not ink(y + 1, x) or not ink(y, x + 1) else
                             light if not ink(y - 1, x) or not ink(y, x - 1) else main)
            else:
                assert px[y][x] not in LETTER_SLOTS[0] + LETTER_SLOTS[1], "the banner: cloth in a letter colour slot"
                if LETTER_OUTLINE and px[y][x]:
                    for ny, nx in ((y - 1, x), (y, x - 1), (y, x + 1), (y + 1, x)):
                        if ink(ny, nx):
                            owner[y][x] = owner[ny][nx]
                            out[y][x] = LETTER_SLOTS[GROUPS[owner[y][x]]][3]
                            break
    return out, owner


def painted_letters(path):
    """A PAINTED picture as colour_letters() gives it: its pixels (palette entries) and each pixel's letter."""
    import re
    from png_tiles import read_rgba
    gpl = [tuple(map(int, l.split()[:3])) for l in open(os.path.join(ROOT, COLOURS)) if re.match(r"\s*\d+\s+\d+\s+\d+", l)]
    pals = letter_palettes()
    letter_colour = {}                          # RGB -> (letter, its palette slot)
    for letter in "PLUS":
        for slot in LETTER_SLOTS[GROUPS[letter]]:
            letter_colour[pals[1 if letter in "US" else 0][slot]] = (letter, slot)
    rgba = read_rgba(os.path.join(ROOT, path))
    px = [[0] * len(rgba[0]) for _ in rgba]
    owner = [[None] * len(rgba[0]) for _ in rgba]
    for y, row in enumerate(rgba):
        for x, (c, a) in enumerate(row):
            if not a or c == (255, 0, 255):
                continue
            if c in letter_colour:
                owner[y][x], px[y][x] = letter_colour[c]
            else:
                assert c in gpl[1:], "%s: pixel %d,%d is #%02x%02x%02x - not the cloth's or a letter's colour" % (
                    path, x, y, *c)
                px[y][x] = gpl.index(c)
                assert px[y][x] not in LETTER_SLOTS[0] + LETTER_SLOTS[1], "%s: cloth in a letter colour slot" % path
    return px, owner


def letter_palettes():
    """(PALETTE's, SECOND_PALETTE's) 16 colours: COLOURS with P / L's, U / S's letter colours in their slots."""
    out = []
    for pair in ("PL", "US"):
        colours = own_colours()
        for letter in pair:
            ramp = [tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for c in RAMPS[LETTERS[letter]].split()]
            picks = [RAMP_MAIN - SHADE, RAMP_MAIN, RAMP_MAIN + SHADE, len(ramp) - 1]
            for slot, pick in zip(LETTER_SLOTS[GROUPS[letter]], picks):
                colours[slot] = ramp[pick]
        out.append(colours)
    return out


def draw_ropes():
    """ROPES' poses, drawn: each rope ~2.5 px thick, twisted (colours 7 / 8 / 9, as in the pictures), its edges dark
    (9) - a stub STUB px long out of the cloth at its KNOTS angle, then bent at its end, at the pose's angle."""
    import math
    out = []

    def segment(px, x0, y0, angle, length, t0):
        a = math.radians(angle)
        dx, dy = -math.sin(a), math.cos(a)
        for y in range(32):
            for x in range(16):
                cx, cy = x + 0.5 - x0, y + ROPE_TOP + 0.5 - y0
                t = cx * dx + cy * dy                  # along the rope
                v = cx * dy - cy * dx                  # across it
                if -0.6 <= t <= length and abs(v) <= 1.25:
                    if abs(v) > 0.75:
                        px[y][x] = 9
                    elif not px[y][x] or px[y][x] == 9:
                        px[y][x] = [7, 8, 9][int(math.floor((t + t0) * 0.7 + v * 0.9)) % 3]

    for pose in angles():
        px = [[0] * 16 for _ in range(32)]
        for (kx, ky, stub), angle in zip(KNOTS, pose):
            a = math.radians(stub)
            bx, by = kx - math.sin(a) * STUB, ky + math.cos(a) * STUB      # the bend
            segment(px, bx, by, angle, ROPE_LENGTH - STUB, STUB)
            segment(px, kx, ky, stub, STUB, 0)
        out.append(px)
    return out


def rope_poses():
    """ROPES' poses (16 x 32 each) - drawn from the settings (and written to ROPES) while ROPES_DRAWN or it isn't
    there."""
    from png_tiles import read_indices, write_indexed
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ROPES)
    if ROPES_DRAWN or not os.path.exists(path):
        poses = draw_ropes()
        write_indexed(path, [sum((p[y] for p in poses), []) for y in range(32)], own_colours())
        return poses
    px = read_indices(path, own_colours())
    assert len(px) == 32 and len(px[0]) % 16 == 0, "%s: 16 x 32 poses side by side" % ROPES
    return [[row[n * 16:n * 16 + 16] for row in px] for n in range(len(px[0]) // 16)]


def apply(rom):
    frames = pictures(rom)
    from png_tiles import rgb_to_neo
    own = any(os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), a)) for a in ARTS)
    palette = PALETTE if own else FIXED_PALETTE
    coloured = bool(LETTERS) and own
    copy = ("".join("""    lea colours+%d(%%pc),%%a1          | its colours, while it's drawn
    lea 0x%X,%%a0
    moveq #15,%%d4
0:  move.w (%%a1)+,(%%a0)+
    dbf %%d4,0b
""" % (n * 32, 0x400000 + p * 32) for n, p in enumerate([PALETTE, SECOND_PALETTE] if coloured else [PALETTE]))
            if own else "")
    palettes = letter_palettes() if coloured else [own_colours()]
    colour_words = ",".join("0x%04X" % (rgb_to_neo(c) if i else 0) for colours in palettes for i, c in enumerate(colours))
    width, height = len(frames[0][0]), len(frames[0])
    cols, rows = (width + 15) // 16, (height + 15) // 16
    owners = None
    if coloured:
        painted = all(os.path.exists(os.path.join(ROOT, p)) for p in PAINTED)
        done = [painted_letters(p) for p in PAINTED] if painted else [colour_letters(px) for px in frames]
        frames, owners = [f for f, _ in done], [o for _, o in done]

    def tile_palette(n, c, r):
        """The palette for picture n's tile (c, r): SECOND_PALETTE with U or S in it."""
        if not owners:
            return palette
        there = {owners[n][y][x] for y in range(r * 16, min(height, r * 16 + 16))
                 for x in range(c * 16, min(width, c * 16 + 16))} - {None}
        assert not (there & set("PL") and there & set("US")), "banner %d, tile %d,%d holds %s" % (n + 1, c, r, there)
        return SECOND_PALETTE if there & set("US") else PALETTE
    tiles = [[[rom.add_sprite_tile([[px[r * 16 + y][c * 16 + x] if r * 16 + y < height and c * 16 + x < width else 0
                                     for x in range(16)] for y in range(16)],
                                   why="title banner %d, column %d row %d" % (n + 1, c, r), share=True)
               for r in range(rows)] for c in range(cols)] for n, px in enumerate(frames)]
    loose = [[[rom.add_sprite_tile([[px[r * 16 + y][c * 16 + x] if r * 16 + y < height and c * 16 + x < width
                                      and c * 16 + x >= ROPE_CLEAR else 0 for x in range(16)] for y in range(16)],
                                   why="title banner %d let go, column %d row %d" % (n + 1, c, r), share=True)
               for r in range(rows)] for c in range(cols)] for n, px in enumerate(frames)]
    poses = rope_poses()
    assert max(FALL + SWAY) < len(poses), "FALL / SWAY name a rope pose that isn't in %s" % ROPES
    rope_tiles = [rom.add_sprite_tile(pose[r * 16:r * 16 + 16], why="title banner's ropes, pose %d tile %d" % (n + 1, r),
                                      share=True) for n, pose in enumerate(poses) for r in range(2)]
    frame_before, leave_before = rom.u32(FRAME_CALL + 2), rom.u32(LEAVE_CALL + 2)
    assert rom.u16(FRAME_CALL) == 0x4EB9 and rom.u16(LEAVE_CALL) == 0x4EB9
    tile_words = ",".join("0x%04X,0x%04X" % (t & 0xFFFF, tile_palette(n, c, r) << 8 | (t >> 16) << 4)
                          for n, picture in enumerate(tiles) for c, col in enumerate(picture) for r, t in enumerate(col))
    loose_words = ",".join("0x%04X,0x%04X" % (t & 0xFFFF, tile_palette(n, c, r) << 8 | (t >> 16) << 4)
                           for n, picture in enumerate(loose) for c, col in enumerate(picture) for r, t in enumerate(col))
    rope_words = ",".join("0x%04X,0x%04X" % (t & 0xFFFF, palette << 8 | (t >> 16) << 4) for t in rope_tiles)
    bird_slot = SLOT + cols
    assert bird_slot + 2 <= 380
    hides = "".join("    move.w #0x%X,0x3C0000\n    move.w #0,0x3C0002\n" % (0x8200 + SLOT + c) for c in range(-1, cols + 1))
    code = rom.place_code(r"""
    bra.w frame
    bra.w leave

leave:
    jsr 0x%(leave_before)X
    move.l %%d0,-(%%sp)
    move.w #1,0x3C0004
%(hides)s    clr.b 0x%(state)X
    clr.w 0x%(tick)X
    clr.w 0x%(rope)X
    move.l (%%sp)+,%%d0
    rts

frame:
    jsr 0x%(frame_before)X
    movem.l %%d0-%%d4/%%a0-%%a1,-(%%sp)
    cmpi.b #2,0x%(state)X
    beq 5f                              | let go: where it stopped
    lea 0x%(objects)X,%%a0              | the bird, if it's out
1:  tst.b %(active)d(%%a0)
    beq 2f
    cmpi.l #0x%(bird)X,4(%%a0)
    beq 3f
2:  lea %(size)d(%%a0),%%a0
    cmpa.l #0x%(last)X,%%a0
    bls 1b
    bra 9f                              | none: not drawn
3:  move.b #1,0x%(state)X
    bsr lift
    move.w 2(%%a0),%%d0                 | x on screen: 2 * x - 127, then behind the bird
    lsr.w #7,%%d0
    sub.w #127-%(gap)d,%%d0
    move.w (%%a0),%%d1                  | y on screen: y - 20, then a little lower
    lsr.w #8,%%d1
    add.w #%(drop)d-20,%%d1
    cmpi.w #%(stop)d,%%d0
    bgt 6f
    move.w #%(stop)d,%%d0               | there: let go
    move.w %%d0,0x%(banner_x)X
    move.w %%d1,0x%(banner_x)X+2
    move.b #2,0x%(state)X
    clr.w 0x%(rope)X
    bra 6f
5:  move.w #1,0x3C0004                  | let go: the bird back where the game draws it
    move.w #0x%(bird_scb3)X,0x3C0000
    move.w #0,0x3C0002
    move.w 0x%(banner_x)X,%%d0
    move.w 0x%(banner_x)X+2,%%d1
6:
%(copy)s    move.w #1,0x3C0004                  | the banner: COLS columns from SLOT, the first at x, y
    and.w #511,%%d0
    lsl.w #7,%%d0
    move.w #496,%%d2
    sub.w %%d1,%%d2
    and.w #511,%%d2
    lsl.w #7,%%d2
    addq.w #%(rows)d,%%d2               | its height in tiles
    moveq #0,%%d4                       | this step's picture
    move.b 0x%(tick)X+1,%%d4
    lea sequence(%%pc),%%a1
    move.b (%%a1,%%d4.w),%%d4
    lea tiles(%%pc),%%a1
    cmpi.b #2,0x%(state)X
    bne 0f
    lea loose(%%pc),%%a1                | let go: without the ropes
0:  mulu #%(cols)d*%(rows)d*4,%%d4
    adda.l %%d4,%%a1
    moveq #0,%%d3
7:  move.w %%d3,%%d4                    | SCB1: the column's tiles
    add.w #%(slot)d,%%d4
    lsl.w #6,%%d4
    move.w %%d4,0x3C0000
    moveq #%(rows)d*2-1,%%d4
8:  move.w (%%a1)+,0x3C0002
    dbf %%d4,8b
    move.w %%d3,%%d4
    add.w #%(slot)d+0x8000,%%d4         | SCB2: full size
    move.w %%d4,0x3C0000
    move.w #0x0FFF,0x3C0002
    add.w #0x200,%%d4                   | SCB3: y, height (the others stick to the first)
    move.w %%d4,0x3C0000
    move.w %%d2,0x3C0002
    add.w #0x200,%%d4                   | SCB4: x
    move.w %%d4,0x3C0000
    move.w %%d0,0x3C0002
    move.w #0x40+%(rows)d,%%d2           | the rest: sticky
    addq.w #1,%%d3
    cmpi.w #%(cols)d,%%d3
    bne 7b
    cmpi.b #2,0x%(state)X
    bne 0f
    bsr ropes
0:  addq.b #1,0x%(tick)X                | the next picture after FRAME_TIME frames
    cmpi.b #%(frame_time)d,0x%(tick)X
    bne 9f
    clr.b 0x%(tick)X
    addq.b #1,0x%(tick)X+1
    cmpi.b #%(steps)d,0x%(tick)X+1
    bne 9f
    clr.b 0x%(tick)X+1
9:  movem.l (%%sp)+,%%d0-%%d4/%%a0-%%a1
    rts

ropes:                                  | (let go) the slack ropes: this pose, behind the banner
    moveq #0,%%d4
    move.b 0x%(rope)X,%%d4              | the step in the fall + the sway: its pose
    lea rope_steps(%%pc),%%a1
    move.b (%%a1,%%d4.w),%%d4
    lsl.w #3,%%d4
    lea rope_tiles(%%pc),%%a1
    adda.w %%d4,%%a1
    move.w #%(rope_slot)d*64,0x3C0000
    moveq #3,%%d4
1:  move.w (%%a1)+,0x3C0002
    dbf %%d4,1b
    move.w #0x8000+%(rope_slot)d,0x3C0000
    move.w #0x0FFF,0x3C0002
    move.w #496-%(rope_top)d,%%d2       | SCB3: ROPE_TOP below the banner's top, 2 tiles
    sub.w 0x%(banner_x)X+2,%%d2
    and.w #511,%%d2
    lsl.w #7,%%d2
    addq.w #2,%%d2
    move.w #0x8200+%(rope_slot)d,0x3C0000
    move.w %%d2,0x3C0002
    move.w #0x8400+%(rope_slot)d,0x3C0000
    move.w %%d0,0x3C0002                | the banner's x
    addq.b #1,0x%(rope)X+1              | the next pose after ROPE_TIME frames (the fall) / SWAY_TIME (the sway)
    move.b #%(rope_time)d,%%d4
    cmpi.b #%(sway_from)d,0x%(rope)X
    bcs 1f
    move.b #%(sway_time)d,%%d4
1:  cmp.b 0x%(rope)X+1,%%d4
    bhi 9f
    clr.b 0x%(rope)X+1
    addq.b #1,0x%(rope)X
    cmpi.b #%(last_pose)d,0x%(rope)X
    bls 9f
    move.b #%(sway_from)d,0x%(rope)X    | round again
9:  rts

lift:                                   | the bird (a0) drawn after the banner
    movem.l %%d0-%%d7,-(%%sp)
    move.w #1,0x3C0004
    move.w 2(%%a0),%%d0                 | where the game drew it: x, its SCB3's y
    lsr.w #7,%%d0
    sub.w #127,%%d0
    and.w #511,%%d0
    move.w (%%a0),%%d1
    lsr.w #8,%%d1
    sub.w #20,%%d1
    move.w #496,%%d2
    sub.w %%d1,%%d2
    and.w #511,%%d2
    moveq #1,%%d3                       | its first column: height 2, not sticky, at that place
1:  move.w %%d3,%%d4
    add.w #0x8200,%%d4
    move.w %%d4,0x3C0000
    move.w 0x3C0002,%%d5
    move.w %%d5,%%d6
    and.w #0x7F,%%d6
    cmpi.w #2,%%d6
    bne 2f
    lsr.w #7,%%d5
    sub.w %%d2,%%d5
    addq.w #1,%%d5
    cmpi.w #3,%%d5
    bcc 2f
    add.w #0x200,%%d4
    move.w %%d4,0x3C0000
    move.w 0x3C0002,%%d5
    lsr.w #7,%%d5
    sub.w %%d0,%%d5
    addq.w #1,%%d5
    cmpi.w #4,%%d5
    bcs 3f
2:  addq.w #1,%%d3
    cmpi.w #%(slot)d,%%d3
    bcs 1b
    move.w #0x%(bird_scb3)X,0x3C0000    | not found: ours hidden
    move.w #0,0x3C0002
    bra 9f
3:  move.w #%(bird_slot)d,%%d2         | its 2 columns (2 tiles tall) copied, the game's hidden
    moveq #2,%%d0
    moveq #4,%%d1
    bsr move_cols
9:  movem.l (%%sp)+,%%d0-%%d7
    rts

move_cols:                              | d0 columns (d1 SCB1 words each) from slot d3 to slot d2; d3's hidden
    movem.l %%d0-%%d7,-(%%sp)
    moveq #0,%%d7
1:  move.w %%d3,%%d4
    add.w %%d7,%%d4
    lsl.w #6,%%d4
    move.w %%d2,%%d5
    add.w %%d7,%%d5
    lsl.w #6,%%d5
    move.w %%d1,%%d6
    subq.w #1,%%d6
2:  bsr copy_word                       | SCB1: its tiles
    addq.w #1,%%d4
    addq.w #1,%%d5
    dbf %%d6,2b
    move.w %%d3,%%d4
    add.w %%d7,%%d4
    add.w #0x8000,%%d4
    move.w %%d2,%%d5
    add.w %%d7,%%d5
    add.w #0x8000,%%d5
    moveq #2,%%d6                       | SCB2-4
3:  bsr copy_word
    add.w #0x200,%%d4
    add.w #0x200,%%d5
    dbf %%d6,3b
    addq.w #1,%%d7
    cmp.w %%d0,%%d7
    bne 1b
    add.w #0x8200,%%d3                  | the original hidden (the rest stick to it)
    move.w %%d3,0x3C0000
    move.w #0,0x3C0002
    movem.l (%%sp)+,%%d0-%%d7
    rts

copy_word:                              | VRAM d4 -> d5
    move.w %%d4,0x3C0000
    movea.w 0x3C0002,%%a1
    move.w %%d5,0x3C0000
    move.w %%a1,0x3C0002
    rts
colours:
    .word %(colours)s
sequence:
    .byte %(sequence)s
    .even
tiles:
    .word %(tiles)s
loose:
    .word %(loose)s
rope_tiles:
    .word %(rope_tiles)s
rope_steps:
    .byte %(rope_steps)s
    .even
""" % {"frame_before": frame_before, "leave_before": leave_before, "hides": hides, "state": STATE,
       "banner_x": BANNER_X, "objects": OBJECTS, "active": ACTIVE, "bird": BIRD, "size": OBJECT_SIZE,
       "last": LAST_OBJECT, "gap": GAP, "drop": DROP, "stop": STOP_X, "slot": SLOT, "rows": rows, "cols": cols,
       "tiles": tile_words, "tick": TICK, "frame_time": FRAME_TIME, "steps": len(SEQUENCE),
       "sequence": ",".join(str(n) for n in SEQUENCE), "colours": colour_words, "copy": copy,
       "bird_slot": bird_slot, "bird_scb3": 0x8200 + bird_slot,
       "loose": loose_words, "rope_tiles": rope_words, "rope": ROPE_STATE, "rope_slot": SLOT - 1, "rope_top": ROPE_TOP,
       "rope_time": ROPE_TIME, "last_pose": len(FALL) + len(SWAY) - 1, "rope_steps": ",".join(str(n) for n in FALL + SWAY),
       "sway_time": SWAY_TIME, "sway_from": len(FALL)},
        why="title: the bird's PLUS banner")
    rom.write(FRAME_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + frame_before.to_bytes(4, "big"), why="title: the banner every frame")
    rom.write(LEAVE_CALL, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + leave_before.to_bytes(4, "big"), why="title: the banner hidden as it ends")

