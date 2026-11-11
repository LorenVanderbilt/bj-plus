import os
import re
import subprocess
import tempfile

import hackbuild

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
#     the big form has no such art (its 0x2D is the standing pose), so its frames are drawn as 1.5x copies of
#     the small ones (FIDGET_ANIM; they stood and breathed before - BREATHE);
#   0x2B (frames 0x184-0x18C), playing the ocarina (standing still with one): the big form has no such art,
#     so its frames are drawn as 1.5x copies of the small ones (OCARINA_FRAMES).
#   0x18, swimming: the big version's fourth frame (0x33C) is a walking pose, so the swim cycle flashed upright
#     every fourth frame; like the normal cycle (0x6C 0x70 0x74 0x70) it repeats its second pose instead.
#   0x2C (frames 0x178-0x180), swimming with the flippers (sta/aes/swim_flippers.sta): the big form's 0xAC
#     (0x3C8 / 0x3CC / 0x3D0) switches to the flippers' palette (0x5F) at the top of the third column with an entry
#     (1, 0x40, 0x5F, 0x00) meant as a blank cell - but the game draws its tile, 0x3A00, there: a stray chunk of
#     flipper above Blue. Each such entry is now a blank (0) followed by the switch on the next tile, the same
#     bytes reordered (SWIM_FIXES, player 2's copies too). The third frame's lower tiles are the wrong ones in the
#     original (a jumble of boxes), so the third swim frame uses the first's (SWIM_BIG).
ROW_OVERRIDES = {0x2D: "none", 0x2B: "none", 0x2C: "none", 0x18: [0x330, 0x334, 0x338, 0x334]}
BREATHE = (0x364, 0x368)
# Standing still (animation 0), the small art's antennas are spread (one leaning out); the big standing pair
# 0x364 / 0x368 has them straight up side by side. They're drawn with spread_antennas copies (new frames: the walk,
# whose big frames 0x30C-0x314 lean and close them, is untouched).
STANDING_ANIM, ANTENNA_FROM = 0, 0x314
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
COPY_START, COPY_END = 0xA430, 0xA7F4   # the drawing routine after DRAW_FRAME, to its last rts (copied: see apply)
FLIP_OFFSET = 0xA4FC              # computes object+34 from the drawn frame's width: move.b 33(a0),d6 ; andi.b #12,d6
HEIGHT_OFFSET = 0xA55A            # and object+36 from its height (zoomed drawing): move.b 33(a0),d6 ; andi.b #3,d6
HERO_OBJECTS = [0x104000, 0x104080]   # the objects for player 1 and player 2
# Red (the ending's rival: his duel, his scenes) is another object drawing player 2's copies of the hero frames
# (0x800 further on). The drawing hook notes such an object in RED_OBJ (forgotten once it draws something else)
# and treats it as a third hero, with its own pair RAM - so he is drawn with the big art too.
RED_PAIR = 0x10EA40
RED_OBJ = 0x10EA50
BIG_NOW = 0x10EA58   # a byte (spare RAM): the object being drawn is drawn big (or carried by a hero): the drawing hooks
                     # run for every object - without it they only do what they replaced (they slowed every draw
                     # down enough that the sprites' update ran into the top of the picture: torn sprites)
RED_CODE = (0x23000, 0x25400)   # ... running the ending's code (its scenes and the duel: 0x234xx-0x2530x)
RED_DUEL_CODE = (0x28400, 0x28680)
BOXES = 0x64772                   # hit boxes: a pointer per frame number (as the frame table)
RED_BOX_SIDE_PX, RED_BOX_UP_PX = 3, 8   # Red's hit box in the duels: this much wider each side, and taller
BOX_LOOKUP = 0xB6A0               # the overlap test's other object's box: move.w 8(a0),d5 ; movea.l (a1,d5.w),a2
                                  # (... or the torch duel's: Lower Earth Empire's house, Red is 0x284BE)
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
# ... stand-ins until redrawn. Redrawn, the throws are four drawings (THROW_ART: the frames differ only at the feet),
# each used once its ART (below) is there: the wind-up, the release, lying down and its release. And with the
# in-between's ART there too (THROW_MID: a frame number no animation uses), the four throws (THROW_ANIMS: wind-up,
# then the release three steps) get it as their second step - wind-up, in-between, release, release (no longer).
THROW_ART = {0xB0: 0xB0, 0xB8: 0xB0, 0xC0: 0xB0, 0xC8: 0xB0, 0x8C: 0xB0,
             0xB4: 0xB4, 0xBC: 0xB4, 0xC4: 0xB4, 0xCC: 0xB4, 0x90: 0xB4,
             0x94: 0x94, 0x98: 0x94, 0x9C: 0x9C}
THROW_MID = 0xAC
THROW_FOLLOW = 0x9C            # its ART is the follow-through, the last step of all four throws after the release.
                               # 0x9C was the lying-down throw's release, never seen in play. 0x94's ART is left
                               # out, since 0x94 / 0x98 draw the big swim poses (FRAME_SUBSTITUTES)
