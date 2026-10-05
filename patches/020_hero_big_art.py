NAME = "hero-big-art"
DESCRIPTION = "Draw the normal-size hero with the big (powerup) artwork; gameplay (collisions, timing) unchanged"

# How the game picks a hero frame: every object has an "art set" word at object+98 (0x104062 for
# player 1's hero): 0 = normal, 0x40 = shrunk (the C-button shrink), 0x80 = the big powerup form.
# The animation lookup at 0x434C4 adds it to the animation number (+102) to index the animation table
# (0x5393A), so animation N exists in three variants: N, 0x40+N and 0x80+N. Each is a sequence of frame
# words ending in FFFF (hold) or FFFE (loop); the step routine stores each frame in object+8 (0x43520, or
# 0x4354E for a frame followed by a command word), leaving a0 just past that word.
#
# The frame in +8 is not only drawn: the collision code takes the object's collision box from it (table
# 0x64772), so the big frames made the hero collide like the powered-up form - e.g. the first level's
# trap door took him through without the key. So the hero keeps running the normal animations (+8 holds
# the normal frames, gameplay is the original) and only the drawing swaps in the big art:
#   * at each animation step of the normal-size hero, the big frame at the same position of big animation
#     N+0x80 (a table built from the ROM below; positions past its end use its last frame) is stored next
#     to the normal frame it goes with (RAM, per player);
#   * the drawing routine (0xA428, where it looks up the frame in +8) draws that big frame instead while +8
#     still holds that normal frame. If +8 was set some other way (e.g. the blink's empty frame) it uses a
#     plain normal->big frame table, or draws +8 as it is.
#   * drawing a flipped object also stores a width-based offset in object+34 (0xA4FC, from the drawn
#     frame's width in tiles), and the collision code uses it to place a flipped object's collision box.
#     For the hero drawn with a big frame, +34 is set back to what the normal frame's width gives (the
#     drawing itself keeps the big frame's value). The same goes for +36 from the frame's height (0xA55A,
#     used while the hero is zoomed by the C-button shrink).
# Only normal-size frames are swapped, so the shrunk and powerup forms are untouched - except while the
# C-button shrink zooms the normal frame down or back up, which is then the big art zooming.
#
# The big art is drawn from the same top-left anchor as the small art, so it hangs lower and
# extends further right than it should. The sprite drawing routine (0xA5B2-0xA6E0) writes each
# object's position to the video chip in two variants (the plain one, and one used while the object
# is being zoomed during transformation animations); an object's first word (a0@(0)) becomes its
# SCB3 Y and its second word (a0@(2)) its SCB4 X. Four small hooks nudge the hero's big art back:
#   * up by HERO_UP_PX pixels (SCB3 is 496-y in units of 128 per pixel, so bigger = higher),
#   * left by HERO_LEFT_PX pixels facing right, or HERO_LEFT_PX_FACING_LEFT facing left (both measured).
# The genuine powerup (art set 0x80) is left alone: the game already shifts the hero on pickup.
ANIM_TABLE = 0x5393A
STEP_SITES = [0x43520, 0x4354E]   # move.w d0,8(a5) ; andi.w #3,d1  = 3B40 0008 0241 0003
DRAW_FRAME = 0xA428               # move.w 8(a0),d3 ; move.l (a3,d3.w),a5  = 3628 0008 2A73 3000
NORMAL_ANIMS = 0x40
NORMAL_FRAMES = 0x190             # the normal hero's frames are 0-0x18C (0x134-0x174 the idle fidget, 0x178-0x180
                                  # swimming)
# Animations whose big version doesn't fit:
#   0x2D, the idle fidget (after standing still a while he bends down, picks something up and looks at it):
#     the big form has no such art (its 0x2D is the standing pose), so he stands and breathes - the big
#     standing pair 0x364 / 0x368 alternating with each fidget frame;
#   0x2B (frames 0x184-0x18C, sparkles rather than the hero) is left as it is.
#   0x18, swimming: the big version's fourth frame (0x33C) is a walking pose, so the swim cycle flashed upright
#     every fourth frame; like the normal cycle (0x6C 0x70 0x74 0x70) it repeats its second pose instead.
ROW_OVERRIDES = {0x2D: "breathe", 0x2B: "none", 0x18: [0x330, 0x334, 0x338, 0x334]}
BREATHE = (0x364, 0x368)
PAIR_RAM = [0x10EA20, 0x10EA30]   # spare RAM per player: +0 normal frame, +2 the big frame drawn for it, +4 the
                                  # normal frame's width in tiles, +5 1 if this draw used the big frame, +6 its
                                  # height, +7 which of +34 / +36 / +38 (bits 0-2) to set back after the draw,
                                  # +8 / +10 / +12 the values to set them to
