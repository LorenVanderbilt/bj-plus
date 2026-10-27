NAME = "marsh-boss-broom"
DESCRIPTION = "Empire Marsh boss's death: the broom cracks, breaks in a puff, and its pieces hop apart and tumble down gently"

# Beaten, the witch flies off and her broom (object 0x2B88C) hangs, then steps through its crack frames (0x173C,
# 0x1740: 8 frames each) and splits: the handle (a new object: 8 turning frames) and the bristles (the broom, as
# BRISTLES). But its step's countdown looped back inside the same frame (CRACK_LOOP: bne to its own start) - the crack
# frames passed in one frame, unseen; now it waits a frame at a time (bne to the rts).
# As it cracks (PUFF_AT: its step - STEP_CHECK - or the split, SPLIT: the broom becomes BRISTLES) a puff of dust comes up
# where it breaks: an object of its own
# billowing through the final boss's dust frames (DUST, PUFF_STEP frames each - PUFF_LIFE in all), drifting up
# (PUFF_RISE), then gone; its colours DUST_COLOURS (the final hall's 0x4F) made a warm grey (GREY) and written into
# PUFF_PALETTE (nothing in the marsh boss's room uses it) while it's out - drawn with it (+0x20, the palette override).
# The pieces: the handle turns a frame every TURN (was every frame - a whole turn in 8). As the bristles start to
# fall (FALLS: each piece's speeds and gravity set - +0x0C y speed, +0x0E x speed, +0x10 y gravity, as the mover
# 0xA258 has them), they now hop up first (HOP; was none), go half as fast sideways (X_SPEED, was 0x50) and fall a
# little slower (GRAVITY, was -0x10).
CRACK_LOOP = 0x2B8B2           # bne 0x2B8A8 (its countdown, again in the same frame) -> bne 0x2B8D6 (rts)
SPLIT = 0x2B916                # move.l #BRISTLES,4(a5) - then move.l a1,0x4010(a5) (a1: the handle)
BRISTLES = 0x2B924
NEW_OBJECT = 0xFFEC            # -> a1 (ne: none free)
MOVE = 0xA258
DUST = [0x1A00, 0x1A04, 0x1A08, 0x1A0C, 0x1A10, 0x1A14, 0x1A18]   # (32 x 32)
DUST_COLOURS = [0xFFFF, 0xEFFA, 0xFFE5, 0xEFC4, 0x5FA1, 0x8F80, 0x8E60, 0x8D40, 0xAC10, 0xCA00, 0x8900, 0xC700,
                0x7500, 0x8400, 0xC200]   # (colours 1-15)
GREY = (1.0, 0.94, 0.85)       # (the dust's brightness, tinted: r, g, b)
PUFF_PALETTE = 0x7B
PUFF_UP, PUFF_X = -26, 10        # px from the broom's place (up, right; 128 a px)
PUFF_STEP, PUFF_RISE = 3, 0x30
PUFF_LIFE = PUFF_STEP * len(DUST)
PUFF_AT = 2                    # (the broom's step it comes at: 1, 2 - its crack frames, 8 frames each - 3 the split)
STEP_CHECK = 0x2B8CE           # cmpi.w #3,0x4000(a5) ; beq <the split> - each step
PUFF_PRIORITY = 0xC0           # (+0x28: lower draws in front - the pieces 0xD0 / 0xD8, Blue 0x80; the template's 0xFD)
TURN_AT = 0x2B980              # move.w #1,0x4002(a5) - the handle's frames: one every TURN
TURN = 3
FALLS = [(0x2B93C, "a0", -1), (0x2B948, "a5", 1)]   # (move.w #-0x10,0x10(an) ; move.w #+-0x50,0x0E(an): the handle,
                                                     # the bristles; x's sign)
HOP = 0x100                    # (~16 px up)
X_SPEED = 0x28
GRAVITY = -0x0C


def grey(word):
    """A colour word as the same brightness in GREY."""
    from png_tiles import neo_to_rgb, rgb_to_neo
    r, g, b = neo_to_rgb(word)
    v = 0.3 * r + 0.59 * g + 0.11 * b
    return rgb_to_neo(tuple(min(255, int(v * t + 0.5)) for t in GREY))


