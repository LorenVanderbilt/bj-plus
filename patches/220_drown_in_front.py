NAME = "drown-in-front"
DESCRIPTION = "Drowning: the hero sinks into the water in front of it (the water line swallows him) instead of behind the waterfall; lava swallows him too"

# Falling into a water pit (e.g. the first gap in Jungle 1, a waterfall) the game hides the hero object and
# spawns a sinking hero (object code 0x3DE90: his sprite y goes down 1 px every 2 frames) and a splash (0x3DEC4).
# Both get object slots in the "behind" draw group: the game draws objects in two groups, each a run of the
# object list at 0x100500 with a descriptor (list start / end offsets, first sprite, sprite limit, sprites used):
# 0x1002E0 = the front group (sprites from 133: enemies, items ...), 0x1002F0 = the behind group (sprites
# 45-99). The level's front layer (ground, cliffs, the waterfall: full-height sprite strips from sprite
# word 0x100246, 100 here) sits between them, so the whole sink happened behind the water - and the splash
# the game draws was hidden too.
# Now, after the frame's objects are drawn (the gameplay loop's `jsr 0xA3A0` at 0x1180A, the behind group),
# the sinking hero and the splash are drawn once more with the game's drawing routine, after the front
# group's sprites - in front of the front layer. Then, over the sinking hero, "cover" sprites: copies of the
# front layer's strips across his width, from a water line down (whole tile rows of the strip, so they sit
# exactly on the layer's own pixels, animation attributes and all). The cover is invisible - the same water
# over the same water - except that it hides the hero below the line. The line is WATER_LINE px below where
# the sinking hero's sprites started (kept per sinking object while it lasts), rounded down to the strip's
# tile row. The front group's "sprites used" count is raised past ours, so its next frame hides them.
# Lava: touching it is instant death - a burn hop (state 3), then state 33, in which the hero (the ordinary hero
# object, in the front group, so in front of the lava) hops up and falls off the bottom of the screen. The
# drawing loop's hooks note which sprites a hero in state 33 got this frame (GROUP_START: each group's first
# sprite; OBJECT_DONE: after each object), and the same cover goes over them from LAVA_LINE px below where he
# was when the state began - the lava surface swallows him.
# Beside a wall or cliff (in the same layer as the liquid): the cover copies only tiles in the liquid's palettes
# (those under his middle, from the line down; others become a blank tile), and he is eased sideways (2 px a
# frame) until his sprites are all over the liquid at the line - the big art is wider than the original's and
# would otherwise hang over the wall and look as if it fell into it.
DRAW_BEHIND_CALL = 0x1180A   # jsr 0xA3A0 - the behind group (after the front group, 0x11804)
DRAW_BEHIND = 0xA3A0
DROWN_CODE = 0x3DE90         # the sinking hero
SPLASH_CODE = 0x3DEC4
WATER_LINE = 40              # px below the sinking hero's first sprite y
COVER_ROWS = 5               # tile rows of cover under the line (80 px: more than the hero's height)
LAVA_LINE = 40               # the same for a hero burning in lava (state 33): px below his first y in that state
FRAME = 0x100207
RAM = 0x10EB80               # +0 2 entries (object offset word, first y word), +8 a byte: entries seen this frame,
                             # +10 / +12 words: cover's arguments, +14 word: the drawing loop's next sprite,
                             # +16 / +22 player 1 / 2 in lava: first sprite, end sprite (words), frame (byte),
                             # +24 / +26 words and +28 4 bytes: cover's workspace (the liquid's palettes), +34..+45
                             # more of it: the entry (x2), each entry's sideways shift (+36 / +38), the liquid's
                             # ends (+40 / +42), the hero's first sprite (+44)
GROUP_START = 0xA3BC         # lea 0x3C0002,a2 - the drawing loop, starting a group (d1 = its first sprite)
OBJECT_DONE = 0xA3FE         # move.w 656(a6),d0 ; dbf d0,0xA3D8 - the drawing loop, after each object


