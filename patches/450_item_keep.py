NAME = "item-keep"
DESCRIPTION = "Items: kept when Blue loses a life, lost on a continue (a light safe keeps them once, a super safe for good)"

# In the original, losing a life ran the item-lost routine 0x4B9F4 on the player data in a4:
#   * with no safe, every item was lost (the leaf, weapons, shoes, flippers, fern, clover and so on, from 0x4BA06);
#   * with a light safe (+0x18 = 1) the items were kept and the safe used up (0x4C08A);
#   * with a super safe (2) they were kept while its stage count lasted (+0x21: 3 when bought, counted down each
#     stage by 0x4B9DC, gone at 0).
# A continue (0x3BA34, then 0x3BA50: the flower penalty and lives from 0x301F) didn't touch the items, since they
# were already gone.
#
# The new rules (designed 2026-10-10):
#   * Losing a life keeps every item (DEATH_CALLS are skipped).
#   * Items are lost on a continue instead. With no safe, all of them go (0x4BA06 on, as a death did). A light safe
#     keeps them and is used up. A super safe keeps them and stays.
#   * The super safe lasts the whole game, since 0x4B9DC no longer counts it down. The stage end's other expiries
#     (0x4C0B0 / 0x4C0E0) run as before, so the clover still only lasts one stage.
DEATH_CALLS = [0x11E7A, 0x124D0]      # jsr 0x4B9F4, players 1 and 2
CONTINUE_LIVES = 0x3BA66              # move.b 0x301F(a6),0(a4), with a4 = the continuing player's data
ALL_LOST, LIGHT_SAFE_USED = 0x4BA06, 0x4C08A
SAFE = 0x18
SUPER_COUNT = 0x4B9DC                 # subq.b #1,0x21(a4) ; bne 0x4B9EA ; bsr 0x4C098 ; bsr 0x4BE10
AFTER_COUNT = 0x4B9EA


def apply(rom):
    for at in DEATH_CALLS:
        rom.write(at, bytes.fromhex("4E714E714E71"), expect=bytes.fromhex("4EB90004B9F4"),
                  why="losing a life: the items kept")
    code = rom.place_code(r"""
    move.b 0x301F(%%a6),0(%%a4)          | as before: the lives
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    move.b %(safe)d(%%a4),%%d0
    cmp.b #2,%%d0
    beq 9f                              | super safe: items kept, and it stays
    cmp.b #1,%%d0
    bne 1f
    jsr 0x%(light)X                     | light safe: items kept, the safe used up
    bra 9f
1:  jsr 0x%(all)X                       | no safe: every item lost
9:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
    rts
""" % {"safe": SAFE, "light": LIGHT_SAFE_USED, "all": ALL_LOST}, why="continue: the items lost (a safe keeps them)")
    rom.write(CONTINUE_LIVES, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("196E301F0000"),
              why="continue: the items lost here now")
    rom.write(SUPER_COUNT, bytes([0x60, AFTER_COUNT - (SUPER_COUNT + 2)]), expect=bytes.fromhex("532C"),
              why="super safe: lasts the whole game (no stage count)")
