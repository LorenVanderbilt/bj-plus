NAME = "two-player-prompt"
DESCRIPTION = "Two players: CONTINUE? and GAME OVER over a player's HUD clear the whole HUD; player 1's Start there continues without pausing"

# In a two-player game a player out of lives gets a prompt in their HUD's corner (1P / CONTINUE? / the countdown,
# later GAME OVER; also the join prompts): the inline printer (0x9FE6) blanks a 14-column block at rows 3-5 (from
# column 1 for player 1, 25 for player 2) and prints the lines in it. That was the old HUD's rows; hud's layout
# reaches from row 2 (the score line's top half) to row 6 (the hearts' bottom half), so those two rows stayed, cut in
# half (the user, 2026-11-10). Each print whose record starts the block (fix address ROW3: column 1 or 25, row 3) now
# goes through `prompt`, which blanks that player's rows 2 and 6 over the same columns first. The HUD draws neither
# while the prompt is up, and redraws them when the player is back in play.
#
# Player 1's Start answers CONTINUE?, but pause-start also paused the game with it, since player 1 still counts as in
# the game during the prompt (the user, 2026-11-10). Player 1's prompt state (PROMPT: 1 for CONTINUE?, then 7 and 3
# through GAME OVER, 0 in play) is non-zero for the whole prompt; after it player 1 leaves the players byte and
# pause-start's join check takes over. So the pause's check (PAUSE_CHECK, pause-start's press detector, still called
# every frame to keep its last-frame state) counts a press only while PROMPT is 0, now and at the previous check
# (PREV_PROMPT): the game takes the Start that continues earlier in the same frame and clears PROMPT before the
# check. Unpausing (0x11B06) is unchanged.
PAUSE_CHECK = 0x11AC0           # jsr <pause-start's press detector> ; nop ; nop ; beq <no pause>
PROMPT = 0x107023
PREV_PROMPT = 0x10E802          # spare RAM (a byte, beside pause-start's): PROMPT at the previous check
PRINT = 0x9FE6
ROW3 = {0x7000 + 1 * 32 + 3: 1, 0x7000 + 25 * 32 + 3: 25}   # the block's first record: its first column
WIDTH = 14
BLANK = 0x5520                  # the prompt's own blank (palette 5)
SEARCH = (0x10000, 0x13000)     # the game modes' code, where the prompts are printed


def apply(rom):
    jsr = bytes.fromhex("4EB9") + PRINT.to_bytes(4, "big")
    sites = []
    at = SEARCH[0]
    while True:
        at = bytes(rom.data).find(jsr, at, SEARCH[1])
        if at < 0:
            break
        if rom.u16(at + 6) in ROW3 and rom.u16(at + 8) == 0xFC55:
            sites.append(at)
        at += 2
    assert len(sites) >= 20, "two-player-prompt: only %d prompt prints found" % len(sites)
    code = rom.place_code("""
| an inline print starting a HUD prompt (its record after the return address): blank rows 2 and 6 of that player's
| columns, then print as before
    movem.l %%d0-%%d2/%%a0,-(%%sp)
    movea.l 16(%%sp),%%a0
    move.w (%%a0),%%d0                  | the record's fix address: column * 32 + row 3
    subq.w #1,%%d0                      | row 2
    moveq #%(w1)d,%%d2
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #32,0x3C0004
    move.w %%d0,0x3C0000
    move.w %%d2,%%d1
0:  move.w #0x%(blank)X,0x3C0002
    dbf %%d1,0b
    addq.w #4,%%d0                      | row 6
    move.w %%d0,0x3C0000
1:  move.w #0x%(blank)X,0x3C0002
    dbf %%d2,1b
    move.w #1,0x3C0004
    move.w (%%sp)+,%%sr
    movem.l (%%sp)+,%%d0-%%d2/%%a0
    jmp 0x%(print)X
""" % {"w1": WIDTH - 1, "blank": BLANK, "print": PRINT}, why="two-player-prompt: the HUD's rows 2 and 6 blanked")
    detector = rom.u32(PAUSE_CHECK + 2)
    check = rom.place_code("""
| the pause's check: a new press of player 1's Start, and player 1 not in a prompt (Z clear = pause)
    jsr 0x%(detector)X
    sne %%d0                            | 0xFF: a new press
    tst.b 0x%(prompt)X
    beq 0f
    clr.b %%d0                          | the prompt is up
0:  tst.b 0x%(prev)X
    beq 1f
    clr.b %%d0                          | ... or was, and the press just continued
1:  move.b 0x%(prompt)X,0x%(prev)X
    tst.b %%d0
    rts
""" % {"detector": detector, "prompt": PROMPT, "prev": PREV_PROMPT}, why="two-player-prompt: no pause from the prompt")
    rom.write(PAUSE_CHECK + 2, check.to_bytes(4, "big"), expect=detector.to_bytes(4, "big"),
              why="pause: not while player 1's CONTINUE? / GAME OVER is up")
    for at in sites:
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=jsr,
                  why="two-player prompt at 0x%04X: rows 2 and 6 blanked too" % rom.u16(at + 6))
