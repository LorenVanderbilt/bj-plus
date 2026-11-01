NAME = "goal-bend"
DESCRIPTION = "Goal stalk: when touched it arcs from a little above the ground, not swung stiffly from its foot"

# The goal's stalk (see sta/aes/goal_bell.sta) is a stack of segment objects. 0x5E4F2 places each one every frame
# from the stalk's base (its parent, +0x4E) at its radius (+0x38, a byte, 8 per 16 px segment) and angle (+0x3A).
# When touched, each segment runs 0x52A0C, which sets its angle to sin(phase) x amplitude, larger higher up and
# decaying. Every segment was placed from the base, so the whole stalk swung stiffly from its foot.
#
# Now segments within BEND of the base stay upright, and each one above is placed one segment's length on from the
# segment below it (the object before it, since segments are made in order). Its angle is scaled by
# (radius - BEND) / CURVE, so the angles grow up the stalk and it arcs from the bend. The bells hang from segments,
# so they follow. Anything else running 0x52A0C is placed as before.
#
# While the stalk swings, the bells shed sparkles, the water sparkle Blue throws off (0x45C40: animation 0x118,
# frames 0x2D9C-0x2DB4). Each bell's routine copies its segment's position first (BELL_COPIES). There, while the
# segment swings (0x52A0C, amplitude +0x7A), every SPARKLE_EVERY frames (staggered by bell) a new object is made
# SPARKLE_DOWN px below the bell's middle, at its mouth. It plays SPARKLE_FRAMES, SPARKLE_HOLD frames each, falling
# SPARKLE_FALL / 128 px a frame, and is then freed.
SWING_PLACE = 0x52A48        # jsr 0x5E4F2 with d0, d1 = the parent's position
PLACE = 0x5E4F2
BELL_COPIES = [0x52B58, 0x52B86, 0x52BB4, 0x52BE2, 0x52C10, 0x52C3E]   # move.l 0(a0),0(a5), with a0 = its segment
SWINGING = 0x52A0C
NEW_OBJECT = 0xFFEC          # returns a1; nonzero if none is free
FREE_OBJECT = 0x43F7C        # jmp here to free the object in a5
SPARKLE_FRAMES = [0x2D9C, 0x2DA0, 0x2DA4, 0x2DA8, 0x2DAC, 0x2DB0, 0x2DB4]   # animation 0x118: dots, then small,
                                                                          # medium and big crosses
SPARKLE_HOLD = 3             # game frames each
FRAME = 0x100206
SPARKLE_EVERY = 8            # frames between one bell's sparkles; a power of 2
SPARKLE_DOWN = 16            # px below the bell's middle, at its mouth
SPARKLE_FALL = 96            # 1/128 px a frame
# The sparkles shimmer. They're drawn in their own palette, SPARKLE_PAL, through the object's palette override
# (+0x20). It was empty in every level checked (sta/aes boss1, lava_fall, ferris_sunken, marsh1_geyser, mech3_guard,
# boss_space, goal_touch and others). Its colours 1-4 step through hues every HUE_FRAMES frames, written once a frame
# (SHIMMER_FRAME records which).
SPARKLE_PAL = 0x4B
PALETTES = 0x400000
HUE_STEPS, HUE_FRAMES = 16, 3
HUE_SATURATION = 0.45        # pastel, for an opal shimmer rather than a rainbow
SHIMMER_FRAME = 0x10E826     # word


def neo_colour(r, g, b):
    """A Neo Geo colour word from 0-1 components (5 bits each: the low bits in 14-12, the rest in 11-0)."""
    r, g, b = (min(31, int(round(c * 31))) for c in (r, g, b))
    return (r & 1) << 14 | (g & 1) << 13 | (b & 1) << 12 | (r >> 1) << 8 | (g >> 1) << 4 | (b >> 1)


GLOW = [(1.0, 1.0), (1.15, 0.92), (1.3, 0.84), (1.45, 0.76)]   # (saturation x, brightness) for colours 1-4. The big
                             # crosses' soft edges use 2-4, which the original has as fainter tints of white


def hues():
    """Colours 1-4 for each of HUE_STEPS hues, bright to soft."""
    import colorsys
    return [neo_colour(*colorsys.hsv_to_rgb(i / HUE_STEPS, min(1.0, HUE_SATURATION * sx), v))
            for i in range(HUE_STEPS) for sx, v in GLOW]
BEND = 0                     # where the arc starts, in radius units (2 px, 8 a segment); 0 is the foot
CURVE = 48                   # radius units over which a segment's angle reaches the swing's, chosen so the top
                             # sways about as far as before


