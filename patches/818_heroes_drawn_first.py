NAME = "heroes-drawn-first"
DESCRIPTION = "The heroes are drawn first each frame, so their sprites are written before the picture starts (no tearing on busy screens)"

# The user, 2026-11-17: on a busy screen by the lava cave's goal, Blue tore for a frame at a time - a strip of him a
# few lines tall shifted sideways - when he was high on the screen. The game writes its sprites each frame while the
# picture is already being drawn: the front group's objects in their sorted order (+0x28, highest first), each taking
# the next sprites up from the group's first (0x1002E4). Blue (0x80) comes after the fire, the goal stalk and the
# other 0xFD objects, so on busy frames his writes landed on lines 14-32, and when he was that high the beam caught
# his columns half written (measured on the user's slow_goal recording).
#
# So the front group is drawn in three passes (GROUP_START, as the group starts): the heroes' run of the list first,
# in HERO_ROOM sprites from HEROES_FROM; then what's before them in the list, from the group's own first sprite up to
# HEROES_FROM; then what's after them, from HEROES_FROM + HERO_ROOM on (the game's own pass, so the group's end word
# is its real end, as drown-in-front and sold-out-stamp expect). Each part keeps its order and its place in the sprite
# numbers, so what's in front of what is as it was; only the heroes' writing moves forward, and the objects before
# them wait only as long as the heroes take to draw. (Moving the heroes to the list's start put them behind
# everything in the group, the leaves he climbs past and the fire; drawing the heroes and everything after them first
# left the objects before them - a bird at the top of the screen - torn instead.)
#
# The sprite numbers have to stay put from frame to frame: the objects after the heroes are written late, after the
# picture has started, so a sprite that held part of Blue last frame and another object's this frame showed Blue's
# old column, chained onto him, at the top of the picture (the user saw a second Blue beside him). So the heroes always
# have HERO_ROOM sprites (what they don't use cleared in the vblank, right after them), and HEROES_FROM only moves
# when the objects before them come within 4 sprites of it (then to their end + MARGIN; they're clipped beyond it for
# that frame), or when the group would reach CEILING (the gap and the heroes' room push everything after them up). The
# split is made whenever a hero is drawn: switching it on and off would renumber things too. Sprites last frame used
# that nothing uses now are cleared by the game's end-of-pass clearing: each pass's "end last frame" word is raised
# to cover what a move of HEROES_FROM left behind.
GROUP_START = 0xA3BC         # jsr <drown-in-front's grp_start> - the drawing loop, starting a group (a0 = its
                             # descriptor + 8, d2 / d0 its list's first / last entry, d1 its first sprite)
DRAW_GROUP = 0xA3AA          # the drawing loop, from a0 = a group descriptor (list's first and last entry, first
                             # sprite, limit, end last frame - words)
GROUP_END = 0xA406           # the drawing loop, after the last object: clears its sprites up from d1 to the end
                             # last frame, then rts
FRONT = 0x1002E0             # the front group's descriptor
LIST = 0x100500
HEROES = (0x4000, 0x4080)    # player 1's and player 2's hero objects (offsets from 0x100000)
RAM = 0x10D5C0               # spare RAM: +0 the heroes' descriptor, +10 the before part's (5 words each, the end
HERO_DESC, BEFORE_DESC = RAM, RAM + 10   # last frame at +8), +20 HEROES_FROM last frame (0: not split), +22 the
OLD_FROM, HS, HE, START, END, FIRST = (RAM + 20, RAM + 22, RAM + 24,   # heroes' first and last entry, +26 / +28
                                       RAM + 26, RAM + 28, RAM + 30)   # the list's, +30 the group's first sprite
HERO_ROOM = 12               # sprites for the heroes' run, used or not (Blue's big art: 3-6 columns)
MARGIN = 16                  # sprites the objects before the heroes may grow by before HEROES_FROM moves
CEILING = 300                # the group stays below this: sprites from 300 are other code's (pause-menu's box,
                             # the goal's pieces, sold-out-stamp's stamps), which the game's own group never reached


