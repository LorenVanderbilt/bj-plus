NAME = "weapon-switch"
DESCRIPTION = "D button: switch between the weapons collected (leaf, boomerang, acorn bomb), each keeping its own level"

# The game holds one weapon at a time, in the player block (0x107000 / 0x107400): the leaf's level at +0x12 (0-2; the
# basic leaf is always there), the boomerang's at +0x2B and the bomb's at +0x2C (0 = not held, 1-3). Picking one up
# made it the weapon and carried the level over, so a level 2 leaf followed by a boomerang gave a level 2 boomerang.
# The item bar shows the weapon held (items 3, 0x10, 0x11). Dying runs each item's lost routine (0x4B9F4, with some
# skipped by the shop's safes), including the weapons' (leaf 0x4C036, boomerang 0x4C10C, bomb 0x4C11A).
#
# Each weapon now keeps its own level in the player block's unused tail (STASH: leaf, boomerang, bomb, with STASH + 3
# holding last frame's D button), and the game's bytes only describe the weapon in hand:
#   * A pickup raises that weapon's own level (the leaf to 2, the others to 3) and puts it in hand; the item bar
#     updates as before.
#   * A new press of D (each player's own) switches to the next collected weapon: leaf, boomerang, bomb, and round
#     again. The leaf is always there; the others once picked up. The item bar changes to match.
#   * A weapon's lost routine also clears its stored level, so dying loses weapons as before, and a safe still keeps
#     what it keeps.
#   * A new game, or a player joining (0x3B94C, where flowers and hearts are set), clears them.
STASH = 0x3F0                # player block offset; the block's used part ends at +0x302
LEAF, BOOMERANG, BOMB = 0x12, 0x2B, 0x2C
LEAF_MAX, OTHER_MAX = 2, 3
ITEM_LEAF, ITEM_BOOMERANG, ITEM_BOMB = 3, 0x10, 0x11
ADD_ITEM, REMOVE_ITEM = 0x4B94A, 0x4B972     # d0 = item, a4 = player block
PLAYERS_IN = 0x106808        # bits 0 / 1: player 1 / 2 in the game
BUTTONS = [0x10FD96, 0x10FD9C]   # each player's buttons held; bit 7 = D
SWITCH_SOUND = -0x33         # the pickup sound
PLAY_SOUND = 0x152FE

FRAME_SITE = 0x11720         # jsr 0xA07C: the first call of a gameplay frame (mode 1, not while paused)
LEAF_PICK = (0x4BCA0, 0x4BCCC)       # the leaf pickup's level logic, up to the item bar part
BOOMERANG_PICK = (0x4BF34, 0x4BF5C)
BOMB_PICK = (0x4BF90, 0x4BFB8)
LEAF_LOST = 0x4C036          # clr.b 0x12(a4) ; moveq #3,d0
BOOMERANG_LOST = 0x4C114     # clr.b 0x2B(a4) ; rts
BOMB_LOST = 0x4C122          # clr.b 0x2C(a4) ; rts
JOIN = 0x3B958               # move.b 0x3C03(a6),0x20(a4)


