NAME = "boomerang-feel"
DESCRIPTION = "Boomerang: each level's reach, speed and size retuned; level 2 throws two out at once, level 3 three - every third throw bigger"

# The boomerang (level 1-3 at player block +0x2B) flies one turn of a loop around a point LOOP[level] ahead of Blue
# (table at 0x4793E; radius LOOP + 0x800). Its angle steps 0x0A00 a frame, a 26-frame trip, and it's drawn as
# animation 197 + level. acorn-bomb (480) lets a second one be thrown with a new press of A during the throw, when
# its second_boomerang check (the code's fifth entry, SECOND_ENTRY) allows it. That check is filled in here.
#
# Tuning per level, found with tools/probes/boomerang_tune.lua on 2026-10-25 (reach ahead of Blue, frames out and
# back, size, how many out at once):
#   1: 60 px, 35 frames, 90%, one
#   2: 65 px, 40 frames, 75%, two
#   3: as 2 but three, with every third throw full size (BIG)
#
# The throw (SPAWN) takes the player's own slot, or if that's taken a slot in the general pool (POOL, also used by
# enemy shots) while fewer than EXTRA[level] of theirs are out. 480's check gives the same answer. Each boomerang gets
# its level's drawing, size and angle step as it starts (LOOK_SITES), keeping its direction. The reach comes from the
# loop table: reach = LOOP / 128 + (LOOP + 0x800) / 256 px.
#
# It also always comes back to Blue. Over the second half of the trip (PLACE_CALLS, after its place on the loop is
# set) its position is blended from the loop's toward the thrower's, reaching him at the end. A throw from a jump
# comes back to Blue wherever he's landed.
REACH = {1: 60, 2: 65, 3: 65}
TRIP = {1: 35, 2: 40, 3: 40}
SIZE = {1: 90, 2: 75, 3: 75}
EXTRA = {1: 0, 2: 1, 3: 2}         # boomerangs allowed in the pool, besides the player's own slot
BIG = (199, 0xFF)                  # every third level 3 throw: level 2's animation at full size
THROWS = 0x10ECF8                  # spare RAM: each player's level 3 throw count, 0-2
LOOP = 0x4793E
PLACE_CALLS = (0x478DC, 0x47926)  # jsr 0x4D446 each frame: its place on the loop (+0 y, +2 x) at its angle
PLACE = 0x4D446
TRIP_DONE = 0x78                   # +0x78: angle travelled so far; a full turn ends the trip
HEROES = 0x4000                    # player 1's hero object, from 0x100000; player 2's is 0x80 on
LOOK_SITES = (0x478AA, 0x478F4)    # move.w #197,d0 ; add.b 0x2B(a4),d0 (a5 = boomerang, a4 = player)
SPAWN = 0x475BC                    # move.b 0x7E(a5),d0 ; bne.s 0x47610 (player 2)
SPAWN_P1, SPAWN_P2 = 0x475C2, 0x47610
SPAWN_FAIL = 0x47590
ACORN_SPAWN = 0x47662              # acorn-bomb's jmp <its code>; the fifth entry (+16) is second_boomerang
SECOND_ENTRY = 16
OWN_SLOT = (0x4100, 0x4180)
BLOCK = (0x7000, 0x7400)
LEVEL = 0x2B
POOL = (0x4480, 0x5B00)
BOOMERANG_CODE = (0x4770A, 0x47946)
OWNER = 0x7E


