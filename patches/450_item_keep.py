NAME = "item-keep"
DESCRIPTION = "Items: kept when Blue loses a life, lost on a continue (a light safe keeps them once, a super safe for good)"

# In the original, losing a life ran the item-lost routine 0x4B9F4 (player data a4): no safe - every item lost
# (the leaf, weapons, shoes, flippers, fern, clover ...: 0x4BA06 on); a light safe (+0x18 = 1) - the items kept,
# the safe used up (0x4C08A); a super safe (2) - kept while its stage count (+0x21, 3 when bought, one off a stage
# by 0x4B9DC, the safe gone at 0) lasts. A continue (0x3BA34 -> 0x3BA50: the flower penalty, lives from 0x301F)
# didn't touch the items - they were gone already.
# Now (the user's design, 2026-10-10):
#   * losing a life keeps every item (DEATH_CALLS skipped);
#   * a continue is where they're lost: no safe - all of them (0x4BA06 on, as a death was); a light safe - kept,
#     the safe used up; a super safe - kept, and it stays;
#   * the super safe lasts the whole game: 0x4B9DC no longer counts it down (the stage end's other expiries -
#     the clover and its like, 0x4C0B0 / 0x4C0E0 - run as before).
# (The clover is still a one-stage item: the stage end removes it, as in the original.)
DEATH_CALLS = [0x11E7A, 0x124D0]      # jsr 0x4B9F4 (players 1 / 2)
CONTINUE_LIVES = 0x3BA66              # move.b 0x301F(a6),0(a4)   (a4 = the continuing player's data)
ALL_LOST, LIGHT_SAFE_USED = 0x4BA06, 0x4C08A
SAFE = 0x18
SUPER_COUNT = 0x4B9DC                 # subq.b #1,0x21(a4) ; bne 0x4B9EA ; bsr 0x4C098 ; bsr 0x4BE10
AFTER_COUNT = 0x4B9EA


def apply(rom):
    for at in DEATH_CALLS:
        rom.write(at, bytes.fromhex("4E714E714E71"), expect=bytes.fromhex("4EB90004B9F4"),
                  why="losing a life: the items kept")
    code = rom.place_code(r"""
    move.b 0x301F(%%a6),0(%%a4)          | (as it was: the lives)
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    move.b %(safe)d(%%a4),%%d0
    cmp.b #2,%%d0
    beq 9f                              | super safe: kept, and it stays
    cmp.b #1,%%d0
    bne 1f
    jsr 0x%(light)X                     | light safe: kept, the safe used up
    bra 9f
1:  jsr 0x%(all)X                       | no safe: every item lost
9:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
    rts
""" % {"safe": SAFE, "light": LIGHT_SAFE_USED, "all": ALL_LOST}, why="continue: the items lost (a safe keeps them)")
    rom.write(CONTINUE_LIVES, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("196E301F0000"),
              why="continue: the items lost here now")
    rom.write(SUPER_COUNT, bytes([0x60, AFTER_COUNT - (SUPER_COUNT + 2)]), expect=bytes.fromhex("532C"),
              why="super safe: lasts the whole game (no stage count)")
