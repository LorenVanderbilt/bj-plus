NAME = "mvs-coin-title"
DESCRIPTION = "Arcade (MVS): a coin on the title adds a credit with a sound - the title carries on, INSERT COIN turns to PUSH START, and its countdown starts the game"

# (the notes in apply). aes-title-first makes the arcade's attract start with the title, as the home console's.
PLAYER_START = 0x108DA  # the game's PLAYER_START (aes-title-first's jmp there)
TITLE_INPUT = 0x1AF9E   # in the title's loop, once a frame: jsr 0x9B16 (the controls)
TITLE_END_SITE = 0x1B026      # the title's end: jsr <title-menu's title_leave> (its markers cleared)
SYSTEM_MODE = 0x10FD82  # BIOS: 0 the home console
USER_MODE = 0x10FDAF    # BIOS: 1 the attract (a coin takes over: wipes the screen, request 3), 2 a game
COUNTDOWN = 0x10FDDA    # BIOS: the credited title's countdown (BCD seconds; the title shows it as TIME)
CREDITS = 0xD00034      # BIOS (MVS): player 1's and player 2's credits (BCD bytes)
CREDIT_CHECK = 0x5F050  # the game's: Z set if no player has a credit
CREDIT_DOWN = 0xC00456  # BIOS: takes 0x10FDB0 / 0x10FDB1 credits from player 1 / 2
CREDIT_MODE = 0x1078CF  # the title in credit mode: PUSH START and TIME, no timeout of its own
QUEUE_SOUND = 0xA27A    # the game's sound queue (d0 = command)
CREDIT_SOUND = 0xC1     # the game's "Credit" sound effect
MVS_TITLE, TICKS, LAST_CREDITS = 0x10E850, 0x10E851, 0x10E852   # spare RAM: the arcade's title is up (byte), frames
                                                                 # to the countdown's next second (byte), credits
                                                                 # last frame (word) - not in 0x10D000-0x10D7FF,
                                                                 # which the title's set-up clears (0x1D10C)
COIN_PENDING = 0x10E854  # spare RAM: a coin went in during the attract (aes-title-first's request 3 notes it): the
                         # Credit sound on the title's first frame
QUIET = 0x10E855         # spare RAM: frames before the Credit sound may play again (the BIOS raises player 1's and
                         # player 2's credits a frame apart: one sound, not two)
COUNT_FROM = 0x30       # the countdown's seconds (BCD), as the original's