THROW_ANIMS = [0x23, 0x24, 0x25, 0x26]
ART_END, FRAMES_END = 0xB8C66, 0x3CB0   # where this patch's code and art always end (see the end of apply)
HERO_UP_PX = 15
OCARINA_FRAMES = [0x184, 0x188, 0x18C]
SWIM_BIG = {0x178: 0x3C8, 0x17C: 0x3CC, 0x180: 0x3C8}   # small flipper swim frame -> the big frame it gets
SWIM_FIXES = [0x3C8, 0x3CC, 0xBC8, 0xBCC]                # (player 1's, player 2's)
FIDGET_ANIM = 0x2D
P2_FRAMES = 0x800                 # player 2's copies of the hero frames (the same art in player 2's palette)
P2_COPIES = {}                    # frames made here -> their player 2 copy (when the palette differs)
# Burning in lava (hero state 33) he flails in charred art: animation 0x31, frames 0x11C-0x128 in palette 0x5C,
# which the lava stage makes charred (elsewhere 0x31 is the landing from some jumps and keeps the big art). The big
# form has no charred version: in state 33 those frames are drawn as copies scaled up 1.5x from the small ones (new
# frames; player 2 draws them too - no copies 0x800 further on, which aren't free).
BURN_ANIMS = [0x31]
# Those 1.5x copies (idle fidget, ocarina, burning) can be redrawn: ART (by the small frame's number) if there is used
# instead - the frame's main block (its tiles across x down, 1.5x the small one's) with MARGIN pixels round it for
# what sticks out, in its palette's colours (PALETTE_COLOURS: as in play; tools/export_hero_frames.py writes the
# 1.5x copies as a start). Transparent = clear.
ART = "art/hero_big/%03X.png"
MARGIN = 16
PALETTE_COLOURS = {
    0x10: "4071 8222 FF96 FE74 7C52 B08F F04F 201E FA00 DB51 6830 CFB0 CF60 0E00 1B06 FFFF",   # player 1
    0x5C: "3060 0222 9C82 9B71 9A60 8950 9840 E620 8900 D520 3400 2C80 DD10 7AAA 7CCC FFFF",   # (charred, in lava)
}
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
# The lottery's ropes (after a boss): Blue jumps up and hangs on one (state 20, as on a vine), at whatever x he
# caught it - the game doesn't line him up, and the small art's hand is near its middle; the big art's hand is
# further out, so he could hang a hand's width from the cord. While the ropes are there their routine (ROPE_IDLE,
# every frame, each rope not pulled) sets ROPE_HELD, cleared whenever a hero is drawn not hanging; a hero hanging
# meanwhile is drawn so his hand is on the nearest rope (ROPE_CODES: idle, being pulled, pulled) within ROPE_NEAR_PX
# (with the nudges above his hand is ROPE_HAND_PX right of the rope's x: measured from
# sta/aes/lotto_ocarina_afford.sta; facing left ROPE_HAND_PX_FACING_LEFT, measured from the user's rope_float clip,
# 2026-11-11 - his hand was ~4px off the cord). One routine finds the rope (rope_routine), called from each hook; the
# rope being pulled comes first (the game can give him a rope further than another), else the nearest.
ROPE_IDLE = 0x299EC          # tst.b 0x78CB(a6) ; bne.w 0x29A44
ROPE_CODES = [0x299EC, 0x29A46, 0x29A6A, 0x29AA8]
ROPE_PULLING = [0x29A46, 0x29A6A]   # being pulled, pulled: the rope a hanging hero has (preferred to the nearest)
ROPE_HELD = 0x10E820
OBJECTS = 96
ROPE_NEAR_PX, ROPE_HAND_PX = 32, 10
ROPE_HAND_PX_FACING_LEFT = 7

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


def hero_only(reg, body, tag=""):
    """68000 source that runs `body` only for our hero while it is being drawn with a big frame (the flag
    the drawing hook sets in PAIR_RAM +5), else skips it. `tag` makes the labels unique when one routine
    uses this more than once."""
    out = ""
    for i, obj in enumerate(HERO_OBJECTS):
        out += """
    cmpa.l #0x%(obj)X,%%%(reg)s
    beq hero%(tag)s_%(i)d""" % {"obj": obj, "reg": reg, "tag": tag, "i": i}
    out += """
    cmpa.l 0x%(red)X,%%%(reg)s                | the red rival, while he's a hero
    beq hero%(tag)s_%(i)d
    bra done%(tag)s""" % {"red": RED_OBJ, "reg": reg, "tag": tag, "i": len(HERO_OBJECTS)}
    for i, ram in enumerate(PAIR_RAM + [RED_PAIR]):
        out += """
hero%(tag)s_%(i)d:
    tst.b 0x%(flag)X                      | drawn with a big frame?
    beq done%(tag)s
    bra hero%(tag)s""" % {"tag": tag, "i": i, "flag": ram + 5}
    return out + """
hero%(tag)s:
%(body)sdone%(tag)s:
""" % {"tag": tag, "body": body}


_vine_labels = [0]
_rope_code = [None]


def rope_routine():
    """68000 source: d1.w = how far the nearest lottery rope's cord is from the hero (a0) in x, Z clear - or Z set
    if there are no ropes or none within ROPE_NEAR_PX. Called by x_shift for a hero hanging (one copy, not one per
    hook)."""
    codes = "".join("""
    cmp.l #0x%X,%%d1
    beq %s""" % (c, "5f" if c in ROPE_PULLING else "2f") for c in ROPE_CODES)
    return """
    moveq #0,%%d1
    tst.w 0x%(held)X                      | lottery ropes in the room?
    beq 9f
    movem.l %%d0/%%d2-%%d4/%%a1,-(%%sp)
    lea 0x104000,%%a1                     | the nearest rope object: its x offset in d3
    moveq #%(last)d,%%d0
    move.w #0x7FFF,%%d2
    moveq #0,%%d3
1:  move.l 4(%%a1),%%d1%(codes)s
    bra 4f
5:  bsr 6f                              | the rope being pulled: his, if he's near it (the game may give him
    cmp.w #%(near)d,%%d4                  | one further than another - 20px against 12, the user's rope_float2)
    bhi 4f
    moveq #0,%%d4
    bra 3f
2:  bsr 6f
3:  cmp.w %%d2,%%d4
    bcc 4f
    move.w %%d4,%%d2
    move.w %%d1,%%d3
4:  lea 0x80(%%a1),%%a1
    dbf %%d0,1b
    moveq #0,%%d1
    cmp.w #%(near)d,%%d2                  | near enough: on the rope
    bhi 8f
    move.w %%d3,%%d1
    movem.l (%%sp)+,%%d0/%%d2-%%d4/%%a1
    andi.b #0xFB,%%ccr
    rts
8:  movem.l (%%sp)+,%%d0/%%d2-%%d4/%%a1
    ori.b #0x04,%%ccr
9:  rts
6:  move.w 2(%%a1),%%d1                   | d1 = the rope's x offset, d4 = its distance
    sub.w 2(%%a0),%%d1
    move.w %%d1,%%d4
    bpl 7f
    neg.w %%d4
7:  rts
""" % {"held": ROPE_HELD, "last": OBJECTS - 1, "codes": codes, "near": ROPE_NEAR_PX * 128}


