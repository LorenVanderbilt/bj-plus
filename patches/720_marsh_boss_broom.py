NAME = "marsh-boss-broom"
DESCRIPTION = "Empire Marsh boss's death: the broom cracks, breaks in a puff, and its pieces hop apart and tumble down gently"

# When the witch is beaten she flies off and her broom (object 0x2B88C) hangs in the air, plays its crack frames
# (0x173C, 0x1740, 8 frames each), and splits into the handle (a new object with 8 turning frames) and the bristles
# (the broom itself, continuing at BRISTLES). The crack countdown looped back within the same frame (CRACK_LOOP), so
# both crack frames went by unseen. It now branches to the rts and counts once per frame.
#
# At crack step PUFF_AT (checked at STEP_CHECK, or at the split) a puff of dust comes up where the broom breaks. It's
# its own object, playing the final boss's dust frames (DUST, PUFF_STEP frames each) while drifting up, then
# disappearing. The dust colours (DUST_COLOURS, from the final hall's palette 0x4F) are turned a warm grey (GREY) and
# written into PUFF_PALETTE, which nothing in the boss room uses, while the puff is out.
#
# The handle now turns one frame every TURN frames instead of every frame. When the pieces start to fall (FALLS),
# they hop up first (HOP), drift sideways at half speed (X_SPEED, was 0x50) and fall a little slower (GRAVITY, was
# -0x10). Speeds are in the fields 0xA258 moves objects by: +0x0C y speed, +0x0E x speed, +0x10 y gravity.
CRACK_LOOP = 0x2B8B2           # bne 0x2B8A8 (loops in the same frame), now bne 0x2B8D6 (rts)
SPLIT = 0x2B916                # move.l #BRISTLES,4(a5), then move.l a1,0x4010(a5) with a1 = the handle
BRISTLES = 0x2B924
NEW_OBJECT = 0xFFEC            # returns a1; ne if no slot is free
MOVE = 0xA258
DUST = [0x1A00, 0x1A04, 0x1A08, 0x1A0C, 0x1A10, 0x1A14, 0x1A18]   # 32x32 each
DUST_COLOURS = [0xFFFF, 0xEFFA, 0xFFE5, 0xEFC4, 0x5FA1, 0x8F80, 0x8E60, 0x8D40, 0xAC10, 0xCA00, 0x8900, 0xC700,
                0x7500, 0x8400, 0xC200]   # colours 1-15
GREY = (1.0, 0.94, 0.85)       # r, g, b tint applied to the dust's brightness
PUFF_PALETTE = 0x7B
PUFF_UP, PUFF_X = -26, 10        # px up and right of the broom
PUFF_STEP, PUFF_RISE = 3, 0x30
PUFF_LIFE = PUFF_STEP * len(DUST)
PUFF_AT = 2                    # broom step: 1 and 2 are the crack frames, 3 is the split
STEP_CHECK = 0x2B8CE           # cmpi.w #3,0x4000(a5) ; beq <split>, at each step
PUFF_PRIORITY = 0xC0           # +0x28, lower draws in front: pieces 0xD0 / 0xD8, Blue 0x80
TURN_AT = 0x2B980              # move.w #1,0x4002(a5): the handle's frame delay
TURN = 3
FALLS = [(0x2B93C, "a0", -1), (0x2B948, "a5", 1)]   # handle, bristles: move.w #-0x10,0x10(an) ;
                                                     # move.w #+-0x50,0x0E(an), and the sign of x
HOP = 0x100                    # about 16 px up
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

split:                                  | the broom becomes the bristles
    move.l #0x%(bristles)X,4(%%a5)      | replaced by the jsr
%(at_split)s    rts

step:                                   | each crack step: 0x4000(a5) = step, 3 = split
    cmpi.w #%(at)d,0x4000(%%a5)
    bne 1f
%(at_step)s1:  cmpi.w #3,0x4000(%%a5)                | replaced by the jsr; its beq follows
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

puff:                                   | dust frames, PUFF_STEP each, drifting up, then removed
    tst.b 0x29(%%a5)
    bne 1f
    st 0x29(%%a5)
    move.w #%(life)d,0x50(%%a5)
    move.w #%(rise)d,0x0C(%%a5)
    clr.w 0x0E(%%a5)
    clr.w 0x10(%%a5)
    clr.w 0x12(%%a5)
    move.b #0x%(palette)X,0x20(%%a5)
    move.b #0x%(priority)X,0x28(%%a5)      | in front of the broom's pieces
1:  lea greys(%%pc),%%a0                | its colours
    lea 0x%(palette_ram)X,%%a1
    moveq #14,%%d0
0:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,0b
    subq.w #1,0x50(%%a5)
    bne 2f
    clr.b 0x28(%%a5)                    | done: remove it
    rts
2:  moveq #0,%%d0                       | frame = (PUFF_LIFE - frames left) / PUFF_STEP
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