def apply(rom):
    for lv, r in REACH.items():
        rom.write(LOOP + 2 * lv, (round((r - 8) * 256 / 3)).to_bytes(2, "big"), why="boomerang: level %d's reach" % lv)
    blocks = [", ".join("0x%02X" % b for b in rom.data[at + 10:at + 36]) for at in (SPAWN_P1, SPAWN_P2)]
    first, last = POOL
    zoom = {lv: min(255, round(SIZE[lv] * 255 / 100)) for lv in SIZE}
    step = {lv: round(65536 / TRIP[lv]) for lv in TRIP}
    code = rom.place_code(r"""
    bra.w spawn
    bra.w look
    bra.w may_more
    bra.w place

| d1 = how many of player d0's boomerangs are in the pool; a1 kept
pooled:
    movem.l %%d2/%%a0,-(%%sp)
    moveq #0,%%d1
    lea 0x%(first)X(%%a6),%%a0
    move.w #(0x%(last)X-0x%(first)X)/0x80,%%d2
1:  tst.b 0x28(%%a0)
    beq 2f
    cmp.b %(owner)d(%%a0),%%d0
    bne 2f
    cmpi.l #0x%(code_lo)X,4(%%a0)
    bcs 2f
    cmpi.l #0x%(code_hi)X,4(%%a0)
    bcc 2f
    addq.w #1,%%d1
2:  lea 0x80(%%a0),%%a0
    dbf %%d2,1b
    movem.l (%%sp)+,%%d2/%%a0
    rts

| Z set if player d0 may throw another boomerang into the pool: their own slot is taken and they have fewer in the
| pool than their level allows
may_more:
    movem.l %%d0-%%d2/%%a0-%%a1,-(%%sp)
    lea 0x%(own1)X(%%a6),%%a0
    lea 0x%(block1)X(%%a6),%%a1
    tst.b %%d0
    beq 3f
    lea 0x%(own2)X(%%a6),%%a0
    lea 0x%(block2)X(%%a6),%%a1
3:  tst.b 0x28(%%a0)
    beq 5f
    moveq #0,%%d2
    move.b %(level)d(%%a1),%%d2
    lea extra(%%pc),%%a0
    move.b (%%a0,%%d2.w),%%d2
    lea 0x%(own1)X(%%a6),%%a0
    tst.b %%d0
    beq 4f
    lea 0x%(own2)X(%%a6),%%a0
4:
    bsr pooled
    cmp.w %%d2,%%d1
    bcc 5f
    movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    ori.b #4,%%ccr
    rts
5:  movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    andi.b #0xFB,%%ccr
    rts
extra:
    .byte %(extra)s
    .even

| each frame, after its place on the loop is set: over the second half, blend toward the thrower,
| loop place + (thrower - loop place) * (trip - half) / half
place:
    jsr 0x%(place_fn)X
    movem.l %%d0-%%d2/%%a0,-(%%sp)
    move.w %(done)d(%%a5),%%d2
    sub.w #0x8000,%%d2
    bcs 19f                             | first half: stay on the loop
    lea 0x%(heroes)X(%%a6),%%a0
    tst.b %(owner)d(%%a5)
    beq 18f
    lea 0x80(%%a0),%%a0
18: moveq #1,%%d1
20: move.w (%%a0),%%d0                  | y, then x
    sub.w (%%a5),%%d0
    muls %%d2,%%d0
    add.l %%d0,%%d0
    swap %%d0
    add.w %%d0,(%%a5)
    addq.l #2,%%a0
    addq.l #2,%%a5
    dbra %%d1,20b
    subq.l #4,%%a5
19: movem.l (%%sp)+,%%d0-%%d2/%%a0
    rts

| the throw: the player's own slot, or a pool slot while more are allowed
spawn:
    move.b %(owner)d(%%a5),%%d0
    bne 7f
    tst.b 0x%(own1)X+0x28(%%a6)
    beq 6f
    bsr may_more
    beq pool1
6:  jmp 0x%(p1)X
7:  tst.b 0x%(own2)X+0x28(%%a6)
    beq 8f
    bsr may_more
    beq pool2
8:  jmp 0x%(p2)X
pool1:
    jsr 0xA158
    .word 0x%(first)X, (0x%(last)X-0x%(first)X)/0x80
    .byte %(block_p1)s
    beq 9f
    jmp 0x%(fail)X
9:  moveq #0,%%d1
    bra 11f
pool2:
    jsr 0xA158
    .word 0x%(first)X, (0x%(last)X-0x%(first)X)/0x80
    .byte %(block_p2)s
    beq 10f
    jmp 0x%(fail)X
10: moveq #1,%%d1
11: move.b %%d1,-(%%sp)                 | as the original does once it has a slot
    jsr 0x10098
    jsr 0x5E05E
    move.l 0(%%a5),0(%%a1)
    clr.w 106(%%a1)
    clr.l 72(%%a1)
    move.b (%%sp)+,%(owner)d(%%a1)
    moveq #0,%%d0
    rts

| as a boomerang starts: its level's angle step (keeping its direction), drawing and size, with every third level 3
| throw the big one; d0 = the animation
look:
    movem.l %%d1-%%d2/%%a0,-(%%sp)
    moveq #0,%%d2
    move.b %(level)d(%%a4),%%d2
    add.w %%d2,%%d2
    lea steps(%%pc),%%a0
    move.w (%%a0,%%d2.w),%%d1
    tst.w 0x3E(%%a5)
    bpl 12f
    neg.w %%d1
12: move.w %%d1,0x3E(%%a5)
    lsr.w #1,%%d2
    cmpi.b #3,%%d2
    bne 13f
    moveq #0,%%d0                       | every third throw is the big one
    move.b %(owner)d(%%a5),%%d0
    lea 0x%(throws)X,%%a0
    add.w %%d0,%%a0
    addq.b #1,(%%a0)
    cmpi.b #3,(%%a0)
    bcs 13f
    clr.b (%%a0)
    move.b #%(big_zoom)d,0x26(%%a5)
    move.b #%(big_zoom)d,0x27(%%a5)
    move.w #%(big_anim)d,%%d0
    bra 15f
13: lea sizes(%%pc),%%a0
    move.b (%%a0,%%d2.w),%%d1
    move.b %%d1,0x26(%%a5)
    move.b %%d1,0x27(%%a5)
    cmpi.b #3,%%d2
    bne 14f
    moveq #2,%%d2                       | level 3 is drawn as level 2
14: move.w #197,%%d0
    add.w %%d2,%%d0
15: movem.l (%%sp)+,%%d1-%%d2/%%a0
    rts
steps:
    .word %(steps)s
sizes:
    .byte %(sizes)s
    .even
""" % {"owner": OWNER, "own1": OWN_SLOT[0], "own2": OWN_SLOT[1], "block1": BLOCK[0], "block2": BLOCK[1],
       "level": LEVEL, "p1": SPAWN_P1, "p2": SPAWN_P2, "first": first, "last": last, "fail": SPAWN_FAIL,
       "code_lo": BOOMERANG_CODE[0], "code_hi": BOOMERANG_CODE[1], "block_p1": blocks[0], "block_p2": blocks[1],
       "extra": ",".join(str(EXTRA.get(lv, 0)) for lv in range(4)),
       "steps": ",".join("0x%04X" % step.get(lv, 0x0A00) for lv in range(4)),
       "sizes": ",".join(str(zoom.get(lv, 255)) for lv in range(4)),
       "big_anim": BIG[0], "big_zoom": BIG[1], "throws": THROWS, "place_fn": PLACE, "done": TRIP_DONE, "heroes": HEROES},
        why="boomerang: each level's speed and size, two / three out at once")
    rom.write(SPAWN, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("102D007E664E"),
              why="boomerang: the throw - two out at level 2, three at level 3")
    for at in LOOK_SITES:
        rom.write(at, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex("303C00C5D02C002B"), why="boomerang: each level's speed, drawing and size")
    for at in PLACE_CALLS:
        rom.write(at + 2, (code + 12).to_bytes(4, "big"), expect=PLACE.to_bytes(4, "big"),
                  why="boomerang: back to the thrower over the trip's second half")
    assert rom.u16(ACORN_SPAWN) == 0x4EF9, "boomerang-feel: needs acorn-bomb"
    entry = rom.u32(ACORN_SPAWN + 2) + SECOND_ENTRY
    assert rom.u16(entry) == 0x6000, "boomerang-feel: acorn-bomb's second_boomerang entry not found"
    at = entry + 2 + rom.u16(entry + 2)
    rom.write(at, bytes.fromhex("4EF9") + (code + 8).to_bytes(4, "big"), expect=bytes.fromhex("023C00FB4E75"),
              why="acorn-bomb's quick second throw: the boomerang's count by level")