def apply(rom):
    names = {"system_mode": SYSTEM_MODE}
    # A coin on the arcade's title (the user, 2026-11-23): the BIOS took over - the screen wiped black (palettes,
    # sprites, the fix layer), the music stopped, the title set up again. Now the title tells the BIOS a game is
    # on (USER_MODE 2), so a coin only adds a credit; the title, its music and all carry on, and Plus does the
    # rest each frame (TITLE_INPUT): the Credit sound as credits go up; with a credit, credit mode (INSERT COIN
    # turns to PUSH START by itself, and the title no longer times out) and the countdown in COUNTDOWN, shown as
    # TIME as the original's; at 0 the game starts (player 1, a credit taken with CREDIT_DOWN, as the BIOS did).
    # Start (PLAYER_START, from the BIOS) puts USER_MODE back to 1 first, so the game starts as ever and the
    # BIOS takes the credit; the title ending with no game started puts it back too (the cinema, the demo).
    sites = {"input": rom.u32(TITLE_INPUT + 2), "leave": rom.u32(TITLE_END_SITE + 2), "start": rom.u32(PLAYER_START + 2)}
    assert rom.u16(TITLE_INPUT) == 0x4EB9 and sites["input"] == 0x9B16
    assert rom.u16(TITLE_END_SITE) == 0x4EB9 and rom.u16(PLAYER_START) == 0x4EF9
    mvs = rom.place_code("""
    bra.w frame
    bra.w leave
    bra.w start
| the title, once a frame
frame:
    tst.b 0x%(system_mode)X
    beq 9f
    movem.l %%d0-%%d2/%%a0,-(%%sp)
    tst.b 0x%(mvs_title)X               | the title's first frame: the credits as they are (no sound for those
    bne 3f                              | left from a game) - but one for a coin that brought the title on
    move.w 0x%(credits)X,0x%(last)X
    st 0x%(mvs_title)X
    clr.b 0x%(quiet)X
    tst.b 0x%(pending)X
    beq 3f
    clr.b 0x%(pending)X
    bsr 20f
3:  move.b #2,0x%(user_mode)X           | a coin: a credit, nothing more
    tst.b 0x%(quiet)X
    beq 4f
    subq.b #1,0x%(quiet)X
4:  move.w 0x%(credits)X,%%d0           | credits up: the Credit sound
    cmp.w 0x%(last)X,%%d0
    bls 1f
    tst.b 0x%(quiet)X
    bne 1f
    bsr 20f
1:  move.w 0x%(credits)X,0x%(last)X
    jsr 0x%(credit_check)X
    beq 8f
    tst.b 0x%(credit_mode)X             | a credit: credit mode, the countdown from COUNT_FROM
    bne 2f
    move.b #1,0x%(credit_mode)X
    move.b #0x%(count)X,0x%(countdown)X
    move.b #60,0x%(ticks)X
2:  subq.b #1,0x%(ticks)X
    bne 8f
    move.b #60,0x%(ticks)X
    move.b 0x%(countdown)X,%%d0         | a second gone (BCD)
    moveq #1,%%d1
    and.b #4,%%ccr                      | (clear X for the BCD subtract)
    sbcd %%d1,%%d0
    move.b %%d0,0x%(countdown)X
    bne 8f
    move.b #1,0x%(user_mode)X           | run out: player 1's game, as the BIOS's own Start
    clr.b 0x%(mvs_title)X
    ori.b #1,0x10FDB4
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    lea 0x100000,%%a6
    jsr 0x%(player_start)X
    move.w #0x0100,0x10FDB0             | its credit
    jsr 0x%(credit_down)X
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
    and.b #0xFC,0x10FDB4
8:  movem.l (%%sp)+,%%d0-%%d2/%%a0
9:  jmp 0x%(input)X
| the Credit sound, then QUIET frames before another
20: move.w #%(sound)d,%%d0
    jsr 0x%(queue_sound)X
    move.b #10,0x%(quiet)X
    rts
| the title's end: no game started - the attract again
leave:
    tst.b 0x%(mvs_title)X
    beq 9f
    clr.b 0x%(mvs_title)X
    tst.b 26624(%%a6)
    bne 9f
    move.b #1,0x%(user_mode)X
9:  jmp 0x%(leave_to)X
| PLAYER_START (the BIOS's, a Start with a credit): the title's "game" was only for the BIOS
start:
    tst.b 0x%(mvs_title)X
    beq 9f
    clr.b 0x%(mvs_title)X
    move.b #1,0x%(user_mode)X
9:  jmp 0x%(start_to)X
""" % dict(names, mvs_title=MVS_TITLE, user_mode=USER_MODE, credits=CREDITS, last=LAST_CREDITS, sound=CREDIT_SOUND,
       queue_sound=QUEUE_SOUND, credit_check=CREDIT_CHECK, credit_mode=CREDIT_MODE, count=COUNT_FROM, pending=COIN_PENDING, quiet=QUIET,
       countdown=COUNTDOWN, ticks=TICKS, player_start=PLAYER_START, credit_down=CREDIT_DOWN, input=sites["input"],
       leave_to=sites["leave"], start_to=sites["start"]), why="arcade: the title carries on through a coin")
    rom.write(TITLE_INPUT + 2, mvs.to_bytes(4, "big"), expect=sites["input"].to_bytes(4, "big"),
              why="arcade title: each frame - coins, credit mode, the countdown")
    rom.write(TITLE_END_SITE + 2, (mvs + 4).to_bytes(4, "big"), expect=sites["leave"].to_bytes(4, "big"),
              why="arcade title: its end - the attract again")
    rom.write(PLAYER_START + 2, (mvs + 8).to_bytes(4, "big"), expect=sites["start"].to_bytes(4, "big"),
              why="arcade title: a Start - the game as ever")