def x_shift(dreg, px=None, facing_left=False):
    """Nudge the big art left (plus the vine-climbing correction while on a vine; mirrored facing left)."""
    _vine_labels[0] += 1
    v = {"n": _vine_labels[0], "d": dreg, "op": "add" if facing_left else "sub", "side": _side_table[0],
         "left": (HERO_LEFT_PX if px is None else px) * 128, "vine": VINE_PX * 128, "held": ROPE_HELD, "hand": (ROPE_HAND_PX_FACING_LEFT if facing_left else ROPE_HAND_PX) * 128, "rope": _rope_code[0]}
    vine = """
    %(op)s.w #%(vine)d,%%%(d)s""" % v
    vine += """
    move.l %%d1,-(%%sp)                   | hanging on a lottery rope: his big hand drawn on its cord
    jsr 0x%(rope)X
    beq 7f
    add.w %%d1,%%%(d)s
    sub.w #%(hand)d,%%%(d)s
7:  move.l (%%sp)+,%%d1""" % v
    v["vine_code"] = vine
    v["states"] = "".join("""
    cmp.b #%d,104(%%a0)
    beq vine%d""" % (st, v["n"]) for st in VINE_STATES)
    return """
    sub.w #%(left)d,%%%(d)s
    movem.l %%d0/%%a1,-(%%sp)              | and by the hero state's entry in the side table
    moveq #0,%%d0
    move.b 104(%%a0),%%d0
    and.w #0x7F,%%d0
    add.w %%d0,%%d0
    lea 0x%(side)X,%%a1
    move.w (%%a1,%%d0.w),%%d0
    %(op)s.w %%d0,%%%(d)s
    movem.l (%%sp)+,%%d0/%%a1%(states)s
    clr.w 0x%(held)X
    bra novine%(n)d
vine%(n)d:%(vine_code)s
novine%(n)d:
""" % v


_up_table = [None]
_side_table = [None]


def y_shift(dreg):
    """Raise the big art by the hero's state's entry in the UP_PX table (HERO_UP_PX unless overridden)."""
    return """
    movem.l %%d0/%%a1,-(%%sp)
    moveq #0,%%d0
    move.b 104(%%a0),%%d0
    and.w #0x7F,%%d0
    add.w %%d0,%%d0
    lea 0x%(up)X,%%a1
    move.w (%%a1,%%d0.w),%%d0
    add.w %%d0,%%%(d)s
    movem.l (%%sp)+,%%d0/%%a1
""" % {"up": _up_table[0], "d": dreg}


def carried_shift(dreg, tag=""):
    """Raise an enemy being carried (code CARRIED_CODE; +126 = which player carries it) while that player's
    hero is drawn big - drawing only, its real position is the game's."""
    return """
    cmpi.l #0x%(code)X,4(%%a0)
    bne cdone%(tag)s
    tst.b 126(%%a0)                       | carried by player 2?
    bne cp2%(tag)s
    tst.b 0x%(p1)X
    bra ctest%(tag)s
cp2%(tag)s:
    tst.b 0x%(p2)X
ctest%(tag)s:
    beq cdone%(tag)s
    add.w #%(up)d,%%%(d)s
cdone%(tag)s:
""" % {"code": CARRIED_CODE, "tag": tag, "p1": PAIR_RAM[0] + 5, "p2": PAIR_RAM[1] + 5, "up": CARRY_UP_PX * 128,
       "d": dreg}