def apply(rom):
    rom.write(CRACK_LOOP, bytes.fromhex("6622"), expect=bytes.fromhex("66F4"),
              why="marsh boss's broom: its crack frames shown (a frame at a time)")
    split_bytes = bytes.fromhex("2B7C") + BRISTLES.to_bytes(4, "big") + bytes.fromhex("0004")
    code = rom.place_code("""
    bra.w split
    bra.w step

split:                                  | (the broom becomes the bristles)
    move.l #0x%(bristles)X,4(%%a5)      | (what the jsr replaced)
%(at_split)s    rts

step:                                   | (each crack step: 0x4000(a5) the step, 3 the split)
    cmpi.w #%(at)d,0x4000(%%a5)
    bne 1f
%(at_step)s1:  cmpi.w #3,0x4000(%%a5)                | (what the jsr replaced: its beq follows)
    rts

spawn:                                  | a puff where it breaks
    movem.l %%d0-%%d2/%%a0-%%a1,-(%%sp)
    jsr 0x%(new)X
    bne 9f
    move.l #puff,4(%%a1)
    move.l (%%a5),(%%a1)
    addi.w #%(up)d,(%%a1)
    addi.w #%(x)d,2(%%a1)
    clr.b 0x29(%%a1)
9:  movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    rts

puff:                                   | (the puff: the dust's frames, PUFF_STEP each, drifting up, then gone)
    tst.b 0x29(%%a5)
    bne 1f
    st 0x29(%%a5)
    move.w #%(life)d,0x50(%%a5)
    move.w #%(rise)d,0x0C(%%a5)
    clr.w 0x0E(%%a5)
    clr.w 0x10(%%a5)
    clr.w 0x12(%%a5)
    move.b #0x%(palette)X,0x20(%%a5)
    move.b #0x%(priority)X,0x28(%%a5)      | (in front of the broom's pieces)
1:  lea greys(%%pc),%%a0                | its colours
    lea 0x%(palette_ram)X,%%a1
    moveq #14,%%d0
0:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,0b
    subq.w #1,0x50(%%a5)
    bne 2f
    clr.b 0x28(%%a5)                    | (done: gone)
    rts
2:  moveq #0,%%d0                       | its frame: (PUFF_LIFE - left) / PUFF_STEP
    move.w #%(life)d,%%d0
    sub.w 0x50(%%a5),%%d0
    divu #%(step)d,%%d0
    add.w %%d0,%%d0
    lea frames(%%pc),%%a0
    move.w (%%a0,%%d0.w),8(%%a5)
    jmp 0x%(move)X
frames:
    .word %(frames)s
greys:
    .word %(greys)s
""" % {"bristles": BRISTLES, "new": NEW_OBJECT, "at": PUFF_AT,
       "at_split": "    bsr spawn\n" if PUFF_AT >= 3 else "", "at_step": "    bsr spawn\n" if PUFF_AT < 3 else "", "up": PUFF_UP * 128, "x": PUFF_X * 128, "life": PUFF_LIFE,
       "rise": PUFF_RISE, "palette": PUFF_PALETTE, "priority": PUFF_PRIORITY, "palette_ram": 0x400000 + PUFF_PALETTE * 32 + 2, "step": PUFF_STEP,
       "move": MOVE, "frames": ",".join("0x%04X" % f for f in DUST + [DUST[-1]]),
       "greys": ",".join("0x%04X" % grey(w) for w in DUST_COLOURS)},
        why="marsh boss's broom: a puff as it breaks")
    rom.write(SPLIT, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"), expect=split_bytes,
              why="marsh boss's broom: its split, with a puff")
    rom.write(STEP_CHECK, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"), expect=bytes.fromhex("0C6D00034000"),
              why="marsh boss's broom: its crack steps (the puff at PUFF_AT)")
    rom.write(TURN_AT, TURN.to_bytes(2, "big"), expect=(1).to_bytes(2, "big"),
              why="marsh boss's broom: the handle turns slower")
    for at, an, sign in FALLS:
        was = bytes(rom.data[at:at + 12])
        op = "317C" if an == "a0" else "3B7C"
        assert was[:6] == bytes.fromhex(op + "FFF00010") and was[6:8] == bytes.fromhex(op) and was[10:] == b"\x00\x0E", was.hex()
        fall = rom.place_code("""
    move.w #%(gravity)d,0x10(%%%(an)s)
    move.w #%(hop)d,0x0C(%%%(an)s)
    move.w #%(x)d,0x0E(%%%(an)s)
    rts
""" % {"gravity": GRAVITY, "hop": HOP, "x": sign * X_SPEED, "an": an}, why="marsh boss's broom: a piece's hop and fall")
        rom.write(at, bytes.fromhex("4EB9") + fall.to_bytes(4, "big") + bytes.fromhex("4E714E714E71"), expect=was,
                  why="marsh boss's broom: a piece hops, then falls gently")