def apply(rom):
    assert rom.u16(GROUP_START) == 0x4EB9
    before = rom.u32(GROUP_START + 2)
    code = rom.place_code("""
    jsr 0x%(before)X
    cmpa.l #0x%(front)X+8,%%a0            | the front group only (not the passes here, nor the other groups)
    bne 99f
    movem.l %%d3-%%d7/%%a1/%%a3-%%a5,-(%%sp)
    lea 0x%(list)X,%%a1
    lea (%%a1,%%d2.w),%%a3              | the first hero drawn, if any (0x4000 and 0x4080 both 0x4000 without bit 7)
    move.w %%d0,%%d3
    sub.w %%d2,%%d3
    lsr.w #1,%%d3                       | (the list's last entry is d0 itself: d3 + 1 entries)
    move.w #0xFF7F,%%d6
    move.w #0x%(h1)X,%%d7
1:  move.w (%%a3)+,%%d5
    and.w %%d6,%%d5
    cmp.w %%d7,%%d5
    dbeq %%d3,1b
    bne 3f
    move.w -2(%%a3),%%d5
    tst.b 0x28(%%a6,%%d5.w)
    bne 2f
    subq.w #1,%%d3                      | (not being drawn: on)
    bcc 1b
    bra 3f
2:  move.l %%a3,%%d4
    sub.l %%a1,%%d4
    subq.w #2,%%d4
    bra 10f
| no hero: drawn as it was, in one pass
3:
    move.w 0x%(front)X+8,0x%(before_desc)X+8   | (a split next frame: the before part as big as all this)
    clr.w 0x%(old_from)X
    movem.l (%%sp)+,%%d3-%%d7/%%a1/%%a3-%%a5
    rts
| the heroes' run of the list: d3 to d7
10: move.w %%d4,%%d3
    move.w %%d4,%%d7
11: cmp.w %%d0,%%d7
    bcc 12f
    move.w %%d7,%%d4
    addq.w #2,%%d4
    bsr 80f
    bne 12f
    move.w %%d4,%%d7
    bra 11b
12: move.w %%d3,0x%(hs)X
    move.w %%d7,0x%(he)X
    move.w %%d2,0x%(start)X
    move.w %%d0,0x%(end)X
    move.w %%d1,0x%(first)X
| d5 the limit, d4 the group's end last frame, d3 the before part's
    move.w 0x%(front)X+6,%%d5
    move.w 0x%(front)X+8,%%d4
    cmpi.w #381,%%d4
    bls 13f
    move.w %%d5,%%d4
    move.w %%d4,0x%(front)X+8
13: move.w 0x%(before_desc)X+8,%%d3
    cmp.w %%d1,%%d3
    bcs 14f
    cmp.w %%d5,%%d3
    bls 15f
14: move.w %%d4,%%d3                    | (not set yet: as big as the whole group)
15: cmp.w %%d3,%%d4                     | the after part clears up to whichever ended later
    bcc 16f
    move.w %%d3,0x%(front)X+8
| d6 HEROES_FROM: as last frame while the before part still fits under it; else the before part's end last frame
| + MARGIN, room left above, not below the group's first
| d7: as high as it may go - the group ending below CEILING, given what the after part used last frame
16: move.w #%(ceiling)d-%(hero_room)d-8,%%d7
    move.w 0x%(old_from)X,%%d6
    cmp.w %%d1,%%d6
    bcs 160f                            | (not set: worked out afresh)
    move.w %%d4,%%d0
    sub.w %%d6,%%d0
    subi.w #%(hero_room)d,%%d0
    ble 151f
    sub.w %%d0,%%d7
151:cmp.w %%d7,%%d6
    bgt 160f
    move.w %%d3,%%d0
    addq.w #4,%%d0
    cmp.w %%d6,%%d0
    bls 18f
160:move.w %%d3,%%d6
    addi.w #%(margin)d,%%d6
    cmp.w %%d7,%%d6
    ble 17f
    move.w %%d7,%%d6
17: cmp.w %%d1,%%d6
    bge 18f
    move.w %%d1,%%d6
| the before part clears from its end to its end last frame - or to the group's if HEROES_FROM rose (the heroes'
| and the after part's sprites then) - and not past HEROES_FROM
18: cmp.w 0x%(old_from)X,%%d6
    bls 19f
    cmp.w %%d4,%%d3
    bcc 19f
    move.w %%d4,%%d3
19: cmp.w %%d6,%%d3
    bls 20f
    move.w %%d6,%%d3
20: move.w %%d3,0x%(before_desc)X+8
    move.w %%d6,0x%(old_from)X
| the heroes, from HEROES_FROM
    lea 0x%(hero_desc)X,%%a0
    move.w 0x%(hs)X,(%%a0)
    move.w 0x%(he)X,2(%%a0)
    move.w %%d6,4(%%a0)
    addi.w #%(hero_room)d,%%d6
    move.w %%d6,6(%%a0)
    move.w %%d6,8(%%a0)                 | (their unused sprites cleared now, in the vblank)
    jsr 0x%(draw)X
| what's before them, from the group's first sprite up to HEROES_FROM
    lea 0x%(before_desc)X,%%a0
    move.w 0x%(hs)X,%%d0
    move.w 0x%(start)X,%%d2
    cmp.w %%d2,%%d0
    bls 21f
    move.w %%d2,(%%a0)
    subq.w #2,%%d0
    move.w %%d0,2(%%a0)
    move.w 0x%(first)X,4(%%a0)
    move.w 0x%(old_from)X,6(%%a0)
    jsr 0x%(draw)X
    bra 22f
21: move.w 0x%(first)X,%%d1             | none: just the clearing (the loop would read an entry anyway)
    lea 0x%(before_desc)X+8,%%a0
    bsr 70f
| what's after them: the game's own pass, after the heroes' HERO_ROOM
22: move.w 0x%(front)X+6,0x%(limit)X(%%a6)
    move.w 0x%(old_from)X,%%d1
    addi.w #%(hero_room)d,%%d1
    move.w 0x%(end)X,%%d0
    move.w %%d0,0x%(end_word)X(%%a6)
    move.w 0x%(he)X,%%d2
    lea 0x%(front)X+8,%%a0
    movem.l (%%sp)+,%%d3-%%d7/%%a1/%%a3-%%a5
    cmp.w %%d0,%%d2
    bcc 23f
    addq.w #2,%%d2
    move.l %%a0,0x%(prev)X(%%a6)
    lea 0x3C0002,%%a2
    rts
23: addq.l #4,%%sp                      | none: just the clearing, then out of the drawing routine
70: move.l %%a0,0x%(prev)X(%%a6)        | (a0: the end-last-frame word)
    lea 0x3C0002,%%a2
    move.w #1,2(%%a2)
    jmp 0x%(group_end)X
| is entry d4 a hero being drawn? Z set if so (d5 used)
80: move.w (%%a1,%%d4.w),%%d5
    cmpi.w #0x%(h1)X,%%d5
    beq 81f
    cmpi.w #0x%(h2)X,%%d5
    bne 82f
81: tst.b 0x28(%%a6,%%d5.w)
    beq 82f
    moveq #0,%%d5
    rts
82: moveq #1,%%d5
99: rts
""" % {"before": before, "front": FRONT, "list": LIST, "h1": HEROES[0], "h2": HEROES[1],
       "hero_room": HERO_ROOM, "hero_desc": HERO_DESC, "before_desc": BEFORE_DESC, "old_from": OLD_FROM, "hs": HS, "he": HE,
       "start": START, "end": END, "first": FIRST, "margin": MARGIN, "ceiling": CEILING, "draw": DRAW_GROUP,
       "group_end": GROUP_END, "limit": 662, "prev": 668, "end_word": 658},
        why="the front group drawn heroes first: their sprites written in the vblank")
    rom.write(GROUP_START + 2, code.to_bytes(4, "big"), expect=before.to_bytes(4, "big"),
              why="the front group starting: the heroes drawn first")