def apply(rom):
    code = rom.place_code(r"""
    move.b 0x38(%%a5),%%d2
    ext.w %%d2
    cmp.w #%(bend)d,%%d2
    bgt 1f
    clr.w 0x3A(%%a5)                    | within the bend: upright
    jmp 0x%(place)X
1:  lea -0x80(%%a5),%%a0                | the segment below is the object before this one, if any
    move.l 4(%%a0),%%d3
    cmp.l 4(%%a5),%%d3
    bne 2f
    move.b 0x4E(%%a0),%%d3
    cmp.b 0x4E(%%a5),%%d3
    bne 2f
    move.b 0x38(%%a0),%%d3              | one segment's length: this radius minus that one's
    sub.b %%d3,%%d2
    ble 2f
    move.b 0x3A(%%a5),%%d3              | scale the angle by (radius - BEND) / CURVE for this frame;
    ext.w %%d3                          | 0x52A0C sets it again from the swing next frame
    move.b 0x38(%%a5),%%d0
    ext.w %%d0
    sub.w #%(bend)d,%%d0
    muls %%d0,%%d3
    divs #%(curve)d,%%d3
    move.b %%d3,0x3A(%%a5)
    move.w 0(%%a0),%%d0                 | from the segment below's position
    move.w 2(%%a0),%%d1
    move.b 0x38(%%a5),-(%%sp)
    move.b %%d2,0x38(%%a5)
    jsr 0x%(place)X
    move.b (%%sp)+,0x38(%%a5)
    rts
2:  jmp 0x%(place)X                     | not a stalk: as before
""" % {"bend": BEND, "place": PLACE, "curve": CURVE}, why="goal stalk: an arc from just above its foot")
    bell = rom.place_code(r"""
    cmpi.l #0x%(swinging)X,4(%%a0)      | is its segment swinging?
    bne 9f
    tst.b 0x7A(%%a0)
    beq 9f
    move.w 0x%(frame)X,%%d0             | every SPARKLE_EVERY frames, staggered by the bell's slot
    move.w %%a5,%%d1
    lsr.w #7,%%d1
    add.w %%d1,%%d0
    and.w #%(every)d-1,%%d0
    bne 9f
    move.l %%a0,-(%%sp)
    jsr 0x%(new)X
    bne 8f
    move.l 0(%%a5),0(%%a1)              | a sparkle at its mouth, below its last position
    subi.w #%(down)d,0(%%a1)
    move.b #0x40,0x28(%%a1)
    move.b #0x%(pal)X,0x20(%%a1)         | its own palette, for the shimmer
    clr.b 0x7E(%%a1)
    move.l #sparkle_start,4(%%a1)
8:  move.l (%%sp)+,%%a0
9:  move.l 0(%%a0),0(%%a5)              | as before: its segment's position
    rts

sparkle_start:                          | SPARKLE_FRAMES, SPARKLE_HOLD frames each, falling; then freed
    clr.b 0x7C(%%a5)
    move.l #sparkle_fall,4(%%a5)
sparkle_fall:
    move.w 0x%(frame)X,%%d0             | the shimmer: once a frame, the palette's colours from the hues
    cmp.w 0x%(shimmer)X,%%d0
    beq 2f
    move.w %%d0,0x%(shimmer)X
    ext.l %%d0
    and.l #0xFFFF,%%d0
    divu #%(hue_frames)d,%%d0
    and.w #%(steps)d-1,%%d0
    lsl.w #3,%%d0                       | 4 colours a step
    lea hue_table(%%pc),%%a0
    move.l (%%a0,%%d0.w),0x%(colour)X
    move.l 4(%%a0,%%d0.w),0x%(colour)X+4
2:  subi.w #%(fall)d,0(%%a5)
    moveq #0,%%d0
    move.b 0x7C(%%a5),%%d0
    addq.b #1,0x7C(%%a5)
    divu #%(hold)d,%%d0
    cmp.w #%(count)d,%%d0
    bcc 1f
    add.w %%d0,%%d0
    lea frames(%%pc),%%a0
    move.w (%%a0,%%d0.w),8(%%a5)
    rts
1:  jmp 0x%(free)X
frames:
    .word %(frames)s
hue_table:
    .word %(hues)s
""" % {"swinging": SWINGING, "frame": FRAME, "every": SPARKLE_EVERY, "new": NEW_OBJECT, "down": SPARKLE_DOWN * 128,
       "hold": SPARKLE_HOLD, "count": len(SPARKLE_FRAMES), "free": FREE_OBJECT,
       "frames": ",".join("0x%X" % f for f in SPARKLE_FRAMES), "fall": SPARKLE_FALL,
       "pal": SPARKLE_PAL, "shimmer": SHIMMER_FRAME, "hue_frames": HUE_FRAMES, "steps": HUE_STEPS,
       "colour": PALETTES + SPARKLE_PAL * 32 + 2, "hues": ",".join("0x%04X" % c for c in hues())},
        why="goal bells: sparkles while the stalk swings")
    for at in BELL_COPIES:
        rom.write(at, bytes.fromhex("4EB9") + bell.to_bytes(4, "big"), expect=bytes.fromhex("2B6800000000"),
                  why="goal bell: sheds sparkles as it swings")
    rom.write(SWING_PLACE, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + PLACE.to_bytes(4, "big"), why="goal stalk: placed from its bend")