# The C-button shrink zooms the hero (object+38: horizontal and vertical zoom bytes, 0xFF = full size) from
# full size down to 0xC7 and then shows the shrunk form's art; growing back zooms from 0x7F up. The big art
# is half as tall again as the normal art, so at those ends it would still be much bigger than the shrunk
# art it switches with: while drawn big it is zoomed further - 0xFF - (0xFF - zoom) * ZOOM_x / 16, which
# makes both ends match what the normal art showed (the zoom is set back after the draw).
ZOOM_SHRINK = 35
ZOOM_GROW = 22
DRAW_LOOP_RETURN = 0xA3FE         # the object drawing loop calls the drawing routine with this return address
FLIP_OFFSET = 0xA4FC              # computes object+34 from the drawn frame's width: move.b 33(a0),d6 ; andi.b #12,d6
HEIGHT_OFFSET = 0xA55A            # and object+36 from its height (zoomed drawing): move.b 33(a0),d6 ; andi.b #3,d6
HERO_OBJECTS = [0x104000, 0x104080]   # the objects for player 1 and player 2
# Red (the ending's rival: his duel, his scenes) is another object drawing player 2's copies of the hero frames
# (0x800 further on). The drawing hook notes such an object in RED_OBJ (forgotten once it draws something else)
# and treats it as a third hero, with its own pair RAM - so he is drawn with the big art too.
RED_PAIR = 0x10EA40
RED_OBJ = 0x10EA50
RED_CODE = (0x23000, 0x25400)   # ... running the ending's code (its scenes and the duel: 0x234xx-0x2530x)
BIG_SET = 0x80
# The big form has no throwing poses (its throw animations 0x23-0x26 + 0x80 are an empty frame), so the
# normal throw's frames are drawn with two big poses from the ROM: the wind-up (arm back) with an unused
# arm-raised frame, the release (arm forward) with the arm-out pose.
BIG_WINDUP, BIG_RELEASE = 0x384, 0x3BC
FRAME_SUBSTITUTES = {0xB0: BIG_WINDUP, 0xB4: BIG_RELEASE, 0xB8: BIG_WINDUP, 0xBC: BIG_RELEASE,
                     0xC0: BIG_WINDUP, 0xC4: BIG_RELEASE, 0xC8: BIG_WINDUP, 0xCC: BIG_RELEASE,
                     # throwing a carried enemy (animation 0x20), and the lying-down throws (0x21 / 0x22)
                     # with the big crawling poses
                     0x8C: BIG_WINDUP, 0x90: BIG_RELEASE, 0x94: 0x330, 0x98: 0x334, 0x9C: 0x338}
HERO_UP_PX = 15
# Burning in lava (hero state 33) he flails in charred art: animation 0x31, frames 0x11C-0x128 in palette 0x5C,
# which the lava stage makes charred (elsewhere 0x31 is the landing from some jumps and keeps the big art). The big
# form has no charred version: in state 33 those frames are drawn as copies scaled up 1.5x from the small ones (new
# frames; player 2 draws them too - no copies 0x800 further on, which aren't free).
BURN_ANIMS = [0x31]
BURN_MODE = 0         # (their definitions' mode byte, as the big art's frames)
# ... per hero state (+104): the big art is lined up by its feet, which is wrong where the hero hangs by his hands:
#   44, hanging from the balloon (player 2 floating in): the big pose's hands are 2px lower in its frame than the
#   normal pose's, so it only goes up 2px (15 lifted his hands well above the balloon's string)
# (by state, not animation: hanging from a swinging vine, state 20, uses the same animation, 0x1C, and is right
# as it is)
UP_PX = {44: 2}
# ... and further toward the art's back per state (mirrored facing left):
#   44, hanging from the balloon: the big pose's raised hand is ~10px further out than the normal pose's, so the
#     string ran through his body; 10px more puts the hand on the string, the body beside it
SIDE_PX = {44: 10}
STATES = 0x80
# An enemy the hero carries sits on his head: the routine at CARRIED_CODE (the carried enemy's code) puts it
# above the normal hero's head every frame, so with the big art it is drawn CARRY_UP_PX higher.
CARRIED_CODE = 0x466B6
CARRY_UP_PX = 16
HERO_LEFT_PX = 5           # facing right: the big art is centred ~5px right of the small art's centre
HERO_LEFT_PX_FACING_LEFT = 10   # facing left: it sits ~10px right of centre (measured), so it needs twice the nudge
# Climbing a vine (hero state 20, object+104) the big art's hands are ~12px right of the vine (the small
# art grips it), so while climbing it is moved that much further toward the hands' side.
VINE_STATES = [20]
VINE_PX = 12

DRAW_X_ZOOMED = 0xA604    # subi.w #0x4000,d5 ; move.w #256,d6
DRAW_X_PLAIN = 0xA6AA     # subi.w #0x4000,d6 ; move.w d6,(a2)
DRAW_Y_ZOOMED = 0xA64A    # subi.w #-18433,d5 ; moveq #1,d6
DRAW_Y_PLAIN = 0xA6C0     # subi.w #-18433,d7 ; add.w d3,d7 ; move.w d7,(a2)
# The hero is drawn as a main sprite (the four hooks above) plus extra pieces written by the routine
# at 0xAF1C, whose base position is built here as d7 = (Y << 16) | X:
#   subi.w #-18433,d7 ; swap d7 ; move.w 664(a6),d7 ; subi.w #0x4000,d7
PIECES_BASE = 0xA6E6
# All of the above is the variant for a hero facing RIGHT (the game draws left-facing art and flips
# it: the main drawing function at 0xA426 jumps to 0xA67A when bit 7 of object+33 is set). A hero
# facing LEFT and not being zoomed is drawn by an inline copy of the same three steps instead:
LEFT_X = 0xA480           # subi.w #0x4000,d5 ; move.w d5,(a2)
LEFT_Y = 0xA496           # subi.w #-18433,d7 ; add.w d3,d7 ; move.w d7,(a2)
LEFT_PIECES = 0xA4BE      # subi.w #-18433,d7 ; swap d7 ; move.w 2(a0),d7 ; subi.w #0x4000,d7
# ... and the zoomed variant of the facing-right path (0xA72C; the C-button shrink zooms the hero down):
RIGHT_X_ZOOMED = 0xA794   # subi.w #0x4000,d6 ; move.w d6,(a2)
RIGHT_Y_ZOOMED = 0xA7C4   # subi.w #-18433,d5 ; moveq #1,d6


