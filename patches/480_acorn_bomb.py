NAME = "acorn-bomb"
DESCRIPTION = "Acorn bomb: levels 2 / 3 thrown further; level 3 keeps level 2's size but two can be out at once (thrown quickly - the boomerang's second too)"

# The acorn bomb (player block +0x2C: level 1-3 - weapon-switch calls it the boomerang) is an object in one fixed
# slot per player (0x104100 / 0x104180, the boomerang's too: the spawn 0x47662 asks 0xA158 for just that slot, so
# while one is out another can't be thrown). Thrown, it gets a speed by level from one of three tables (by the
# throw's direction: SPEEDS, (x, y) words for levels 0-3), its look from animation 200 + level (0x47A8E) and, when
# it goes off, 236 + level - 1 (0x47B22: level 3's the biggest, raised 0x800). Levels 2 and 3 threw alike.
#   * level 2 and 3 speeds x RANGE;
#   * level 3 looks like level 2 (thrown and going off);
#   * level 3: with the player's own slot taken, a second one goes in a free slot of the game's general pool
#     (POOL, as enemies' shots use) - only one there per player (an acorn of theirs already in the pool: no);
#   * level 3: the thrower's throw (THROWING's states, both weapons') no longer holds up the second - a new press of
#     A during it, with the acorn in hand and a second allowed, throws again at once (the acorn's attack); the same
#     for level 3's boomerang (the boomerang patch puts its second in the pool: BOOMERANG_ATTACKS, its level / code).
SPEEDS = (0x47BAC, 0x47BBC, 0x47BCC)
RANGE = 1.15
LOOK_SITE = 0x47A8E          # move.w #200,d0 ; add.b 0x2C(a4),d0
GONE_LEVEL3 = 0x47B2E        # move.w #238,d0 (level 3's going off) -> level 2's (0x47B48)
GONE_LEVEL2 = 0x47B48
SPAWN = 0x47662              # move.b 0x7E(a5),d0 ; bne 0x476B8 (player 2's)
SPAWN_P1, SPAWN_P2 = 0x47668, 0x476B8
SPAWN_FAIL = 0x47590
THROWING = ((0x3DADC, 0x3DAA8), (0x3DB7A, 0x3DB4E))   # the throw's state (jsr 0x3BF0A first, each frame; a5 =
                                                      # the thrower) and the acorn's attack: on the ground, in the air
THROWING_FIRST = 0x3BF0A
OWN_SLOT = (0x4100, 0x4180)  # (offsets from 0x100000)
BLOCK = (0x7000, 0x7400)     # each player's block
LEVEL = 0x2C
POOL = (0x4480, 0x5B00)      # (first slot, last)
ACORN_CODE = (0x47946, 0x47BAC)   # its routines: an object running one of them (+4) is an acorn
OWNER = 0x7E
BOOMERANG_ATTACKS = (0x3DA96, 0x3DB3C)   # its attack: on the ground, in the air
BOOMERANG_LEVEL, BOOMERANG_CODE = 0x2B, (0x4770A, 0x47946)
BUTTONS = (0x10FD96, 0x10FD9C)    # BIOS: each player's buttons now (bit 4: A)
FRAME = 0x100207             # the game's frame counter (a byte)
SEEN = 0x10E9F8              # per player: the frame the throw was last seen, A down then (bytes; spare RAM) - a press
                             # counts only between two frames of the same throw (the one that starts it doesn't)


SECOND = r"""| Z set if player d0 (0 / 1) may throw a second acorn now: level 3, their own slot taken, none of theirs in the pool
second:
    movem.l %%d0-%%d1/%%a0-%%a1,-(%%sp)
    lea 0x%(own1)X(%%a6),%%a0
    lea 0x%(block1)X(%%a6),%%a1
    tst.b %%d0
    beq 3f
    lea 0x%(own2)X(%%a6),%%a0
    lea 0x%(block2)X(%%a6),%%a1
3:  tst.b 0x28(%%a0)
    beq 6f
    cmpi.b #3,%(level)d(%%a1)
    bne 6f
    lea 0x%(first)X(%%a6),%%a0
    move.w #(0x%(last)X-0x%(first)X)/0x80,%%d1
4:  tst.b 0x28(%%a0)
    beq 5f
    cmp.b %(owner)d(%%a0),%%d0
    bne 5f
    cmpi.l #0x%(code_lo)X,4(%%a0)
    bcs 5f
    cmpi.l #0x%(code_hi)X,4(%%a0)
    bcs 6f
5:  lea 0x80(%%a0),%%a0
    dbf %%d1,4b
    movem.l (%%sp)+,%%d0-%%d1/%%a0-%%a1
    ori.b #4,%%ccr
    rts
6:  movem.l (%%sp)+,%%d0-%%d1/%%a0-%%a1
    andi.b #0xFB,%%ccr
    rts

"""


