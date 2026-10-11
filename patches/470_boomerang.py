NAME = "boomerang"
DESCRIPTION = "Boomerang: level 2 reaches further; level 3 keeps level 2's size and range but two can be out at once"

# The boomerang (player block +0x2B: level 1-3 - weapon-switch calls it the bomb; +0x2C is the acorn bomb) is an
# object in one fixed slot per player (0x104100 / 0x104180, the acorn's too: the spawn 0x475BC asks 0xA158 for just
# that slot, so while one is out another can't be thrown). It flies a loop round a point ahead of the thrower: the
# point LOOP[level] out, the loop's radius that + 0x800 (so its reach ~ 2 x LOOP + 0x800); its look is animation
# 197 + level (LOOK_SITES; level 3's is the biggest). Level 3 just reached further and was bigger.
#   * level 2 reaches ~15% further (LOOP_LEVEL2), level 3 a little further still (LOOP_LEVEL3) - and looks like
#     level 2;
#   * level 3: with the player's own slot taken, a second one goes in a free slot of the game's general pool
#     (POOL, as enemies' shots use) - only one there per player (a boomerang of theirs already in the pool: no).
LOOP = 0x4793E               # words, levels 0-3: 0, 0x0C00, 0x1000, 0x1400
LOOP_LEVEL2 = 0x1300         # (reach 0x2800 -> 0x2E00)
LOOP_LEVEL3 = 0x1500         # (reach 0x3000 -> 0x3200: a little past level 2's)
LOOK_SITES = (0x478AA, 0x478F4)   # move.w #197,d0 ; add.b 0x2B(a4),d0
SPAWN = 0x475BC              # move.b 0x7E(a5),d0 ; bne.s 0x47610 (player 2's)
SPAWN_P1, SPAWN_P2 = 0x475C2, 0x47610
SPAWN_FAIL = 0x47590
OWN_SLOT = (0x4100, 0x4180)  # (offsets from 0x100000)
BLOCK = (0x7000, 0x7400)     # each player's block
LEVEL = 0x2B
POOL = (0x4480, 0x5B00)      # (first slot, last)
BOOMERANG_CODE = (0x4770A, 0x47946)   # its routines: an object running one of them (+4) is a boomerang
OWNER = 0x7E

def apply(rom):
    rom.write(LOOP + 4, LOOP_LEVEL2.to_bytes(2, "big") + LOOP_LEVEL3.to_bytes(2, "big"),
              expect=bytes.fromhex("10001400"), why="boomerang: level 2 / 3 reach further")
    # the pool spawn: the original's own inline block (the 0xA158 call's data after its slot range), per player
    blocks = []
    for at in (SPAWN_P1, SPAWN_P2):
        data = bytes(rom.data[at + 6 + 4: at + 6 + 4 + 26])
        blocks.append(", ".join("0x%02X" % b for b in data))
    first, last = POOL
    code = rom.place_code(r"""
    bra.w spawn
    bra.w look

| the throw: the player's own slot; level 3 with it taken - a pool slot (one there per player)
spawn:
    move.b %(owner)d(%%a5),%%d0
    bne 2f
    tst.b 0x%(own1)X+0x28(%%a6)
    beq 1f
    cmpi.b #3,0x%(block1)X+%(level)d(%%a6)
    bne 1f
    moveq #0,%%d0
    bsr have
    beq pool1
1:  jmp 0x%(p1)X
2:  tst.b 0x%(own2)X+0x28(%%a6)
    beq 3f
    cmpi.b #3,0x%(block2)X+%(level)d(%%a6)
    bne 3f
    moveq #1,%%d0
    bsr have
    beq pool2
3:  jmp 0x%(p2)X

| Z clear if player d0 has a boomerang in the pool
have:
    movem.l %%d1/%%a0,-(%%sp)
    lea 0x%(first)X(%%a6),%%a0
    move.w #(0x%(last)X-0x%(first)X)/0x80,%%d1
4:  tst.b 0x28(%%a0)
    beq 5f
    cmp.b %(owner)d(%%a0),%%d0
    bne 5f
    cmpi.l #0x%(code_lo)X,4(%%a0)
    bcs 5f
    cmpi.l #0x%(code_hi)X,4(%%a0)
    bcc 5f
    movem.l (%%sp)+,%%d1/%%a0
    andi.b #0xFB,%%ccr
    rts
5:  lea 0x80(%%a0),%%a0
    dbf %%d1,4b
    movem.l (%%sp)+,%%d1/%%a0
    ori.b #4,%%ccr
    rts

pool1:
    jsr 0xA158
    .word 0x%(first)X, (0x%(last)X-0x%(first)X)/0x80
    .byte %(block_p1)s
    beq 6f
    jmp 0x%(fail)X
6:  moveq #0,%%d1
    bra 8f
pool2:
    jsr 0xA158
    .word 0x%(first)X, (0x%(last)X-0x%(first)X)/0x80
    .byte %(block_p2)s
    beq 7f
    jmp 0x%(fail)X
7:  moveq #1,%%d1
8:  move.b %%d1,-(%%sp)                 | (as the original, after its slot is found)
    jsr 0x10098
    jsr 0x5E05E
    move.l 0(%%a5),0(%%a1)
    clr.w 106(%%a1)
    clr.l 72(%%a1)
    move.b (%%sp)+,%(owner)d(%%a1)
    moveq #0,%%d0
    rts

| its look: 197 + level, level 3 as 2
look:
    moveq #0,%%d0
    move.b %(level)d(%%a4),%%d0
    cmpi.b #3,%%d0
    bne 9f
    moveq #2,%%d0
9:  add.w #197,%%d0
    rts
""" % {"owner": OWNER, "own1": OWN_SLOT[0], "own2": OWN_SLOT[1], "block1": BLOCK[0], "block2": BLOCK[1],
       "level": LEVEL, "p1": SPAWN_P1, "p2": SPAWN_P2, "first": first, "last": last, "fail": SPAWN_FAIL,
       "code_lo": BOOMERANG_CODE[0], "code_hi": BOOMERANG_CODE[1], "block_p1": blocks[0], "block_p2": blocks[1]},
        why="boomerang: level 3's second one, levels 2 / 3 look the same")
    rom.write(SPAWN, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("102D007E664E"),
              why="boomerang: the throw - level 3 can have a second one out")
    for at in LOOK_SITES:
        rom.write(at, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex("303C00C5D02C002B"), why="boomerang: level 3 looks like level 2")