import os
_DEBUG_MARKS = bool(os.environ.get("BJ_DEBUG_MARKS"))   # diagnostic build: count hero draws per hook
_marks = {}


def hero_only(reg, body, tag=""):
    """68000 source that runs `body` only for our hero while it is being drawn with a big frame (the flag
    the drawing hook sets in PAIR_RAM +5), else skips it. `tag` makes the labels unique when one routine
    uses this more than once."""
    checks = "".join("    cmpa.l #0x%X,%%%s\n    beq hero%s_%d\n" % (obj, reg, tag, i) for i, obj in enumerate(HERO_OBJECTS))
    checks += "    cmpa.l 0x%X,%%%s\n    beq hero%s_%d\n" % (RED_OBJ, reg, tag, len(HERO_OBJECTS))
    flags = "".join("hero%s_%d:\n    tst.b 0x%X\n    beq done%s\n    bra hero%s\n" % (tag, i, ram + 5, tag, tag)
                    for i, ram in enumerate(PAIR_RAM + [RED_PAIR]))
    mark = ""
    if _DEBUG_MARKS:
        mark = "    addq.b #1,0x%X\n" % (0x10E700 + len(_marks))
        _marks[len(_marks)] = tag
    return (checks + "    bra done%s\n%shero%s:\n%s%sdone%s:\n"
            % (tag, flags, tag, mark, body, tag))


_vine_labels = [0]


def x_shift(dreg, px=None, facing_left=False):
    """Nudge the big art left (plus the vine-climbing correction while on a vine; mirrored facing left)."""
    _vine_labels[0] += 1
    n = _vine_labels[0]
    checks = "".join("    cmp.b #%d,104(%%a0)\n    beq vine%d\n" % (st, n) for st in VINE_STATES)
    vine = "    %s.w #%d,%%%s\n" % ("add" if facing_left else "sub", VINE_PX * 128, dreg)
    per_anim = ("    movem.l %%d0/%%a1,-(%%sp)\n    moveq #0,%%d0\n    move.b 104(%%a0),%%d0\n    and.w #0x7F,%%d0\n"
                "    add.w %%d0,%%d0\n    lea 0x%X,%%a1\n    move.w (%%a1,%%d0.w),%%d0\n    %s.w %%d0,%%%s\n"
                "    movem.l (%%sp)+,%%d0/%%a1\n" % (_side_table[0], "add" if facing_left else "sub", dreg))
    return ("    sub.w #%d,%%%s\n" % ((HERO_LEFT_PX if px is None else px) * 128, dreg) + per_anim +
            checks + "    bra novine%d\nvine%d:\n%snovine%d:\n" % (n, n, vine, n))


_up_table = [None]
_side_table = [None]


def y_shift(dreg):
    """Raise the big art by the hero's state's entry in the UP_PX table (HERO_UP_PX unless overridden)."""
    return ("    movem.l %%d0/%%a1,-(%%sp)\n    moveq #0,%%d0\n    move.b 104(%%a0),%%d0\n    and.w #0x7F,%%d0\n"
            "    add.w %%d0,%%d0\n    lea 0x%X,%%a1\n    move.w (%%a1,%%d0.w),%%d0\n    add.w %%d0,%%%s\n"
            "    movem.l (%%sp)+,%%d0/%%a1\n" % (_up_table[0], dreg))


def carried_shift(dreg, tag=""):
    """Raise an enemy being carried (code CARRIED_CODE; +126 = which player carries it) while that player's
    hero is drawn big - drawing only, its real position is the game's."""
    return ("    cmpi.l #0x%X,4(%%a0)\n    bne cdone%s\n    tst.b 126(%%a0)\n    bne cp2%s\n    tst.b 0x%X\n"
            "    bra ctest%s\ncp2%s:\n    tst.b 0x%X\nctest%s:\n    beq cdone%s\n    add.w #%d,%%%s\ncdone%s:\n"
            % (CARRIED_CODE, tag, tag, PAIR_RAM[0] + 5, tag, tag, PAIR_RAM[1] + 5, tag, tag, CARRY_UP_PX * 128,
               dreg, tag))