def apply(rom):
    for t in SPEEDS:
        x, y = (rom.u16(t + 8 + i) for i in (0, 2))
        new = b"".join((round(v * RANGE)).to_bytes(2, "big") for v in (x, y))
        rom.write(t + 8, new + new, why="acorn bomb: level 2 / 3 thrown further")
    # the pool spawn: the original's own inline block (the 0xA158 call's data after its slot range), per player
    blocks = []
    for at in (SPAWN_P1, SPAWN_P2):
        data = bytes(rom.data[at + 6 + 4: at + 6 + 4 + 26])
        blocks.append(", ".join("0x%02X" % b for b in data))
    first, last = POOL
    seconds = ""
    for name, level, (lo, hi) in (("second", LEVEL, ACORN_CODE), ("second_boomerang", BOOMERANG_LEVEL, BOOMERANG_CODE)):
        seconds += (SECOND.replace("second:", name + ":") % {
            "owner": OWNER, "own1": OWN_SLOT[0], "own2": OWN_SLOT[1], "block1": BLOCK[0], "block2": BLOCK[1],
            "level": level, "first": first, "last": last, "code_lo": lo, "code_hi": hi})
    code = rom.place_code(r"""
    bra.w spawn
    bra.w look
    bra.w throwing_ground
    bra.w throwing_air

| the throw: the player's own slot; level 3 with it taken - a pool slot (one there per player)
spawn:
    move.b %(owner)d(%%a5),%%d0
    bne 2f
    bsr second
    beq pool1
    jmp 0x%(p1)X
2:  bsr second
    beq pool2
    jmp 0x%(p2)X

%(seconds)spool1:
    jsr 0xA158
    .word 0x%(first)X, (0x%(last)X-0x%(first)X)/0x80
    .byte %(block_p1)s
    beq 7f
    jmp 0x%(fail)X
7:  moveq #0,%%d1
    bra 9f
pool2:
    jsr 0xA158
    .word 0x%(first)X, (0x%(last)X-0x%(first)X)/0x80
    .byte %(block_p2)s
    beq 8f
    jmp 0x%(fail)X
8:  moveq #1,%%d1
9:  move.b %%d1,-(%%sp)                 | (as the original, after its slot is found)
    jsr 0x10098
    jsr 0x5E05E
    move.l 0(%%a5),0(%%a1)
    clr.w 106(%%a1)
    clr.l 72(%%a1)
    move.b (%%sp)+,%(owner)d(%%a1)
    moveq #0,%%d0
    rts

| its look: 200 + level, level 3 as 2
look:
    moveq #0,%%d0
    move.b %(level)d(%%a4),%%d0
    cmpi.b #3,%%d0
    bne 10f
    moveq #2,%%d0
10: add.w #200,%%d0
    rts

| the throw's state each frame: a new press of A, a second acorn allowed - thrown at once (the state left for the
| acorn's attack, a1)
throwing_ground:
    clr.l -(%%sp)                       | (which attack: the ground's / the air's, then the attack itself)
    bra 13f
throwing_air:
    move.l #4,-(%%sp)
13: jsr 0x%(throwing_first)X
    movem.l %%d0-%%d2/%%a0-%%a1,-(%%sp)
    move.b %(owner)d(%%a5),%%d0
    lea 0x%(buttons1)X,%%a0
    lea 0x%(seen)X,%%a1
    tst.b %%d0
    beq 11f
    lea 0x%(buttons2)X,%%a0
    addq.l #2,%%a1
11: move.b 0x%(frame)X,%%d1             | (d2: seen last frame)
    move.b (%%a1),%%d2
    move.b %%d1,(%%a1)
    addq.b #1,%%d2
    sub.b %%d1,%%d2
    move.b 1(%%a1),%%d1                 | (A down then)
    move.b (%%a0),%%d0
    andi.b #0x10,%%d0
    move.b %%d0,1(%%a1)
    tst.b %%d2
    bne 12f
    tst.b %%d1
    bne 12f
    tst.b %%d0
    beq 12f
    move.b %(owner)d(%%a5),%%d0
    bsr second
    beq 14f
    bsr second_boomerang
    bne 12f
    lea boomerang_attacks(%%pc),%%a0
    bra 15f
14: lea acorn_attacks(%%pc),%%a0
15: move.l 20(%%sp),%%d1
    move.l 0(%%a0,%%d1.w),20(%%sp)
    movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    move.l (%%sp)+,(%%sp)               | (the attack in place of the return into the state: its rts goes back
    rts                                 | where the state's would)
12: movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    addq.l #4,%%sp
    rts
acorn_attacks:
    .long 0x%(attack_ground)X, 0x%(attack_air)X
boomerang_attacks:
    .long 0x%(boom_ground)X, 0x%(boom_air)X
""" % {"owner": OWNER, "own1": OWN_SLOT[0], "own2": OWN_SLOT[1], "block1": BLOCK[0], "block2": BLOCK[1],
       "level": LEVEL, "p1": SPAWN_P1, "p2": SPAWN_P2, "first": first, "last": last, "fail": SPAWN_FAIL,
       "code_lo": ACORN_CODE[0], "code_hi": ACORN_CODE[1], "block_p1": blocks[0], "block_p2": blocks[1],
       "throwing_first": THROWING_FIRST, "buttons1": BUTTONS[0], "buttons2": BUTTONS[1], "seen": SEEN,
       "frame": FRAME,
       "attack_ground": THROWING[0][1], "attack_air": THROWING[1][1],
       "boom_ground": BOOMERANG_ATTACKS[0], "boom_air": BOOMERANG_ATTACKS[1], "seconds": seconds},
        why="acorn bomb: level 3's second one (thrown at once), levels 2 / 3 look the same")
    rom.write(SPAWN, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("102D007E6650"),
              why="acorn bomb: the throw - level 3 can have a second one out")
    rom.write(LOOK_SITE, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("303C00C8D02C002C"), why="acorn bomb: level 3 looks like level 2")
    rom.write(GONE_LEVEL3, bytes.fromhex("6000") + (GONE_LEVEL2 - GONE_LEVEL3 - 2).to_bytes(2, "big"),
              expect=bytes.fromhex("303C00EE"), why="acorn bomb: level 3 going off looks like level 2")
    for n, (state, _) in enumerate(THROWING):
        rom.write(state, bytes.fromhex("4EB9") + (code + 8 + 4 * n).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + THROWING_FIRST.to_bytes(4, "big"),
                  why="the throw: level 3's acorn can be thrown again at once")
