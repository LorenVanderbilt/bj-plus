NAME = "vine-drop"
DESCRIPTION = "Grabbing a vine while carrying an enemy drops the enemy (it used to stay with Blue on the vine)"

# The user, 2026-11-11: carrying a stunned enemy over his head, Blue jumped onto a vine and the enemy came along,
# floating above him as he swung. Now the enemy is let go as soon as he takes hold of the vine.
#
# A carried enemy runs CARRIED (0x466B6): while its carrier's player block +4 (CARRYING) is set it sits on his head;
# once it's clear it's let go the way the stick points (RELEASE: a jump table by the player's directions - up throws
# it upwards, down throws it flat, anything else tosses it a little), the same as when a throw (0x3CDF6) clears it.
# The vine's grab (GRABS: where each player's on-the-vine byte, +7, is set) now also clears CARRYING and marks the
# player (DROP, a byte in the player block's unused tail, after tunnel-ball-once's TAKEN). For a marked player
# RELEASE ignores the stick and takes the no-direction entry (NO_DIRECTION): the little toss, as if the stick were
# let go - the vine's Up or Right would otherwise throw it. The mark is cleared.
CARRYING = 4                 # player block offsets
ON_VINE = 7
DROP = 0x3F5
PLAYER_BLOCKS = [0x107000, 0x107400]
GRABS = [0x42F1C, 0x42F44]   # move.b #1,0x7007(a6) / 0x7407(a6): a player takes hold of the vine
RELEASE = 0x46806            # move.b 0x3900(a6),d0 ... andi.w #15,d0, up to the jump (0x46818)
RELEASE_END = 0x46818
NO_DIRECTION = 0             # the jump table's entry for the stick let go: the little toss


def apply(rom):
    code = rom.place_code("""
    bra.w grab_p1                       | +0
    bra.w grab_p2                       | +4
    bra.w release                       | +8

| a player takes hold of the vine: an enemy carried is let go
grab_p1:
    lea 0x%(p1)X,%%a1
    bra 0f
grab_p2:
    lea 0x%(p2)X,%%a1
0:  move.b #1,%(on_vine)d(%%a1)
    tst.b %(carrying)d(%%a1)
    beq 1f
    clr.b %(carrying)d(%%a1)
    st %(drop)d(%%a1)
1:  rts

| a carried enemy let go (a5 = the enemy, +126 = its carrier): which way, d0 = the directions
release:
    lea 0x%(p1)X,%%a1
    move.b 0x103900,%%d0
    tst.b 126(%%a5)
    beq 0f
    lea 0x%(p2)X,%%a1
    move.b 0x103904,%%d0
0:  andi.w #15,%%d0
    tst.b %(drop)d(%%a1)
    beq 1f
    clr.b %(drop)d(%%a1)
    moveq #%(no_direction)d,%%d0
1:  rts
""" % {"p1": PLAYER_BLOCKS[0], "p2": PLAYER_BLOCKS[1], "on_vine": ON_VINE, "carrying": CARRYING, "drop": DROP,
       "no_direction": NO_DIRECTION}, why="a vine grabbed: the enemy carried dropped")
    for at, entry, block in zip(GRABS, (0, 4), (0x7007, 0x7407)):
        rom.write(at, bytes.fromhex("4EB9") + (code + entry).to_bytes(4, "big"),
                  expect=bytes.fromhex("1D7C0001") + block.to_bytes(2, "big"), why="the vine grabbed: drop what's carried")
    # jsr release ; bra.s RELEASE_END ; nops
    body = bytes.fromhex("4EB9") + (code + 8).to_bytes(4, "big")
    body += bytes([0x60, RELEASE_END - (RELEASE + len(body) + 2)])
    body += bytes.fromhex("4E71") * ((RELEASE_END - RELEASE - len(body)) // 2)
    rom.write(RELEASE, body, expect=bytes.fromhex("102E39004A2D007E6704102E39040240000F"),
              why="a carried enemy let go: dropped after a vine grab")