def apply(rom):
    code = rom.place_code(r"""
    bra.w frame
    bra.w leaf_pick
    bra.w boomerang_pick
    bra.w bomb_pick
    bra.w leaf_lost
    bra.w boomerang_lost
    bra.w bomb_lost
    bra.w join

| store the level of the weapon in hand (a4 = player block)
sync:
    move.b %(boomerang)d(%%a4),%%d0
    beq 1f
    move.b %%d0,%(stash)d+1(%%a4)
    rts
1:  move.b %(bomb)d(%%a4),%%d0
    beq 2f
    move.b %%d0,%(stash)d+2(%%a4)
    rts
2:  move.b %(leaf)d(%%a4),%(stash)d(%%a4)
    rts

| put the leaf, boomerang or bomb in hand at its own level
hold_leaf:
    move.b %(stash)d(%%a4),%(leaf)d(%%a4)
    clr.b %(boomerang)d(%%a4)
    clr.b %(bomb)d(%%a4)
    rts
hold_boomerang:
    move.b %(stash)d+1(%%a4),%(boomerang)d(%%a4)
    clr.b %(leaf)d(%%a4)
    clr.b %(bomb)d(%%a4)
    rts
hold_bomb:
    move.b %(stash)d+2(%%a4),%(bomb)d(%%a4)
    clr.b %(leaf)d(%%a4)
    clr.b %(boomerang)d(%%a4)
    rts

| pickups: raise that weapon's level and put it in hand; the game's item bar part follows
leaf_pick:
    bsr sync
    cmpi.b #%(leaf_max)d,%(stash)d(%%a4)
    bcc 1f
    addq.b #1,%(stash)d(%%a4)
1:  bra hold_leaf
boomerang_pick:
    bsr sync
    cmpi.b #%(other_max)d,%(stash)d+1(%%a4)
    bcc 1f
    addq.b #1,%(stash)d+1(%%a4)
1:  bra hold_boomerang
bomb_pick:
    bsr sync
    cmpi.b #%(other_max)d,%(stash)d+2(%%a4)
    bcc 1f
    addq.b #1,%(stash)d+2(%%a4)
1:  bra hold_bomb

| lost on dying: clear its stored level too
leaf_lost:
    clr.b %(leaf)d(%%a4)
    clr.b %(stash)d(%%a4)
    moveq #%(item_leaf)d,%%d0
    rts
boomerang_lost:
    clr.b %(boomerang)d(%%a4)
    clr.b %(stash)d+1(%%a4)
    rts
bomb_lost:
    clr.b %(bomb)d(%%a4)
    clr.b %(stash)d+2(%%a4)
    rts

| a new game or a player joining: none collected
join:
    move.b 0x3C03(%%a6),0x20(%%a4)
    clr.l %(stash)d(%%a4)
    rts

| every gameplay frame: each player's D
frame:
    jsr 0xA07C
    movem.l %%d0-%%d2/%%a0/%%a4,-(%%sp)
    btst #0,0x%(players)X
    beq 1f
    lea 0x107000,%%a4
    move.b 0x%(buttons1)X,%%d1
    bsr d_button
1:  btst #1,0x%(players)X
    beq 2f
    lea 0x107400,%%a4
    move.b 0x%(buttons2)X,%%d1
    bsr d_button
2:  movem.l (%%sp)+,%%d0-%%d2/%%a0/%%a4
    rts

d_button:                               | d1 = buttons held; a new press of D switches
    move.b %(stash)d+3(%%a4),%%d2
    move.b %%d1,%(stash)d+3(%%a4)
    not.b %%d2
    and.b %%d2,%%d1
    btst #7,%%d1
    beq 9f
    bsr sync
    moveq #0,%%d2                       | d2 = in hand: 0 leaf, 1 boomerang, 2 bomb
    tst.b %(boomerang)d(%%a4)
    beq 1f
    moveq #1,%%d2
1:  tst.b %(bomb)d(%%a4)
    beq 2f
    moveq #2,%%d2
2:  move.w %%d2,%%d1                    | the next one collected (the leaf always is)
3:  addq.w #1,%%d1
    cmp.w #3,%%d1
    bcs 4f
    moveq #0,%%d1
4:  tst.w %%d1
    beq 5f
    lea %(stash)d(%%a4),%%a0
    tst.b (%%a0,%%d1.w)
    beq 3b
5:  cmp.w %%d2,%%d1
    beq 9f                              | only the one in hand
    move.w %%d1,-(%%sp)
    moveq #%(item_leaf)d,%%d0           | the item bar: remove the old one
    jsr 0x%(remove)X
    moveq #%(item_boomerang)d,%%d0
    jsr 0x%(remove)X
    moveq #%(item_bomb)d,%%d0
    jsr 0x%(remove)X
    move.w (%%sp)+,%%d1
    tst.w %%d1
    bne 6f
    bsr hold_leaf
    moveq #%(item_leaf)d,%%d0
    bra 8f
6:  cmp.w #1,%%d1
    bne 7f
    bsr hold_boomerang
    moveq #%(item_boomerang)d,%%d0
    bra 8f
7:  bsr hold_bomb
    moveq #%(item_bomb)d,%%d0
8:  jsr 0x%(add)X                       | and add the new one
    moveq #%(sound)d,%%d0
    jsr 0x%(play)X
9:  rts
""" % {"stash": STASH, "leaf": LEAF, "boomerang": BOOMERANG, "bomb": BOMB, "leaf_max": LEAF_MAX, "other_max": OTHER_MAX,
       "item_leaf": ITEM_LEAF, "item_boomerang": ITEM_BOOMERANG, "item_bomb": ITEM_BOMB, "add": ADD_ITEM,
       "remove": REMOVE_ITEM, "players": PLAYERS_IN, "buttons1": BUTTONS[0], "buttons2": BUTTONS[1],
       "sound": SWITCH_SOUND, "play": PLAY_SOUND},
        why="weapon switch: D, each weapon's own level")

    def jsr(at, entry, expect, why, pad_to=6):
        body = bytes.fromhex("4EB9") + (code + entry).to_bytes(4, "big")
        rom.write(at, body + bytes.fromhex("4E71") * ((pad_to - 6) // 2), expect=bytes.fromhex(expect), why=why)

    jsr(FRAME_SITE, 0, "4EB90000A07C", "gameplay frame: the D button switches weapons")
    for (start, back), entry, name in ((LEAF_PICK, 4, "leaf"), (BOOMERANG_PICK, 8, "boomerang"), (BOMB_PICK, 12,
                                                                                      "bomb")):
        size = back - start
        body = bytes.fromhex("4EB9") + (code + entry).to_bytes(4, "big")
        disp = back - (start + 6 + 2)
        body += bytes([0x60, disp]) if disp < 128 else bytes.fromhex("6000") + (back - (start + 8)).to_bytes(2, "big")
        body += bytes.fromhex("4E71") * ((size - len(body)) // 2)        # nops up to the item bar part
        rom.write(start, body, expect=bytes(rom.data[start:start + size]), why="%s pickup: its own level" % name)
    jsr(LEAF_LOST, 16, "422C00127003", "leaf lost (dying): its own level too")
    rom.write(BOOMERANG_LOST, bytes.fromhex("4EF9") + (code + 20).to_bytes(4, "big"), expect=bytes.fromhex("422C002B4E75"),
              why="boomerang lost (dying): its own level too")
    rom.write(BOMB_LOST, bytes.fromhex("4EF9") + (code + 24).to_bytes(4, "big"),
              expect=bytes.fromhex("422C002C4E75"), why="bomb lost (dying): its own level too")
    jsr(JOIN, 28, "196E3C030020", "a new game / joining: no weapons collected")
