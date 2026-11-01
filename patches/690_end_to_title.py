NAME = "end-to-title"
DESCRIPTION = "Home console (AES): after a game over or the ending, back to the title (not the attract demo)"

# A whole game runs inside START_GAME (0x10CE8), the mode loop from the first stage to the game over or ending, then
# the save prompt, initials and TODAY'S BEST, before returning to the attract sequence. The attract sequence
# alternates two cycles on bit 0 of ATTRACT_TOGGLE. With aes-title-first, cycle 1 is the title and then the story
# cinema, and cycle 2 is the demo, the high scores and the items. After a game it was cycle 2's turn, so the demo ran.
#
# Now bit 0 is cleared as START_GAME ends (GAME_END), so the title comes next, as with the pause menu's QUIT TO
# TITLE. This is for the home console only (SYSTEM_MODE 0). On the arcade, cycle 1 opens with the story cinema, so
# it keeps its own flow.
GAME_END = 0x10D18
GAME_END_BYTES = "422E306E70FF"
ATTRACT_TOGGLE = 0x1033CA      # bit 0 clear: the attract cycle with the title runs next
SYSTEM_MODE = 0x10FD82         # 0 = home console


def apply(rom):
    code = rom.place_code("""
    clr.b 0x306E(%%a6)                  | replaced by the jump
    tst.b 0x%(mode)X
    bne 1f
    bclr #0,0x%(toggle)X                | the title comes next
1:  moveq #-1,%%d0
    rts
""" % {"mode": SYSTEM_MODE, "toggle": ATTRACT_TOGGLE}, why="a game's end: the title next (AES)")
    rom.write(GAME_END, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex(GAME_END_BYTES),
              why="a game's end: back to the title")