def apply(rom):
    src = r"""
post:
    jsr DRAW_BEHIND
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    lea 0x100000,%a6
    clr.b RAM+8
    move.w 0x2E8(%a6),%d1            | the next free sprite after the front group
    move.w 0x2E6(%a6),0x296(%a6)     | its sprite limit, for the drawing routine
    move.w 0x2F0(%a6),%d7            | the behind group's list entries
1:  cmp.w 0x2F2(%a6),%d7
    bhi 9f
    lea 0x500(%a6),%a0
    move.w (%a0,%d7.w),%d3
    lea (%a6,%d3.w),%a0
    tst.b 0x28(%a0)                  | (not drawn)
    beq 8f
    move.l 4(%a0),%d0
    cmp.l #DROWN_CODE,%d0
    beq 2f
    cmp.l #SPLASH_CODE,%d0
    bne 8f
2:  move.w %d1,%d0                   | room for it and a cover?
    add.w #16,%d0
    cmp.w 0x2E6(%a6),%d0
    bcc 9f
    move.w %d7,-(%sp)
    move.l %a0,-(%sp)
    move.w %d1,-(%sp)
    bsr draw_obj
    move.w (%sp)+,%d6                | d6..d1-1: its sprites
    move.l (%sp)+,%a0
    cmp.l #DROWN_CODE,4(%a0)
    bne 7f
    move.w %d1,RAM+10                | (its sprites end here)
    move.w #WATER_LINE,RAM+12
    bsr cover
7:  move.w (%sp)+,%d7
8:  addq.w #2,%d7
    bra 1b
9:  lea RAM+16,%a1                   | a hero burning in lava (state 33), drawn this frame: the lava's cover
    lea 0x104000,%a0
    moveq #1,%d7
20: move.b FRAME,%d0
    cmp.b 4(%a1),%d0
    bne 21f
    move.w %d1,%d0
    add.w #8,%d0
    cmp.w 0x2E6(%a6),%d0
    bcc 21f
    movem.l %d7/%a0-%a1,-(%sp)
    move.w (%a1),%d6
    move.w 2(%a1),RAM+10
    move.w #LAVA_LINE,RAM+12
    bsr cover
    movem.l (%sp)+,%d7/%a0-%a1
21: lea 6(%a1),%a1
    lea 0x80(%a0),%a0
    dbf %d7,20b
    move.w %d1,0x2E8(%a6)            | (the front group hides them next frame unless drawn again)
    lea RAM,%a0                      | forget sinking objects that are gone
    btst #0,RAM+8
    bne 3f
    clr.l (%a0)
    clr.w RAM+36
3:  btst #1,RAM+8
    bne 4f
    clr.l 4(%a0)
    clr.w RAM+38
4:  movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

| the drawing loop, at the start of each group (in place of `lea 0x3C0002,a2` at 0xA3BC): d1 = its first sprite
grp_start:
    move.w %d1,RAM+14
    lea 0x3C0002,%a2
    rts

| the drawing loop, after each object (0xA3FE, in place of `move.w 656(a6),d0 ; dbf d0,0xA3D8`): d1 = the next
| free sprite. A hero in state 33 (burning in lava) has its sprites noted: RAM+14 (where it started) to d1.
after_obj:
    movem.l %d0/%a0-%a1,-(%sp)
    move.w -2(%a4),%d0
    lea RAM+16,%a1
    cmp.w #0x4000,%d0
    beq 1f
    lea RAM+22,%a1
    cmp.w #0x4080,%d0
    bne 2f
1:  lea (%a6,%d0.w),%a0
    cmp.b #33,0x68(%a0)
    bne 2f
    move.w RAM+14,(%a1)
    move.w %d1,2(%a1)
    move.b FRAME,4(%a1)
2:  move.w %d1,RAM+14
    movem.l (%sp)+,%d0/%a0-%a1
    move.w 656(%a6),%d0
    dbf %d0,3f
    jmp 0xA406
3:  jmp 0xA3D8

| a0 = object, d1 = first sprite: the game's drawing routine (as its loop at 0xA3D8 calls it) -> d1 = next free
draw_obj:
    lea 0x3C0002,%a2
    move.w #1,2(%a2)
    lea 0x60772,%a3
    move.b 0x28(%a0),%d2
    pea 9f
    addq.b #2,%d2
    bcc 1f
    bne 2f
    jmp 0xB244
1:  jmp 0xA426
2:  jmp 0xB0A0
9:  rts

| VRAM word at d0 -> d0 (reading doesn't move the address)
vread:
    move.w %d0,0x3C0000
    move.w 0x3C0002,%d0
    rts

| a0 = the sinking hero, d6..RAM+10 - 1 its sprites, RAM+12 the line's distance below their first y: cover
| sprites from d1 on (d1 moves past them)
cover:
    move.w %sr,-(%sp)
    or.w #0x0700,%sr                 | nothing else may move the VRAM address meanwhile
    move.w %d6,RAM+44                | (his first sprite)
    move.w %d6,%d0                   | its first sprite's y
    add.w #0x8200,%d0
    bsr vread
    lsr.w #7,%d0
    neg.w %d0
    add.w #496,%d0
    and.w #511,%d0
    move.w %d0,%d5
    move.l %a0,%d0                   | its entry: the first y seen
    sub.l #0x100000,%d0
    lea RAM,%a1
    moveq #0,%d2
1:  cmp.w (%a1),%d0
    beq 3f
    addq.l #4,%a1
    addq.w #1,%d2
    cmp.w #2,%d2
    bne 1b
    lea RAM,%a1                      | new: a free entry
    moveq #0,%d2
2:  tst.w (%a1)
    beq 4f
    addq.l #4,%a1
    addq.w #1,%d2
    cmp.w #2,%d2
    bne 2b
    bra 90f                          | (no room: no cover)
4:  move.w %d0,(%a1)
    move.w %d5,2(%a1)
3:  bset %d2,RAM+8
    add.w %d2,%d2
    move.w %d2,RAM+34                | (his entry's shift: RAM+36 + this)
    move.w 2(%a1),%d5
    add.w RAM+12,%d5                 | d5 = the water line (y)
    and.w #511,%d5
    | its x range: d3..d4
    move.w #0x7FFF,%d3
    moveq #0,%d4
    move.w %d6,%d2
5:  cmp.w RAM+10,%d2
    bcc 6f
    move.w %d2,%d0
    add.w #0x8200,%d0
    bsr vread
    btst #6,%d0
    bne 51f
    move.w %d2,%d0
    add.w #0x8400,%d0
    bsr vread
    lsr.w #7,%d0
    move.w %d0,%d7
    bra 52f
51: add.w #16,%d7
52: cmp.w %d3,%d7
    bcc 53f
    move.w %d7,%d3
53: move.w %d7,%d0
    add.w #16,%d0
    cmp.w %d4,%d0
    bls 54f
    move.w %d0,%d4
54: addq.w #1,%d2
    bra 5b
6:  | pass 1: the liquid's palettes - those of the strip under the hero's middle, from the line down (a wall or
    | cliff beside him is in the same layer, but in other palettes: the cover leaves those out)
    move.w %d1,RAM+24
    move.l #-1,RAM+28                | up to 4 palettes (0xFF = none)
    move.w %d3,%d0
    add.w %d4,%d0
    lsr.w #1,%d0
    move.w %d0,RAM+26                | his middle x
    move.w 0x246(%a6),%d2
    moveq #0,%d6
    moveq #0,%d7
30: cmp.w 0x2E4(%a6),%d2
    bcc 39f
    move.w %d2,%d0
    add.w #0x8200,%d0
    bsr vread
    btst #6,%d0
    bne 31f
    move.w %d0,%a4
    lsr.w #7,%d0
    neg.w %d0
    add.w #496,%d0
    and.w #511,%d0
    move.w %d0,%d6
    move.w %d2,%d0
    add.w #0x8400,%d0
    bsr vread
    lsr.w #7,%d0
    move.w %d0,%d7
    bra 32f
31: add.w #16,%d7
    and.w #511,%d7
32: move.w %a4,%d0
    and.w #63,%d0
    cmp.w #32,%d0
    bcs 38f
    move.w RAM+26,%d0                | under his middle?
    sub.w %d7,%d0
    cmp.w #16,%d0
    bcc 38f
    move.w %d5,%d0                   | r0, as below
    sub.w %d6,%d0
    and.w #511,%d0
    add.w #15,%d0
    lsr.w #4,%d0
    cmp.w #32,%d0
    bcc 39f
    move.w %d2,%a5                   | its rows' palettes: a5 = the tile word address, a3 = rows left
    move.w %d2,%d1
    move.w %d0,-(%sp)
    lsl.w #6,%d1
    add.w %d0,%d1
    add.w %d0,%d1
    addq.w #1,%d1                    | (the attribute word)
    moveq #32,%d0
    sub.w (%sp)+,%d0
    cmp.w #COVER_ROWS,%d0
    bls 33f
    moveq #COVER_ROWS,%d0
33: move.w %d0,%a3
34: move.w %d1,%d0
    bsr vread
    lsr.w #8,%d0
    lea RAM+28,%a0
    moveq #3,%d2
35: cmp.b (%a0),%d0
    beq 37f
    cmp.b #0xFF,(%a0)
    bne 36f
    move.b %d0,(%a0)
    bra 37f
36: addq.l #1,%a0
    dbf %d2,35b
37: addq.w #2,%d1
    subq.w #1,%a3
    move.w %a3,%d0
    bne 34b
    move.w %a5,%d2
    bra 39f
38: addq.w #1,%d2
    bra 30b
39: move.w RAM+24,%d1                | (d1 was borrowed)
    | pass 1b: where the liquid ends either side of his middle at the line: the nearest strips (within 64 px)
    | whose tile at the line isn't in the liquid's palettes -> RAM+40 = left end, RAM+42 = right end
    move.w RAM+26,%d0
    sub.w #64,%d0
    move.w %d0,RAM+40
    add.w #128,%d0
    move.w %d0,RAM+42
    move.w 0x246(%a6),%d2
    moveq #0,%d6
    moveq #0,%d7
40: cmp.w 0x2E4(%a6),%d2
    bcc 49f
    move.w %d2,%d0
    add.w #0x8200,%d0
    bsr vread
    btst #6,%d0
    bne 41f
    move.w %d0,%a4
    lsr.w #7,%d0
    neg.w %d0
    add.w #496,%d0
    and.w #511,%d0
    move.w %d0,%d6
    move.w %d2,%d0
    add.w #0x8400,%d0
    bsr vread
    lsr.w #7,%d0
    move.w %d0,%d7
    bra 42f
41: add.w #16,%d7
    and.w #511,%d7
42: move.w %a4,%d0
    and.w #63,%d0
    cmp.w #32,%d0
    bcs 48f
    move.w %d7,%d0                   | near him? (-80 < x - middle < 64)
    sub.w RAM+26,%d0
    cmp.w #-80,%d0
    ble 48f
    cmp.w #64,%d0
    bge 48f
    move.w %d5,%d0                   | its tile at the line
    sub.w %d6,%d0
    and.w #511,%d0
    add.w #15,%d0
    lsr.w #4,%d0
    cmp.w #32,%d0
    bcc 48f
    add.w %d0,%d0
    move.w %d2,%a5
    move.w %d2,-(%sp)
    lsl.w #6,%d2
    add.w %d2,%d0
    addq.w #1,%d0
    bsr vread
    move.w (%sp)+,%d2
    lsr.w #8,%d0
    lea RAM+28,%a0
    cmp.b (%a0)+,%d0
    beq 48f
    cmp.b (%a0)+,%d0
    beq 48f
    cmp.b (%a0)+,%d0
    beq 48f
    cmp.b (%a0)+,%d0
    beq 48f
    move.w %d7,%d0                   | not liquid: left of his middle -> the left end, right of it -> the right end
    add.w #16,%d0
    cmp.w RAM+26,%d0
    bgt 43f
    cmp.w RAM+40,%d0
    ble 48f
    move.w %d0,RAM+40
    bra 48f
43: cmp.w RAM+26,%d7
    ble 48f
    cmp.w RAM+42,%d7
    bge 48f
    move.w %d7,RAM+42
48: addq.w #1,%d2
    bra 40b
49: | the shift that keeps him over the liquid (not over a wall or cliff beside it), eased 2 px a frame
    move.w RAM+40,%d0
    sub.w %d3,%d0
    bgt 50f
    move.w %d4,%d0
    sub.w RAM+42,%d0
    ble 51f
    neg.w %d0
    bra 50f
51: moveq #0,%d0
50: lea RAM+36,%a0
    add.w RAM+34,%a0
    move.w (%a0),%d2
    cmp.w %d2,%d0
    beq 53f
    blt 52f
    addq.w #2,%d2
    cmp.w %d2,%d0
    bge 53f
    move.w %d0,%d2
    bra 53f
52: subq.w #2,%d2
    cmp.w %d2,%d0
    ble 53f
    move.w %d0,%d2
53: move.w %d2,(%a0)                 | d2 = the shift now: move his sprites (each chain's x) by it
    add.w %d2,%d3
    add.w %d2,%d4
    tst.w %d2
    beq 59f
    move.w %d2,%a2
    move.w RAM+44,%d2
54: cmp.w RAM+10,%d2
    bcc 59f
    move.w %d2,%d0
    add.w #0x8200,%d0
    bsr vread
    btst #6,%d0
    bne 55f
    move.w %d2,%d0
    add.w #0x8400,%d0
    bsr vread
    lsr.w #7,%d0
    add.w %a2,%d0
    and.w #511,%d0
    lsl.w #7,%d0
    move.w %d2,%d6
    add.w #0x8400,%d6
    move.w %d6,0x3C0000
    move.w %d0,0x3C0002
55: addq.w #1,%d2
    bra 54b
59:
    | pass 2: the front layer's strips (from sprite word 0x246 up to the front group's first sprite)
    move.w 0x246(%a6),%d2
    moveq #0,%d6                     | (strip y)
    moveq #0,%d7                     | (strip x)
    moveq #0,%d0
10: cmp.w 0x2E4(%a6),%d2
    bcc 90f
    move.w %d2,%d0
    add.w #0x8200,%d0
    bsr vread
    btst #6,%d0
    bne 11f
    move.w %d0,%a4                   | a chain's first sprite: its y, size, x
    lsr.w #7,%d0
    neg.w %d0
    add.w #496,%d0
    and.w #511,%d0
    move.w %d0,%d6
    move.w %d2,%d0
    add.w #0x8400,%d0
    bsr vread
    lsr.w #7,%d0
    move.w %d0,%d7
    bra 12f
11: add.w #16,%d7
    and.w #511,%d7
12: move.w %a4,%d0                   | a full-height strip?
    and.w #63,%d0
    cmp.w #32,%d0
    bcs 19f
    move.w %d7,%d0                   | across the hero? (x + 16 > d3 and x < d4)
    add.w #16,%d0
    cmp.w %d3,%d0
    bls 19f
    cmp.w %d4,%d7
    bcc 19f
    move.w %d5,%d0                   | the first row at or below the line: r0 = ((line - y) & 511 + 15) / 16
    sub.w %d6,%d0
    and.w #511,%d0
    add.w #15,%d0
    lsr.w #4,%d0
    cmp.w #32,%d0
    bcc 19f
    movem.l %d2-%d7,-(%sp)
    move.w %d0,%d3                   | d3 = r0
    moveq #32,%d4
    sub.w %d0,%d4
    cmp.w #COVER_ROWS,%d4
    bls 13f
    moveq #COVER_ROWS,%d4            | d4 = rows
13: | tiles: strip rows r0.. -> cover rows 0..
    move.w %d4,%d5
    subq.w #1,%d5
    move.w %d2,%d0                   | the strip's tile words start at sprite * 64 + 2 * r0
    lsl.w #6,%d0
    add.w %d3,%d0
    add.w %d3,%d0
    move.w %d0,%a5
    move.w %d1,%d0
    lsl.w #6,%d0
    move.w %d0,%a3
14: move.w %a5,%d0
    bsr vread
    move.w %d0,%a2
    move.w %a5,%d0
    addq.w #1,%d0
    bsr vread
    move.w %d0,%a1
    lsr.w #8,%d0                     | the liquid's palette? else a blank tile (he stays in front of it)
    lea RAM+28,%a0
    cmp.b (%a0)+,%d0
    beq 15f
    cmp.b (%a0)+,%d0
    beq 15f
    cmp.b (%a0)+,%d0
    beq 15f
    cmp.b (%a0)+,%d0
    beq 15f
    move.w #BLANK_TILE,%a2
    move.w #0,%a1
15: move.w %a3,0x3C0000
    move.w %a2,0x3C0002              | (the modulo is 1: tile, then attributes)
    move.w %a1,0x3C0002
    addq.w #2,%a5
    addq.w #2,%a3
    dbf %d5,14b
    move.w %d2,%d0                   | its zoom
    add.w #0x8000,%d0
    bsr vread
    move.w %d0,%d5
    move.w %d1,%d0
    add.w #0x8000,%d0
    move.w %d0,0x3C0000
    move.w %d5,0x3C0002
    lsl.w #4,%d3                     | y: the strip's + 16 * r0
    add.w %d6,%d3
    move.w #496,%d0
    sub.w %d3,%d0
    and.w #511,%d0
    lsl.w #7,%d0
    or.w %d4,%d0
    move.w %d1,%d5
    add.w #0x8200,%d5
    move.w %d5,0x3C0000
    move.w %d0,0x3C0002
    move.w %d7,%d0                   | x
    lsl.w #7,%d0
    move.w %d1,%d5
    add.w #0x8400,%d5
    move.w %d5,0x3C0000
    move.w %d0,0x3C0002
    movem.l (%sp)+,%d2-%d7
    addq.w #1,%d1
    move.w %d1,%d0
    cmp.w 0x2E6(%a6),%d0
    bcc 90f
19: addq.w #1,%d2
    bra 10b
90: move.w (%sp)+,%sr
    rts
"""
    consts = {"DRAW_BEHIND": "0x%X" % DRAW_BEHIND, "DROWN_CODE": "0x%X" % DROWN_CODE,
              "SPLASH_CODE": "0x%X" % SPLASH_CODE, "WATER_LINE": str(WATER_LINE), "COVER_ROWS": str(COVER_ROWS),
              "RAM": "0x%X" % RAM, "LAVA_LINE": str(LAVA_LINE), "FRAME": "0x%X" % FRAME,
              "BLANK_TILE": "0x%X" % rom.add_sprite_tile([[0] * 16 for _ in range(16)], why="drowning: a blank tile")}
    for k in sorted(consts, key=len, reverse=True):
        src = src.replace(k, consts[k])
    base = rom.place_code("    bra.w post\n    bra.w grp_start\n    bra.w after_obj\n" + src,
                          why="drowning: the sinking hero and splash in front of the water, a water line; lava too")
    post, grp_start, after_obj = base, base + 4, base + 8
    rom.write(GROUP_START, bytes.fromhex("4EB9") + grp_start.to_bytes(4, "big"),
              expect=bytes.fromhex("45F9003C0002"), why="drawing loop: note each group's first sprite")
    rom.write(OBJECT_DONE, bytes.fromhex("4EF9") + after_obj.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("302E029051C8FFD4"), why="drawing loop: note a burning hero's sprites")
    rom.write(DRAW_BEHIND_CALL, bytes.fromhex("4EB9") + post.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90000A3A0"), why="after the objects: draw a drowning hero in front of the water")