def hook(rom, site, expect_hex, source, why):
    """Replace the instructions at `site` (expect_hex) with a jsr into new code holding `source`."""
    expect = bytes.fromhex(expect_hex)
    assert len(expect) >= 6
    cave = rom.place_code(source, why=why)
    rom.write(site, bytes.fromhex("4EB9") + cave.to_bytes(4, "big") + bytes.fromhex("4E71") * ((len(expect) - 6) // 2),
              expect=expect, why="now goes through the new code above")


def relocated(code, start, end):
    """68000 source for `code` (the bytes at start-end) to run anywhere: branches and pc-relative calls inside go to
    labels, outside to absolute addresses (a conditional branch out through a jmp); everything else as it is."""
    with tempfile.NamedTemporaryFile(suffix=".bin") as f:
        f.write(code)
        f.flush()
        dis = subprocess.run(["m68k-neogeo-elf-objdump", "-D", "-b", "binary", "-m", "m68k",
                              "--adjust-vma=0x%X" % start, f.name], capture_output=True, text=True, check=True).stdout
    insns = []
    for line in dis.splitlines():
        m = re.match(r"\s+([0-9a-f]+):\t((?:[0-9a-f]{4} ?)+)\s*(?:\t(.*))?$", line)
        if not m:
            continue
        at, words, text = int(m.group(1), 16), m.group(2).split(), (m.group(3) or "").strip()
        if text:
            insns.append([at, words, text])
        else:
            insns[-1][1] += words                   # a long instruction's further words
    out, outside = [], {}
    for at, words, text in insns:
        out.append("L%X:" % at)
        mn, _, ops = text.partition(" ")
        ops = ops.strip()
        b = re.match(r"^(b(?:ra|sr|hi|ls|cc|cs|ne|eq|vc|vs|pl|mi|ge|lt|gt|le))[swl]?$", mn)
        target = re.search(r"0x([0-9a-f]+)$", ops)
        if b and target and "%" not in ops:
            t, cc = int(target.group(1), 16), b.group(1)
            if start <= t < end:
                out.append("    %s L%X" % (cc, t))
            elif cc in ("bra", "bsr"):
                out.append("    %s 0x%X" % ("jmp" if cc == "bra" else "jsr", t))
            else:
                outside[t] = "X%X" % t
                out.append("    %s X%X" % (cc, t))
        elif mn.startswith("db") and target:
            t = int(target.group(1), 16)
            assert start <= t < end, text
            out.append("    %s %s,L%X" % (mn, ops.split(",")[0], t))
        elif mn in ("jsr", "jmp") and "%pc@" in ops:
            t = int(re.search(r"%pc@\(0x([0-9a-f]+)\)", ops).group(1), 16)
            out.append("    %s %s" % (mn, ("L%X" % t) if start <= t < end else "0x%X" % t))
        else:
            assert "%pc" not in ops, text
            out.append("    .word " + ",".join("0x" + w for w in words))
    for t, label in sorted(outside.items()):
        out.append("%s: jmp 0x%X" % (label, t))
    return "\n".join(out) + "\n"


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
    and its palette). An entry 1, attribute, [palette,] [high byte,] low byte changes the high byte (attribute bit
    5) and the flips from then on (bits 0 / 1: e.g. the ocarina frames' tiles are stored mirrored)."""
    p = rom.u32(hackbuild.FRAME_TABLE + frame)
    d = rom.data
    cols, rows, _, palette, hi = d[p:p + 5]
    q, px, st = p + 5, {}, {"hi": hi, "flip": 0}

    def tile(q):
        b = d[q]
        q += 1
        if b == 1:
            a, q = d[q], q + 1
            if a & 0x80:
                raise SystemExit("frame_pixels: frame 0x%X uses an unknown entry" % frame)
            if a & 0x40:
                q += 1
            if a & 0x20:
                st["hi"], q = d[q], q + 1
            st["flip"] = a & 3
            b, q = d[q], q + 1
        return (st["hi"] << 8 | b if b else None), q

    def put(t, x0, y0):
        art = rom.sprite_tile(t)
        for y in range(16):
            for x in range(16):
                v = art[15 - y if st["flip"] & 2 else y][15 - x if st["flip"] & 1 else x]
                if v:
                    px[x0 + x, y0 + y] = v
    for c in range(cols + 1):
        for r in range(rows + 1):
            t, q = tile(q)
            if t is not None:
                put(t, c * 16, r * 16)
    while d[q] != 0xFF:
        n, x, up, _, st["hi"] = d[q:q + 5]
        q += 5
        x, up = (x ^ 0x80) - 0x80, (up ^ 0x80) - 0x80
        for r in range(n + 1):
            t, q = tile(q)
            if t is not None:
                put(t, x * 2, r * 16 - up * 2)
    return px, palette


def upscaled_pixels(rom, frame):
    """`frame` (with its pieces) 1.5x as big (each pixel to 1 or 2 rows / columns, nearest): ({(x, y): colour} from
    the main block's top left, palette, main block's tiles across, down)."""
    src, palette = frame_pixels(rom, frame)
    big = {}
    xs, ys = [x for x, _ in src], [y for _, y in src]
    for y in range(min(ys) * 3 // 2 - 1, max(ys) * 3 // 2 + 2):
        for x in range(min(xs) * 3 // 2 - 1, max(xs) * 3 // 2 + 2):
            v = src.get((x * 2 // 3, y * 2 // 3))
            if v:
                big[x, y] = v
    p = rom.u32(hackbuild.FRAME_TABLE + frame)
    return big, palette, (rom.data[p] + 1) * 3 // 2, (rom.data[p + 1] + 1) * 3 // 2


def upscaled_frame(rom, frame):
    """A new frame: `frame` drawn 1.5x as big - its ART if redrawn, else the 1.5x copy. The main block grows from its
    top left; whatever lies outside it becomes pieces again."""
    big, palette, cols, rows = upscaled_pixels(rom, frame)
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ART % frame)
    what = "1.5x"
    if os.path.exists(path):
        from png_tiles import read_indices, neo_to_rgb
        colours = [neo_to_rgb(int(w, 16)) for w in PALETTE_COLOURS[palette].split()]
        px = read_indices(path, colours)
        if (len(px[0]), len(px)) != (cols * 16 + 2 * MARGIN, rows * 16 + 2 * MARGIN):
            raise SystemExit("hero-big-art: %s must be %dx%d" % (ART % frame, cols * 16 + 2 * MARGIN,
                                                                 rows * 16 + 2 * MARGIN))
        big = {(x - MARGIN, y - MARGIN): v for y, row in enumerate(px) for x, v in enumerate(row) if v}
        what = "redrawn"
    return frame_from_pixels(rom, big, palette, cols, rows, frame, what)


def frame_from_pixels(rom, big, palette, main_cols, main_rows, frame, what, keep=None):
    """A new frame from {(x, y): colour} (x, y from the main block's top left): a main block of main_cols x
    main_rows tiles, whatever lies outside it as pieces; and its player 2 copy (as `frame`'s, in its palette).
    keep: {(column, row): an existing tile} used again where the cell's pixels are that tile's."""
    cells = {}
    for (x, y), v in big.items():
        cells.setdefault((x // 16, y // 16), {})[x % 16, y % 16] = v

    def new_tile(cell):
        block = [[cells[cell].get((x, y), 0) for x in range(16)] for y in range(16)]
        if keep and cell in keep and rom.sprite_tile(keep[cell]) == block:
            return keep[cell]
        return rom.add_sprite_tile(block, why="big hero frame 0x%X, %s" % (frame, what), share=True)
    out = [[new_tile((c, r)) if (c, r) in cells else None for c in range(main_cols)] for r in range(main_rows)]
    pieces = []
    for c in sorted({c for c, _ in cells}):
        rs = sorted(r for cc, r in cells if cc == c and not (0 <= c < main_cols and 0 <= r < main_rows))
        while rs:
            run = [rs.pop(0)]
            while rs and rs[0] == run[-1] + 1:
                run.append(rs.pop(0))
            pieces.append((c * 8, -run[0] * 8, [new_tile((c, r)) for r in run]))
    n = rom.add_frame(out, palette, why="big hero: frame 0x%X, %s" % (frame, what), pieces=pieces)
    rom.data[rom.u32(hackbuild.FRAME_TABLE + n) + 2] = BURN_MODE
    p2_palette = rom.data[rom.u32(hackbuild.FRAME_TABLE + frame + P2_FRAMES) + 3]
    if p2_palette != palette:                 # player 2's copy of the frame: the same art in its own palette
        m = rom.add_frame(out, p2_palette, why="big hero: frame 0x%X, %s, player 2" % (frame, what), pieces=pieces)
        rom.data[rom.u32(hackbuild.FRAME_TABLE + m) + 2] = BURN_MODE
        P2_COPIES[n] = m
    return n


def spread_antennas(rom, frame):
    """The big standing frame `frame` (0x364 / 0x368: both antennas straight up, side by side) with its right
    antenna leaning out, as the small art's standing pose has it - that antenna as the big walk frame 0x314 draws
    it (its head 1 px lower: moved up 1). Columns / rows as in 0x364."""
    px, palette = frame_pixels(rom, frame)
    lean = frame_pixels(rom, ANTENNA_FROM)[0]
    for y in range(5, 12):                    # the straight right antenna out
        for x in range(23, 27):
            px.pop((x, y), None)
    for y in range(7, 13):                    # the leaning one in (it starts at x = 36 - y)
        for x in range(36 - y, 33):
            if (x, y) in lean:
                px[x, y - 1] = lean[x, y]
    for x in range(23, 27):                   # where it joins the head
        if (x, 13) in lean:
            px[x, 12] = lean[x, 13]
    p = rom.u32(hackbuild.FRAME_TABLE + frame)
    tiles = rom.frame_tiles(frame)[0]        # the cells left alone keep their tiles
    keep = {(c, r): t for r, row in enumerate(tiles) for c, t in enumerate(row) if t is not None}
    return frame_from_pixels(rom, px, palette, rom.data[p] + 1, rom.data[p + 1] + 1, frame, "antennas spread",
                             keep)


def red_boxes(rom, frame_map):
    """Red drawn big keeps the small art's hit box (object+8 is the normal frame), so a leaf could touch the big
    art and miss him. When the overlap test (0xB642) checks an object against the noted Red, it now takes a box
    from RED_BOXES: his small frame's outer box (y offset, height, x offset, width; x128) RED_BOX_SIDE_PX wider
    each side and RED_BOX_UP_PX taller - between the small art's and the big art's (the big frames' own boxes made
    the duel too easy, and sit off the nudged art's middle)."""
    made, table = {}, b""
    for f in range(0, NORMAL_FRAMES, 4):
        q = rom.u32(BOXES + f)
        if q not in made:
            yoff, h, xoff, w = (rom.u16(q + i) for i in range(0, 8, 2))
            rec = b"".join(v.to_bytes(2, "big") for v in (yoff, h + RED_BOX_UP_PX * 128,
                                                          (xoff - RED_BOX_SIDE_PX * 128) & 0xFFFF,
                                                          w + 2 * RED_BOX_SIDE_PX * 128, 0))
            made[q] = rom.alloc(len(rec), align=2)
            rom.data[made[q]:made[q] + len(rec)] = rec
        table += made[q].to_bytes(4, "big")
    at = rom.alloc(len(table), align=2)
    rom.data[at:at + len(table)] = table
    hook(rom, BOX_LOOKUP, "3A28000824715000",
         "    move.w 8(%%a0),%%d5\n"
         "    cmpa.l 0x%X,%%a0\n"
         "    bne 1f\n"
         "    and.w #0x7FF,%%d5\n"
         "    cmp.w #0x%X,%%d5\n"
         "    bcc 2f\n"
         "    lea 0x%X,%%a2\n"
         "    movea.l (%%a2,%%d5.w),%%a2\n"
         "    rts\n"
         "2:  move.w 8(%%a0),%%d5\n"
         "1:  movea.l (%%a1,%%d5.w),%%a2\n"
         "    rts\n" % (RED_OBJ, NORMAL_FRAMES, at),
         "overlap test: Red drawn big is hit as the big art")


def apply(rom):
    original = bytes(rom.data[COPY_START:COPY_END])   # the drawing routine before the hooks below
    stub = rom.place_code("    jmp 0x%X\n" % 0xFFFFF0, why="hero big art: into the drawing routine's copy")
    ROW_OVERRIDES[STANDING_ANIM] = [spread_antennas(rom, f) for f in BREATHE]
    rows, frame_map = big_frame_tables(rom)
    hook(rom, ROPE_IDLE, "4A2E78CB66000052", """
    move.w #1,0x%X
    tst.b 0x78CB(%%a6)
    beq 1f
    addq.l #4,%%sp
    jmp 0x29A44
1:  rts
""" % ROPE_HELD, "lottery ropes: note that they're there (for the big hero hanging on one)")
    red_boxes(rom, frame_map)
    fidget, q = [], rom.u32(ANIM_TABLE + 4 * FIDGET_ANIM)
    while rom.u16(q) < 0xFFFE:
        w = rom.u16(q)
        if w < 0x8000 and (w & 0x3FFC) < NORMAL_FRAMES and (w & 0x3FFC) not in fidget:
            fidget.append(w & 0x3FFC)
        q += 4 if w >= 0x8000 else 2
    for frame in SWIM_FIXES:
        at = rom.u32(hackbuild.FRAME_TABLE + frame)
        k = bytes(rom.data[at:at + 32]).index(b"\x01\x40\x5f\x00")
        rom.write(at + k, b"\x00\x01\x40\x5f", expect=b"\x01\x40\x5f\x00",
                  why="big flipper swim frame 0x%X: its palette switch on a tile, not a stray one" % frame)
    for small, big in SWIM_BIG.items():
        frame_map[small] = big
    for f in OCARINA_FRAMES + fidget:
        frame_map[f] = upscaled_frame(rom, f)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    drawn = {}                                # the throws: the redrawn ones
    for f, art in THROW_ART.items():
        if os.path.exists(os.path.join(root, ART % art)):
            if art not in drawn:
                drawn[art] = upscaled_frame(rom, art)
            frame_map[f] = drawn[art]
    if os.path.exists(os.path.join(root, ART % THROW_MID)):
        frame_map[THROW_MID] = upscaled_frame(rom, THROW_MID)
        for n in THROW_ANIMS:
            at = rom.u32(ANIM_TABLE + 4 * n) + 2
            w = rom.u16(at)
            rom.write(at, (THROW_MID | w & 3).to_bytes(2, "big"),
                      why="throw animation 0x%X: its second step the in-between (was its release)" % n)
    if os.path.exists(os.path.join(root, ART % THROW_FOLLOW)):
        for n in THROW_ANIMS:
            at = rom.u32(ANIM_TABLE + 4 * n) + 6
            w = rom.u16(at)
            assert w < 0x8000 and rom.u16(at + 2) >= 0xFFFE, "throw animation 0x%X: not four steps" % n
            rom.write(at, (THROW_FOLLOW | w & 3).to_bytes(2, "big"),
                      why="throw animation 0x%X: its last step the follow-through (was its release)" % n)
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
    first_new = hackbuild.FRAME_FREE_START
    p2_end = max(list(P2_COPIES) + [first_new - 4]) + 4
    data = ("p2_tab:\n    .word %s\n" % ",".join("0x%X" % P2_COPIES.get(f, f) for f in range(first_new, p2_end, 4)) +
            "burn_tab:\n    .word %s\n" % ",".join("0x%X" % burned[f] for f in (0x11C, 0x120, 0x124, 0x128)) +
            "row_off:\n    .word %s\n" % ",".join(str(o) for o in offs) +
            "row_len:\n    .byte %s\n    .even\n" % ",".join(str(min(255, len(r))) for r in rows) +
            "rows:\n" + "".join("    .word %s\n" % ",".join("0x%X" % v for v in row) for row in rows if row) +
            "frame_map:\n    .word %s\n" % ",".join("0x%X" % frame_map.get(f, 0) for f in range(0, NORMAL_FRAMES, 4)))

    def hero_check(reg):
        """To 1f if `reg` is a hero (or the red rival) - else on."""
        out = "".join("""
    cmpa.l #0x%X,%%%s
    beq 1f""" % (obj, reg) for obj in HERO_OBJECTS)
        return out + """
    cmpa.l 0x%X,%%%s
    beq 1f
""" % (RED_OBJ, reg)

    def pair(reg, ram):
        """`ram` = the hero `reg`'s pair RAM (player 1's, player 2's, else the red rival's)."""
        return """
    lea 0x%(p1)X,%%%(ram)s
    cmpa.l #0x%(hero1)X,%%%(reg)s
    beq 2f
    lea 0x%(p2)X,%%%(ram)s
    cmpa.l #0x%(hero2)X,%%%(reg)s
    beq 2f
    lea 0x%(red)X,%%%(ram)s
2:
""" % {"p1": PAIR_RAM[0], "p2": PAIR_RAM[1], "red": RED_PAIR, "hero1": HERO_OBJECTS[0], "hero2": HERO_OBJECTS[1],
       "reg": reg, "ram": ram}

    def restore(i, load_obj):
        """Each hero's +34 / +36 / +38 put back as its normal frame gives them (pair RAM +7: which are due)."""
        return """
%(load)s    btst #0,7(%%a1)
    beq no34_%(i)s
    move.w 8(%%a1),34(%%a0)
no34_%(i)s:
    btst #1,7(%%a1)
    beq no36_%(i)s
    move.w 10(%%a1),36(%%a0)
no36_%(i)s:
    btst #2,7(%%a1)
    beq nozoom_%(i)s
    move.w 12(%%a1),38(%%a0)
nozoom_%(i)s:
    clr.b 7(%%a1)
""" % {"i": i, "load": load_obj}

    restores = "".join(restore(i, "    lea 0x%X,%%a1\n    lea 0x%X,%%a0\n" % (ram, obj))
                       for i, (ram, obj) in enumerate(zip(PAIR_RAM, HERO_OBJECTS)))
    restores += restore("r", "    lea 0x%X,%%a1\n    move.l 0x%X,%%a0\n    cmpa.w #0,%%a0\n    beq nozoom_r\n"
                        % (RED_PAIR, RED_OBJ))
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
    cmpa.l #HERO_END,%a0              | (quickly past for most objects: not a hero, not Red - his frames are
    bcs 15f
    cmpa.l RED_OBJ_RAM,%a0            | player 2's copies, 0x800-0xFFF - and not carried)
    beq 15f
    cmp.w #0x800,%d3
    bcs 16f
    cmp.w #0x1000,%d3
    bcs 15f
16: cmpi.l #CARRIED_CODE_ADDR,4(%a0)
    beq 18f
    move.l (%a3,%d3.w),%a5
    rts
18: st BIG_NOW_RAM                   | a carried enemy: on in the drawing routine's copy, with the hooks
    move.l (%a3,%d3.w),%a5
    move.l #COPY_STUB,(%sp)
    rts
15: clr.b BIG_NOW_RAM                 | set below if this object is drawn big
    move.l %d4,-(%sp)
    move.w %d3,%d4                  | Red (an object drawing player 2's copies, not a player's hero): noted
    and.w #0xF800,%d4
    cmp.w #0x800,%d4
    bne 11f
    move.w %d3,%d4
    and.w #0x7FF,%d4
    cmp.w #NORMAL_FRAMES,%d4
    bcc 11f
    cmpi.l #RED_CODE_LO,4(%a0)      | the ending's objects only - e.g. the title screen's green player stays small
    bcs 13f
    cmpi.l #RED_CODE_HI,4(%a0)
    bcs 14f
13: cmpi.l #RED_DUEL_LO,4(%a0)      | ... or the torch duel's
    bcs 11f
    cmpi.l #RED_DUEL_HI,4(%a0)
    bcc 11f
14:
HERO_ONLY_A0    move.l %a0,RED_OBJ_RAM
    bra 12f
11: cmpa.l RED_OBJ_RAM,%a0             | the noted object drawing something else: forgotten
    bne 12f
    clr.l RED_OBJ_RAM
12: move.l (%sp)+,%d4
HERO_A0    bra 9f
1:  move.l %a1,-(%sp)
PAIR_A0    clr.b 5(%a1)                    | 1 = this draw uses a big frame: the +34 fix and the position nudges
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
    st BIG_NOW_RAM
    move.w (%sp)+,%d4
    and.w #0x800,%d4
    cmp.w #NEW_FRAMES,%d3           | frames made here: player 2's copy from p2_tab, if it has one
    bcs 46f
    tst.w %d4
    beq 8f
    cmp.w #P2_TAB_END,%d3
    bcc 8f
    move.w %d3,%d4
    sub.w #NEW_FRAMES,%d4
    lsr.w #1,%d4
    lea p2_tab(%pc),%a5
    move.w (%a5,%d4.w),%d3
    bra 8f
46:
    add.w %d4,%d3                   | player 2: its copy of the big frame
    bra 8f
4:  move.w (%sp)+,%d3               | as it is
8:  tst.b 5(%a1)                    | drawn big: return through `restore` (the stack holds a1, the return
    beq 7f                          | to 0xA430, then the drawing loop's return address)
    cmpi.w #0xFFFF,38(%a0)          | being zoomed (the C-button shrink): zoom the big art further
    beq 6f
    movem.l %d0-%d2,-(%sp)
    move.w 38(%a0),12(%a1)          | set back after the draw
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
    tst.b BIG_NOW_RAM                 | drawn big: on in the drawing routine's copy, with the hooks (the
    beq 10f                           | original, for every other object, has none: they slowed every draw
    move.l #COPY_STUB,(%sp)           | down enough that the sprites' update ran into the top of the picture)
10: rts

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
    moveq #11,%d5                   | as 0xA50A
    move.w %d4,%d6
    lsl.w %d5,%d6
    addi.w #0x780,%d6
    move.w %d6,34(%a0)
    add.w 2(%a0),%d6
    move.w %d6,664(%a6)
    bra 22f
20: moveq #11,%d5                   | as 0xA522
    move.w %d4,%d6
    lsl.w %d5,%d6
    addi.w #0x780,%d6
    neg.w %d6
    move.w #0,34(%a0)
    move.w 2(%a0),%d5
    move.w %d5,664(%a6)
    add.w %d5,%d6
    rts                             | +34 is 0 here whatever the width
21: moveq #10,%d5                   | as 0xA540
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
    btst #2,33(%a0)                 | the case above: 4 -> (w+1)<<10, 8/12 -> (w<<11)+0x780
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
24: move.w %d7,8(%a1)                | set back after the draw - the drawing itself uses the big value
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
    moveq #11,%d5                   | as 0xA568
    move.w %d3,%d6
    lsl.w %d5,%d6
    addi.w #0x780,%d6
    move.w %d6,36(%a0)
    neg.w %d6
    add.w 0(%a0),%d6
    move.w %d6,666(%a6)
    bra 32f
30: move.w #0,36(%a0)               | as 0xA582: +36 is 0 whatever the height
    move.w 0(%a0),666(%a6)
    rts
31: moveq #10,%d5                   | as 0xA590
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
    btst #0,33(%a0)                 | the case above: 1 -> (h+1)<<10, 2/3 -> (h<<11)+0x780
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
    tokens = [   # in this order: HERO_A0F / HERO_A0H before HERO_A0, PAIR_A0F / PAIR_A0H before PAIR_A0
        ("HERO_ONLY_A0", "".join("    cmpa.l #0x%X,%%a0\n    beq 12f\n" % obj for obj in HERO_OBJECTS)),
        ("RED_OBJ_RAM", "0x%X" % RED_OBJ), ("BIG_NOW_RAM", "0x%X" % BIG_NOW),
        ("CARRIED_CODE_ADDR", "0x%X" % CARRIED_CODE), ("COPY_STUB", "0x%X" % stub),
        ("HERO_END", "0x%X" % (max(HERO_OBJECTS) + 0x80)),
        ("RED_CODE_LO", "0x%X" % RED_CODE[0]), ("RED_CODE_HI", "0x%X" % RED_CODE[1]),
        ("RED_DUEL_LO", "0x%X" % RED_DUEL_CODE[0]), ("RED_DUEL_HI", "0x%X" % RED_DUEL_CODE[1]),
        ("HERO_A0F", hero_check("a0")), ("PAIR_A0F", pair("a0", "a1")),
        ("HERO_A0H", hero_check("a0")), ("PAIR_A0H", pair("a0", "a1")),
        ("HERO_A5", hero_check("a5")), ("HERO_A0", hero_check("a0")),
        ("PAIR_A5", pair("a5", "a2")), ("PAIR_A0", pair("a0", "a1")),
        ("NORMAL_ANIMS", "0x%X" % NORMAL_ANIMS), ("NORMAL_FRAMES", "0x%X" % NORMAL_FRAMES),
        ("ANIM_TABLE", "0x%X" % ANIM_TABLE), ("NEW_FRAMES", "0x%X" % first_new), ("P2_TAB_END", "0x%X" % p2_end),
        ("BURN_STATE", "33"), ("DRAW_LOOP_RETURN", "0x%X" % DRAW_LOOP_RETURN),
        ("ZOOM_SHRINK", str(ZOOM_SHRINK)), ("ZOOM_GROW", str(ZOOM_GROW)), ("RESTORES", restores), ("DATA", data)]
    for token, value in tokens:
        src = src.replace(token, value)
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
    _rope_code[0] = rom.place_code(rope_routine(), why="hero big art: the lottery rope a hanging hero holds")
    _up_table[0] = rom.place_code(
        "    .word %s\n" % ",".join(str(UP_PX.get(n, HERO_UP_PX) * 128) for n in range(STATES)),
        why="hero big art: how far up to draw it, per hero state")
    # Each draw hook: the instructions it replaces, with (for the hero drawn big) the nudge after the position's
    # worked out - X: x_shift; Y: y_shift and carried_shift; a sprite's pieces: both. In this order (their code is
    # placed as they're made).
    def lines(instructions):
        return "".join("    %s\n" % i for i in instructions)

    def x_part(reg, tag, left):
        return hero_only("a0", x_shift(reg, HERO_LEFT_PX_FACING_LEFT, True) if left else x_shift(reg), tag)

    def y_part(reg, tag):
        return hero_only("a0", y_shift(reg), tag) + carried_shift(reg, tag)

    hooks = [   # (site, the bytes there, what, the new code)
        (DRAW_X_ZOOMED, "044540003C3C0100", "sprite X (facing left, zoomed)",
         lines(["sub.w #0x4000,%d5"]) + x_part("d5", "", True) + lines(["move.w #256,%d6", "rts"])),
        (DRAW_X_PLAIN, "044640003486", "sprite X (usual path)",
         lines(["sub.w #0x4000,%d6"]) + x_part("d6", "", False) + lines(["move.w %d6,(%a2)", "rts"])),
        (DRAW_Y_ZOOMED, "0445B7FF7C01", "sprite Y (zoomed path)",
         lines(["sub.w #-18433,%d5"]) + y_part("d5", "") + lines(["moveq #1,%d6", "rts"])),
        (DRAW_Y_PLAIN, "0447B7FFDE433487", "sprite Y (usual path)",
         lines(["sub.w #-18433,%d7", "add.w %d3,%d7"]) + y_part("d7", "") + lines(["move.w %d7,(%a2)", "rts"])),
        (PIECES_BASE, "0447B7FF48473E2E029804474000", "sprite pieces' base position",
         lines(["sub.w #-18433,%d7"]) + y_part("d7", "y") +
         lines(["swap %d7", "move.w 664(%fp),%d7", "sub.w #0x4000,%d7"]) + x_part("d7", "x", False) + lines(["rts"])),
        # the same for the hero facing left
        (LEFT_X, "044540003485", "sprite X (facing left)",
         lines(["sub.w #0x4000,%d5"]) + x_part("d5", "lx", True) + lines(["move.w %d5,(%a2)", "rts"])),
        (LEFT_Y, "0447B7FFDE433487", "sprite Y (facing left)",
         lines(["sub.w #-18433,%d7", "add.w %d3,%d7"]) + y_part("d7", "ly") + lines(["move.w %d7,(%a2)", "rts"])),
        (LEFT_PIECES, "0447B7FF48473E28000204474000", "sprite pieces' base position (facing left)",
         lines(["sub.w #-18433,%d7"]) + y_part("d7", "py") +
         lines(["swap %d7", "move.w 2(%a0),%d7", "sub.w #0x4000,%d7"]) + x_part("d7", "px", True) + lines(["rts"])),
        # and the zoomed path facing right
        (RIGHT_X_ZOOMED, "044640003486", "sprite X (facing right, zoomed)",
         lines(["sub.w #0x4000,%d6"]) + x_part("d6", "rzx", False) + lines(["move.w %d6,(%a2)", "rts"])),
        (RIGHT_Y_ZOOMED, "0445B7FF7C01", "sprite Y (facing right, zoomed)",
         lines(["sub.w #-18433,%d5"]) + y_part("d5", "rzy") + lines(["moveq #1,%d6", "rts"])),
    ]
    for site, expect, what, source in hooks:
        hook(rom, site, expect, source, what)

    # The drawing routine with all the hooks above, as a copy only the big hero (and a carried enemy) is drawn by:
    # the original, for every other object, is as it was.
    copy = rom.place_code(relocated(bytes(rom.data[COPY_START:COPY_END]), COPY_START, COPY_END),
                          why="hero big art: the drawing routine's copy with the hooks")
    rom.write(stub + 2, copy.to_bytes(4, "big"), why="hero big art: into the drawing routine's copy")
    rom.data[COPY_START:COPY_END] = original
    rom.log.append("  0x%06X  %d byte(s)  the drawing routine as it was (its hooks only in the copy)" %
                   (COPY_START, COPY_END - COPY_START))
    # The art's definitions share the free space with every later patch's code, and its frames their frame numbers -
    # a redrawn frame can change both, which moved the later code (old saves then crash). So this patch always ends
    # at ART_END / FRAMES_END (where it ended 2026-10-21): later patches stay put as the art changes.
    assert rom.next_free <= ART_END, "hero-big-art: the art outgrew ART_END (0x%X > 0x%X)" % (rom.next_free, ART_END)
    assert rom.next_frame <= FRAMES_END, "hero-big-art: more frames than FRAMES_END (0x%X)" % rom.next_frame
    rom.log.append("  hero-big-art: %d byte(s), %d frame number(s) to spare" % (ART_END - rom.next_free,
                                                                              (FRAMES_END - rom.next_frame) // 4))
    rom.next_free, rom.next_frame = ART_END, FRAMES_END
