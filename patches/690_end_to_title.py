NAME = "end-to-title"
DESCRIPTION = "Home console (AES): after a game over or the ending, back to the title (not the attract demo)"

# A whole game is START_GAME (0x10CE8: the mode loop, from the first stage to the game over or the ending - its save
# prompt, the initials, TODAY'S BEST - then back to the attract sequence). The attract sequence alternates two cycles
# by ATTRACT_TOGGLE's bit 0 (aes-title-first: cycle 1 the title then the story cinema, cycle 2 the demo, the high
# scores, the items), and after a game it was cycle 2's turn: the demo. Now, as START_GAME ends (GAME_END: clr.b
# 0x306E(a6) ; moveq #-1,d0 ; rts), bit 0 is cleared - the title next - as the pause menu's QUIT TO TITLE does. Home
# console only (SYSTEM_MODE 0); the arcade's cycle 1 opens with the story cinema, so it keeps its flow.
# (Its own patch, last, so its code moves nothing.)
GAME_END = 0x10D18
GAME_END_BYTES = "422E306E70FF"
ATTRACT_TOGGLE = 0x1033CA      # bit 0 clear: the attract cycle with the title runs next
SYSTEM_MODE = 0x10FD82         # 0: home console


def apply(rom):
    code = rom.place_code("""
    clr.b 0x306E(%%a6)                  | (what the jump replaced)
    tst.b 0x%(mode)X
    bne 1f
    bclr #0,0x%(toggle)X                | the title next
1:  moveq #-1,%%d0
    rts
""" % {"mode": SYSTEM_MODE, "toggle": ATTRACT_TOGGLE}, why="a game's end: the title next (AES)")
    rom.write(GAME_END, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex(GAME_END_BYTES),
              why="a game's end: back to the title")