def hook(rom, site, expect_hex, source, why):
    """Replace the instructions at `site` (expect_hex) with a jsr into new code holding `source`."""
    expect = bytes.fromhex(expect_hex)
    assert len(expect) >= 6
    cave = rom.place_code(source, why=why)
    rom.write(site, bytes.fromhex("4EB9") + cave.to_bytes(4, "big") + bytes.fromhex("4E71") * ((len(expect) - 6) // 2),
              expect=expect, why="now goes through the new code above")


def big_frame_tables(rom):
    """(rows, frame_map): rows[N][i] = the big frame for word i of normal animation N (0 = none), and a
    normal frame -> big frame table from the first place each normal frame is paired."""
    def words(p):
        out = []
        while len(out) < 64:
            w = rom.u16(p + 2 * len(out))
            out.append(w)
            if w >= 0xFFFE:
                break
        return out

    def is_frame(ws, i):   # a frame word, not a terminator or the parameter word after a command frame
        w = ws[i]
        return w < 0xFFFE and not (i > 0 and 0x8000 <= ws[i - 1] < 0xFFFE)
    rows, frame_map = [], {}
    for n in range(NORMAL_ANIMS):
        small = words(rom.u32(ANIM_TABLE + 4 * n))
        big = words(rom.u32(ANIM_TABLE + 4 * (n + BIG_SET)))
        big_frames = [i for i in range(len(big)) if is_frame(big, i)]
        row = []
        for i in range(len(small)):
            if not is_frame(small, i) or not big_frames:
                row.append(0)
                continue
            j = max([k for k in big_frames if k <= i] or [big_frames[0]])
            b = big[j] & 0x3FFC
            if ROW_OVERRIDES.get(n) == "none":
                row.append(0)
                continue
            if isinstance(ROW_OVERRIDES.get(n), list):
                b = ROW_OVERRIDES[n][sum(1 for k in range(i) if is_frame(small, k)) % len(ROW_OVERRIDES[n])]
            if ROW_OVERRIDES.get(n) == "breathe":
                b = BREATHE[sum(1 for k in range(i) if is_frame(small, k)) % 2]
            row.append(b)
            if (small[i] & 0x3FFC) < NORMAL_FRAMES:
                frame_map.setdefault(small[i] & 0x3FFC, b)
        rows.append(row)
    frame_map.update(FRAME_SUBSTITUTES)
    return rows, frame_map


def frame_pixels(rom, frame):
    """({(x, y): colour} of an original frame - its main block and the extra one-column pieces after it (see
    0xAF1C: tiles-1, x and y-up in 2px units, palette, high byte, the tiles) - from the main block's top left;
    and its palette)."""
    import hackbuild
    p = rom.u32(hackbuild.FRAME_TABLE + frame)
    d = rom.data
    cols, rows, _, palette, hi = d[p:p + 5]
    q, px = p + 5, {}

    def tile(q, hi):
        b = d[q]
        if b == 1:
            return d[q + 3], d[q + 2], q + 4
        return (b or None), hi, q + 1

    def put(t, x0, y0):
        art = rom.sprite_tile(t)
        for y in range(16):
            for x in range(16):
                if art[y][x]:
                    px[x0 + x, y0 + y] = art[y][x]
    for c in range(cols + 1):
        for r in range(rows + 1):
            b, hi, q = tile(q, hi)
            if b:
                put(hi << 8 | b, c * 16, r * 16)
    while d[q] != 0xFF:
        n, x, up, _, hi = d[q:q + 5]
        q += 5
        x, up = (x ^ 0x80) - 0x80, (up ^ 0x80) - 0x80
        for r in range(n + 1):
            b, hi, q = tile(q, hi)
            if b:
                put(hi << 8 | b, x * 2, r * 16 - up * 2)
    return px, palette


def upscaled_frame(rom, frame):
    """A new frame: `frame` (with its pieces) drawn 1.5x as big (each pixel to 1 or 2 rows / columns, nearest).
    The main block grows from its top left; whatever lies outside it becomes pieces again."""
    src, palette = frame_pixels(rom, frame)
    big = {}
    xs, ys = [x for x, _ in src], [y for _, y in src]
    for y in range(min(ys) * 3 // 2 - 1, max(ys) * 3 // 2 + 2):
        for x in range(min(xs) * 3 // 2 - 1, max(xs) * 3 // 2 + 2):
            v = src.get((x * 2 // 3, y * 2 // 3))
            if v:
                big[x, y] = v
    p = rom.u32(__import__("hackbuild").FRAME_TABLE + frame)
    main_cols, main_rows = (rom.data[p] + 1) * 3 // 2, (rom.data[p + 1] + 1) * 3 // 2
    cells = {}
    for (x, y), v in big.items():
        cells.setdefault((x // 16, y // 16), {})[x % 16, y % 16] = v

    def new_tile(cell):
        block = [[cells[cell].get((x, y), 0) for x in range(16)] for y in range(16)]
        return rom.add_sprite_tile(block, why="big burn frame 0x%X" % frame)
    out = [[new_tile((c, r)) if (c, r) in cells else None for c in range(main_cols)] for r in range(main_rows)]
    pieces = []
    for c in sorted({c for c, _ in cells}):
        rs = sorted(r for cc, r in cells if cc == c and not (0 <= c < main_cols and 0 <= r < main_rows))
        while rs:
            run = [rs.pop(0)]
            while rs and rs[0] == run[-1] + 1:
                run.append(rs.pop(0))
            pieces.append((c * 8, -run[0] * 8, [new_tile((c, r)) for r in run]))
    n = rom.add_frame(out, palette, why="big hero: burned frame 0x%X, 1.5x" % frame, pieces=pieces)
    import hackbuild
    q = rom.u32(hackbuild.FRAME_TABLE + n)
    rom.data[q + 2] = BURN_MODE
    return n


def apply(rom):
    rows, frame_map = big_frame_tables(rom)
    burned = {}
    for n in BURN_ANIMS:
        p = rom.u32(ANIM_TABLE + 4 * n)
        i = 0
        while True:
            w = rom.u16(p + 2 * i)
            if w >= 0xFFFE:
                break
            if w not in burned:
                burned[w] = upscaled_frame(rom, w)
            i += 1
    offs, off = [], 0
    for row in rows:
        offs.append(off)
        off += len(row)
    data = ("burn_tab:\n    .word %s\n" % ",".join("0x%X" % burned[f] for f in (0x11C, 0x120, 0x124, 0x128)) +
            "row_off:\n    .word %s\n" % ",".join(str(o) for o in offs) +
            "row_len:\n    .byte %s\n    .even\n" % ",".join(str(min(255, len(r))) for r in rows) +
            "rows:\n" + "".join("    .word %s\n" % ",".join("0x%X" % v for v in row) for row in rows if row) +
            "frame_map:\n    .word %s\n" % ",".join("0x%X" % frame_map.get(f, 0) for f in range(0, NORMAL_FRAMES, 4)))

    def hero_check(reg):
        return ("".join("    cmpa.l #0x%X,%%%s\n    beq 1f\n" % (obj, reg) for obj in HERO_OBJECTS) +
                "    cmpa.l 0x%X,%%%s\n    beq 1f\n" % (RED_OBJ, reg))

    def pair(reg, ram):
        return ("    lea 0x%X,%%%s\n    cmpa.l #0x%X,%%%s\n    beq 2f\n    lea 0x%X,%%%s\n    cmpa.l #0x%X,%%%s\n"
                "    beq 2f\n    lea 0x%X,%%%s\n2:\n" % (PAIR_RAM[0], ram, HERO_OBJECTS[0], reg, PAIR_RAM[1], ram,
                                                          HERO_OBJECTS[1], reg, RED_PAIR, ram))

    restores = "".join(
        "    lea 0x%X,%%a1\n    lea 0x%X,%%a0\n    btst #0,7(%%a1)\n    beq no34_%d\n    move.w 8(%%a1),34(%%a0)\n"
        "no34_%d:\n    btst #1,7(%%a1)\n    beq no36_%d\n    move.w 10(%%a1),36(%%a0)\nno36_%d:\n"
        "    btst #2,7(%%a1)\n    beq nozoom_%d\n    move.w 12(%%a1),38(%%a0)\nnozoom_%d:\n    clr.b 7(%%a1)\n"
        % (ram, obj, i, i, i, i, i, i) for i, (ram, obj) in enumerate(zip(PAIR_RAM, HERO_OBJECTS)))
    restores += ("    lea 0x%X,%%a1\n    move.l 0x%X,%%a0\n    cmpa.w #0,%%a0\n    beq nozoom_r\n    btst #0,7(%%a1)\n"
                 "    beq no34_r\n    move.w 8(%%a1),34(%%a0)\nno34_r:\n    btst #1,7(%%a1)\n    beq no36_r\n"
                 "    move.w 10(%%a1),36(%%a0)\nno36_r:\n    btst #2,7(%%a1)\n    beq nozoom_r\n    move.w 12(%%a1),38(%%a0)\n"
                 "nozoom_r:\n    clr.b 7(%%a1)\n" % (RED_PAIR, RED_OBJ))
    src = r"""
    bra.w step                      | +0: from the animation step
    bra.w draw                      | +4: from the drawing routine
    bra.w flip                      | +8: in place of the flip-offset routine 0xA4FC
    bra.w height                    | +12: in place of the height-offset routine 0xA55A

| ---- animation step: in place of `move.w d0,8(a5) ; andi.w #3,d1`; a0 = just past the frame word read
step:
    move.w %d0,8(%a5)
    andi.w #3,%d1
HERO_A5    rts
1:  movem.l %d0-%d3/%a1-%a2,-(%sp)
PAIR_A5    tst.w 98(%a5)                   | normal-size hero only (other forms: no pair noted)
    beq 6f
    move.w #0xFFFF,(%a2)
    bra 7f
6:  move.w %d0,(%a2)                | the normal frame, and the big one to draw for it:
    clr.w 2(%a2)
    moveq #0,%d2
    move.b 102(%a5),%d2             | the animation
    cmp.w #NORMAL_ANIMS,%d2
    bcc 8f
    move.w %d2,%d3
    lsl.w #2,%d3
    lea ANIM_TABLE,%a1
    move.l (%a1,%d3.w),%d3
    move.l %a0,%d1                  | the word just read, as a position in that animation
    subq.l #2,%d1
    sub.l %d3,%d1
    bmi 8f
    lsr.l #1,%d1
    lea row_len(%pc),%a1
    moveq #0,%d3
    move.b (%a1,%d2.w),%d3
    cmp.w %d3,%d1
    bcc 8f
    add.w %d2,%d2
    lea row_off(%pc),%a1
    move.w (%a1,%d2.w),%d3
    add.w %d1,%d3
    add.w %d3,%d3
    lea rows(%pc),%a1
    move.w (%a1,%d3.w),2(%a2)
    bne 7f
8:  move.w (%a2),%d0                | not in the tables: the plain normal -> big table
    cmp.w #NORMAL_FRAMES,%d0
    bcc 7f
    lsr.w #1,%d0
    lea frame_map(%pc),%a1
    move.w (%a1,%d0.w),2(%a2)
7:  movem.l (%sp)+,%d0-%d3/%a1-%a2
9:  rts

| ---- drawing: in place of `move.w 8(a0),d3 ; move.l (a3,d3.w),a5` (d3 is already clear)
draw:
    move.w 8(%a0),%d3
    move.l %d4,-(%sp)
    move.w %d3,%d4                  | Red (an object drawing player 2's copies, not a player's hero): noted
    and.w #0xF800,%d4
    cmp.w #0x800,%d4
    bne 11f
    move.w %d3,%d4
    and.w #0x7FF,%d4
    cmp.w #NORMAL_FRAMES,%d4
    bcc 11f
    cmpi.l #RED_CODE_LO,4(%a0)      | (the ending's objects only - e.g. the title screen's green player stays small)
    bcs 11f
    cmpi.l #RED_CODE_HI,4(%a0)
    bcc 11f
HERO_ONLY_A0    move.l %a0,RED_OBJ_RAM
    bra 12f
11: cmpa.l RED_OBJ_RAM,%a0             | (the noted object drawing something else: forgotten)
    bne 12f
    clr.l RED_OBJ_RAM
12: move.l (%sp)+,%d4
HERO_A0    bra 9f
1:  move.l %a1,-(%sp)
PAIR_A0    clr.b 5(%a1)                    | (1 = this draw uses a big frame: the +34 fix and the position nudges)
    clr.b 7(%a1)
    move.w %d3,-(%sp)               | the frame in +8 (player 2's hero draws player 2's copies, 0x800 further on)
    and.w #0x7FF,%d3                | as player 1's frame
    cmp.w #NORMAL_FRAMES,%d3        | only a normal-size frame is swapped (whatever the form: growing
    bcc 4f                          | back from the shrink zooms the normal frame while +98 is still shrunk)
    move.w (%sp),%d4
    move.l (%a3,%d4.w),%a5          | the normal frame's width and height in tiles
    move.b (%a5),4(%a1)
    move.b 1(%a5),6(%a1)
    cmp.w (%a1),%d4                 | still the frame the step picked a big one for?
    bne 3f
    move.w 2(%a1),%d4
    beq 3f
    move.w %d4,%d3
    bra 5f
3:  lsr.w #1,%d3                    | set some other way: the plain table, or as it is
    lea frame_map(%pc),%a5
    move.w (%a5,%d3.w),%d3
    beq 4f
5:  cmp.b #BURN_STATE,104(%a0)       | burning in lava: the charred frames 0x11C-0x128 drawn as their big copies
    bne 47f
    move.w (%sp),%d4
    and.w #0x7FF,%d4
    sub.w #0x11C,%d4
    bcs 47f
    cmp.w #0x10,%d4
    bcc 47f
    lsr.w #1,%d4
    lea burn_tab(%pc),%a5
    move.w (%a5,%d4.w),%d3
47: move.b #1,5(%a1)
    move.w (%sp)+,%d4
    and.w #0x800,%d4
    cmp.w #NEW_FRAMES,%d3           | (frames made here have no player 2 copies)
    bcc 8f
    add.w %d4,%d3                   | player 2: its copy of the big frame
    bra 8f
4:  move.w (%sp)+,%d3               | as it is
8:  tst.b 5(%a1)                    | drawn big: return through `restore` (the stack holds a1, the return
    beq 7f                          | to 0xA430, then the drawing loop's return address)
    cmpi.w #0xFFFF,38(%a0)          | being zoomed (the C-button shrink): zoom the big art further
    beq 6f
    movem.l %d0-%d2,-(%sp)
    move.w 38(%a0),12(%a1)          | (set back after the draw)
    bset #2,7(%a1)
    moveq #ZOOM_SHRINK,%d2          | shrinking (still the normal form) or growing back (+98 shrunk)
    tst.w 98(%a0)
    beq 1f
    moveq #ZOOM_GROW,%d2
1:  moveq #0,%d0
    move.b 38(%a0),%d0
    bsr zoom
    move.b %d0,38(%a0)
    moveq #0,%d0
    move.b 39(%a0),%d0
    bsr zoom
    move.b %d0,39(%a0)
    movem.l (%sp)+,%d0-%d2
6:
    cmpi.l #DRAW_LOOP_RETURN,8(%sp)
    bne 7f
    move.l #restore,8(%sp)
7:  move.l (%sp)+,%a1
9:  move.l (%a3,%d3.w),%a5
    rts

| d0 = a zoom byte (0xFF = full size) -> 0xFF - (0xFF - d0) * d2 / 16, at least 0x0F
zoom:
    not.b %d0
    mulu %d2,%d0
    lsr.l #4,%d0
    cmp.w #0xF0,%d0
    bls 1f
    move.w #0xF0,%d0
1:  not.b %d0
    rts

| ---- 0xA4FC, copied exactly (d4 = the drawn frame's width in tiles; returns d6, sets +34 and 664(a6)),
| then for the normal-size hero drawn with a big frame +34 is recomputed from the normal frame's width.
flip:
    move.b 33(%a0),%d6
    andi.b #12,%d6
    beq 20f
    subq.b #4,%d6
    beq 21f
    moveq #11,%d5                   | (as 0xA50A)
    move.w %d4,%d6
    lsl.w %d5,%d6
    addi.w #0x780,%d6
    move.w %d6,34(%a0)
    add.w 2(%a0),%d6
    move.w %d6,664(%a6)
    bra 22f
20: moveq #11,%d5                   | (as 0xA522)
    move.w %d4,%d6
    lsl.w %d5,%d6
    addi.w #0x780,%d6
    neg.w %d6
    move.w #0,34(%a0)
    move.w 2(%a0),%d5
    move.w %d5,664(%a6)
    add.w %d5,%d6
    rts                             | (+34 is 0 here whatever the width)
21: moveq #10,%d5                   | (as 0xA540)
    move.w %d4,%d6
    addq.w #1,%d6
    lsl.w %d5,%d6
    move.w %d6,34(%a0)
    add.w 2(%a0),%d6
    move.w %d6,664(%a6)
    move.w 2(%a0),%d6
22: move.l %a1,-(%sp)               | the hero drawn big: +34 from the normal frame's width
HERO_A0F    bra 29f
1:
PAIR_A0F    tst.b 5(%a1)
    beq 29f
    move.l %d7,-(%sp)
    moveq #0,%d7
    move.b 4(%a1),%d7
    btst #2,33(%a0)                 | (the case above: 4 -> (w+1)<<10, 8/12 -> (w<<11)+0x780)
    beq 23f
    btst #3,33(%a0)
    bne 23f
    addq.w #1,%d7
    lsl.w #8,%d7
    lsl.w #2,%d7
    bra 24f
23: lsl.w #8,%d7
    lsl.w #3,%d7
    addi.w #0x780,%d7
24: move.w %d7,8(%a1)                | (set back after the draw - the drawing itself uses the big value)
    bset #0,7(%a1)
    move.l (%sp)+,%d7
29: move.l (%sp)+,%a1
    rts

| ---- 0xA55A, copied exactly (d3 = the drawn frame's height in tiles - 1; the zoomed drawing's +36 and
| 666(a6)), then for the hero drawn with a big frame +36 is recomputed from the normal frame's height.
height:
    move.b 33(%a0),%d6
    andi.b #3,%d6
    beq 30f
    subq.b #1,%d6
    beq 31f
    moveq #11,%d5                   | (as 0xA568)
    move.w %d3,%d6
    lsl.w %d5,%d6
    addi.w #0x780,%d6
    move.w %d6,36(%a0)
    neg.w %d6
    add.w 0(%a0),%d6
    move.w %d6,666(%a6)
    bra 32f
30: move.w #0,36(%a0)               | (as 0xA582: +36 is 0 whatever the height)
    move.w 0(%a0),666(%a6)
    rts
31: moveq #10,%d5                   | (as 0xA590)
    move.w %d3,%d6
    addq.w #1,%d6
    lsl.w %d5,%d6
    move.w %d6,36(%a0)
    neg.w %d6
    add.w 0(%a0),%d6
    move.w %d6,666(%a6)
32: move.l %a1,-(%sp)
HERO_A0H    bra 39f
1:
PAIR_A0H    tst.b 5(%a1)
    beq 39f
    move.l %d7,-(%sp)
    moveq #0,%d7
    move.b 6(%a1),%d7
    btst #0,33(%a0)                 | (the case above: 1 -> (h+1)<<10, 2/3 -> (h<<11)+0x780)
    beq 33f
    btst #1,33(%a0)
    bne 33f
    addq.w #1,%d7
    lsl.w #8,%d7
    lsl.w #2,%d7
    bra 34f
33: lsl.w #8,%d7
    lsl.w #3,%d7
    addi.w #0x780,%d7
34: move.w %d7,10(%a1)
    bset #1,7(%a1)
    move.l (%sp)+,%d7
39: move.l (%sp)+,%a1
    rts

| ---- after the hero was drawn big: +34 / +36 get the normal frame's values, then back to the drawing loop
restore:
    movem.l %a0-%a1,-(%sp)
RESTORES    movem.l (%sp)+,%a0-%a1
    jmp DRAW_LOOP_RETURN

DATA
"""
    src = src.replace("HERO_ONLY_A0", "".join("    cmpa.l #0x%X,%%a0\n    beq 12f\n" % obj for obj in HERO_OBJECTS))
    src = src.replace("RED_OBJ_RAM", "0x%X" % RED_OBJ)
    src = src.replace("RED_CODE_LO", "0x%X" % RED_CODE[0]).replace("RED_CODE_HI", "0x%X" % RED_CODE[1])
    src = (src.replace("HERO_A0F", hero_check("a0")).replace("PAIR_A0F", pair("a0", "a1"))
           .replace("HERO_A0H", hero_check("a0")).replace("PAIR_A0H", pair("a0", "a1"))
           .replace("HERO_A5", hero_check("a5")).replace("HERO_A0", hero_check("a0"))
           .replace("PAIR_A5", pair("a5", "a2")).replace("PAIR_A0", pair("a0", "a1"))
           .replace("NORMAL_ANIMS", "0x%X" % NORMAL_ANIMS).replace("NORMAL_FRAMES", "0x%X" % NORMAL_FRAMES)
           .replace("ANIM_TABLE", "0x%X" % ANIM_TABLE).replace("NEW_FRAMES", "0x3F00").replace("BURN_STATE", "33")
           .replace("DRAW_LOOP_RETURN", "0x%X" % DRAW_LOOP_RETURN)
           .replace("ZOOM_SHRINK", str(ZOOM_SHRINK)).replace("ZOOM_GROW", str(ZOOM_GROW)).replace("RESTORES", restores).replace("DATA", data))
    base = rom.place_code(src, why="hero big art: pick and draw the big frame for the normal hero's frame")
    for site in STEP_SITES:
        rom.write(site, bytes.fromhex("4EB9") + base.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex("3B4000080241 0003".replace(" ", "")), why="animation step: note the big frame")
    rom.write(DRAW_FRAME, bytes.fromhex("4EB9") + (base + 4).to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("36280008 2A733000".replace(" ", "")), why="drawing: draw the big frame")
    rom.write(FLIP_OFFSET, bytes.fromhex("4EF9") + (base + 8).to_bytes(4, "big"),
              expect=bytes.fromhex("1C2800210206"), why="flip offset: +34 from the normal frame for the hero")
    rom.write(HEIGHT_OFFSET, bytes.fromhex("4EF9") + (base + 12).to_bytes(4, "big"),
              expect=bytes.fromhex("1C2800210206"), why="height offset: +36 from the normal frame for the hero")

    _side_table[0] = rom.place_code(
        "    .word %s\n" % ",".join(str(SIDE_PX.get(n, 0) * 128) for n in range(STATES)),
        why="hero big art: how far sideways to draw it, per hero state")
    _up_table[0] = rom.place_code(
        "    .word %s\n" % ",".join(str(UP_PX.get(n, HERO_UP_PX) * 128) for n in range(STATES)),
        why="hero big art: how far up to draw it, per hero state")
    hook(rom, DRAW_X_ZOOMED, "044540003C3C0100",
         "    sub.w #0x4000,%d5\n" + hero_only("a0", x_shift("d5", HERO_LEFT_PX_FACING_LEFT, True)) +
         "    move.w #256,%d6\n    rts\n",
         "sprite X (facing left, zoomed)")
    hook(rom, DRAW_X_PLAIN, "044640003486",
         "    sub.w #0x4000,%d6\n" + hero_only("a0", x_shift("d6")) + "    move.w %d6,(%a2)\n    rts\n",
         "sprite X (usual path)")
    hook(rom, DRAW_Y_ZOOMED, "0445B7FF7C01",
         "    sub.w #-18433,%d5\n" + hero_only("a0", y_shift("d5")) + carried_shift("d5", "") + "    moveq #1,%d6\n    rts\n",
         "sprite Y (zoomed path)")
    hook(rom, DRAW_Y_PLAIN, "0447B7FFDE433487",
         "    sub.w #-18433,%d7\n    add.w %d3,%d7\n" + hero_only("a0", y_shift("d7")) + carried_shift("d7", "") + "    move.w %d7,(%a2)\n    rts\n",
         "sprite Y (usual path)")
    hook(rom, PIECES_BASE, "0447B7FF48473E2E029804474000",
         "    sub.w #-18433,%d7\n" + hero_only("a0", y_shift("d7"), "y") + carried_shift("d7", "y") +
         "    swap %d7\n    move.w 664(%fp),%d7\n    sub.w #0x4000,%d7\n" + hero_only("a0", x_shift("d7"), "x") +
         "    rts\n",
         "sprite pieces' base position")

    # The same three hooks for the hero facing left.
    hook(rom, LEFT_X, "044540003485",
         "    sub.w #0x4000,%d5\n" + hero_only("a0", x_shift("d5", HERO_LEFT_PX_FACING_LEFT, True), "lx") + "    move.w %d5,(%a2)\n    rts\n",
         "sprite X (facing left)")
    hook(rom, LEFT_Y, "0447B7FFDE433487",
         "    sub.w #-18433,%d7\n    add.w %d3,%d7\n" + hero_only("a0", y_shift("d7"), "ly") + carried_shift("d7", "ly") + "    move.w %d7,(%a2)\n    rts\n",
         "sprite Y (facing left)")
    hook(rom, LEFT_PIECES, "0447B7FF48473E28000204474000",
         "    sub.w #-18433,%d7\n" + hero_only("a0", y_shift("d7"), "py") + carried_shift("d7", "py") +
         "    swap %d7\n    move.w 2(%a0),%d7\n    sub.w #0x4000,%d7\n" + hero_only("a0", x_shift("d7", HERO_LEFT_PX_FACING_LEFT, True), "px") +
         "    rts\n",
         "sprite pieces' base position (facing left)")
    hook(rom, RIGHT_X_ZOOMED, "044640003486",
         "    sub.w #0x4000,%d6\n" + hero_only("a0", x_shift("d6"), "rzx") + "    move.w %d6,(%a2)\n    rts\n",
         "sprite X (facing right, zoomed)")
    hook(rom, RIGHT_Y_ZOOMED, "0445B7FF7C01",
         "    sub.w #-18433,%d5\n" + hero_only("a0", y_shift("d5"), "rzy") + carried_shift("d5", "rzy") + "    moveq #1,%d6\n    rts\n",
         "sprite Y (facing right, zoomed)")
