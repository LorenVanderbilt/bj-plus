NAME = "screen-blackout"
DESCRIPTION = "Screen changes: the old screen goes black at once and the new one appears whole (title to how-to-play)"

# Changing screens, the game takes the old one down a piece a frame (the title: its text, then JOURNEY, then the
# scenery strips - scraps on black for a couple of frames) and builds the new one the same way (how-to-play: a
# background strip drawn partway down the screen, then the scene, the item bar, Blue - four frames). Now, as a screen
# ends (BLACKOUT_AT), every colour goes black (palette RAM cleared: sprites, the fix layer, the backdrop) and the
# palette loads that follow (the game's loader, 0xBC86 - each loads palettes from the ROM's palette bank after a
# vblank; LOAD_WAIT) are only noted (LIST); when the new screen is whole they're all copied in at once, at the start
# of a vblank (TICK: the end of the game's vblank wait, 0xE856, every frame) - the screen appears in one frame.
#   * The title ends (TITLE_END: its last calls, the title loop over) - blacked out when a game is starting (players
#     in, 0x106800), not on its timeout to the attract sequence.
#   * How-to-play ends (HTP_END: its time up or a button pressed) - blacked out before it's taken down.
#   * How-to-play asks for the reveal on its loop's REVEAL_HTP-th frame (HTP_FRAME: once a loop frame) - the
#     scene, the item bar and Blue all drawn by then.
#   * Anything else (a stage's title card, OPTIONS, a picked level ...): FALLBACK frames after the last noted load
#     (held off while how-to-play sets up - HTP_START - for HOLD frames at most), so nothing stays black.
# (Its own patch, last, so its code moves nothing.)
TITLE_END = 0x1B026            # jsr <title's clean-up, title-banner's> ; jsr 0xA136 ; rts
PLAYERS = 0x106800
LOAD_WAIT = 0xBCAA             # jsr 0xE856 - the loader's wait, a0 = the palettes' address, a1 = the source, d2 = count-1
VBLANK_END = 0xE8B2            # movem.l (sp)+,d1-a5 ; rts - the vblank wait's end
HTP_END = 0x1124A              # clr.b 0x3005(a6) ; clr.b 0x309B(a6) - how-to-play over, before it's taken down
HTP_START = 0x1111C            # jsr 0x15696 - how-to-play setting up
HTP_FRAME = 0x111E6            # move.b #1,0x30DF(a6) - how-to-play's loop, each frame
PALETTES, PALETTE_BYTES = 0x400000, 0x2000
REVEAL_HTP = 5                 # (how-to-play's loop frames: its 4th frame's drawing is whole - shown on the 5th)
FALLBACK = 2                   # (frames after the last noted load: a plain screen, e.g. a stage's title card, is up)
EMPTY = 60                     # (... or after the blackout, if nothing has loaded)
HOLD = 120                     # (how-to-play: frames the fallback waits for its own reveal, at most)
MAX_LOADS = 16
RAM = 0x10E600                 # spare RAM (0x10D000-0x10E6FF: the game only clears it, at the attract cycle's start)
BLACK, REVEAL, SINCE, HTP, COUNT, HOLD_AT = RAM, RAM + 1, RAM + 2, RAM + 4, RAM + 6, RAM + 8
LIST = RAM + 10                # (10 bytes a load)


def apply(rom):
    assert rom.u16(TITLE_END) == 0x4EB9 and rom.u32(TITLE_END + 6) == 0x4EB90000
    title_cleanup = rom.u32(TITLE_END + 2)
    assert rom.data[LOAD_WAIT:LOAD_WAIT + 6] == bytes.fromhex("4EB90000E856")
    assert rom.data[VBLANK_END:VBLANK_END + 6] == bytes.fromhex("4CDF3FFE4E75")
    assert rom.data[HTP_FRAME:HTP_FRAME + 6] == bytes.fromhex("1D7C000130DF")
    assert LIST + 10 * MAX_LOADS <= 0x10E700
    code = rom.place_code("""
    bra.w title_end                     | (+0)
    bra.w load_wait                     | (+4)
    bra.w htp_frame                     | (+8)
    bra.w vblank_end                    | (+12)
    bra.w htp_end                       | (+16)
    bra.w htp_start                     | (+20)

| the title over: black, if a game is starting
title_end:
    tst.b 0x%(players)X
    beq 1f
    jsr 0xE856                          | (at a vblank: all of it at once)
    bsr blackout
1:  jmp 0x%(cleanup)X

| every colour black; palette loads noted from here
blackout:
    movem.l %%d0-%%d7/%%a0,-(%%sp)
    lea 0x%(pal)X,%%a0
    moveq #0,%%d1
    moveq #0,%%d2
    moveq #0,%%d3
    moveq #0,%%d4
    moveq #0,%%d5
    moveq #0,%%d6
    moveq #0,%%d7
    moveq #0,%%d0
    swap %%d0
    move.w #%(pal_count)d-1,%%d0          | (a palette a step: fast enough to be done within the vblank)
1:  movem.l %%d1-%%d7,(%%a0)
    clr.l 28(%%a0)
    lea 32(%%a0),%%a0
    dbf %%d0,1b
    move.b #1,0x%(black)X
    clr.b 0x%(reveal)X
    clr.w 0x%(since)X
    clr.w 0x%(htp)X
    clr.w 0x%(count)X
    movem.l (%%sp)+,%%d0-%%d7/%%a0
    rts

| the loader's wait: blacked out, the load is noted and the loader left (its copy skipped)
load_wait:
    jsr 0xE856
    tst.b 0x%(black)X
    bne 1f
    rts
1:  movem.l %%d0/%%a2,-(%%sp)
    move.w 0x%(count)X,%%d0
    cmpi.w #%(max)d,%%d0
    bcc 2f                              | (no room: shown now - the rest of the screen stays black till the reveal)
    addq.w #1,0x%(count)X
    mulu #10,%%d0
    lea 0x%(list)X,%%a2
    adda.w %%d0,%%a2
    move.l %%a0,(%%a2)+
    move.l %%a1,(%%a2)+
    move.w %%d2,(%%a2)
    clr.w 0x%(since)X
    movem.l (%%sp)+,%%d0/%%a2
    addq.l #4,%%sp                      | (out of the loader)
    rts
2:  clr.w 0x%(since)X
    movem.l (%%sp)+,%%d0/%%a2
    rts

| how-to-play setting up: its reveal is its own (the fallback held off a while)
htp_start:
    move.w #%(hold)d,0x%(hold_at)X
    jmp 0x15696

| how-to-play over (its time up, or a button): black at once, before it's taken down
htp_end:
    jsr 0xE856
    bsr blackout
    clr.w 0x%(hold_at)X
    clr.b 0x103005
    clr.b 0x10309B
    rts

| how-to-play's loop, each frame
htp_frame:
    move.b #1,0x1030DF
    tst.b 0x%(black)X
    beq 1f
    addq.w #1,0x%(htp)X
    cmpi.w #%(reveal_htp)d,0x%(htp)X
    bcs 1f
    move.b #1,0x%(reveal)X
1:  rts

| the vblank wait's end (d1-a5 still to be restored: free here; d0 kept): the reveal, when it's time
vblank_end:
    tst.b 0x%(black)X
    beq 9f
    addq.w #1,0x%(since)X
    tst.b 0x%(reveal)X
    bne 1f
    tst.w 0x%(hold_at)X                 | (held: how-to-play reveals itself - unless it's taking too long)
    beq 0f
    subq.w #1,0x%(hold_at)X
    bra 9f
0:  move.w #%(fallback)d,%%d1
    tst.w 0x%(count)X                   | (nothing loaded yet: a long wait - a screen that loads nothing still shows)
    bne 0f
    move.w #%(empty)d,%%d1
0:  cmp.w 0x%(since)X,%%d1
    bhi 9f
1:  lea 0x%(list)X,%%a2
    move.w 0x%(count)X,%%d3
    bra 4f
2:  movea.l (%%a2)+,%%a0
    movea.l (%%a2)+,%%a1
    move.w (%%a2)+,%%d2
3:  move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    dbf %%d2,3b
4:  dbf %%d3,2b
    clr.b 0x%(black)X
    clr.b 0x%(reveal)X
    clr.w 0x%(count)X
    clr.w 0x%(hold_at)X
9:  movem.l (%%sp)+,%%d1-%%d7/%%a0-%%a5
    rts
""" % {"players": PLAYERS, "cleanup": title_cleanup, "pal": PALETTES, "pal_count": PALETTE_BYTES // 32,
       "black": BLACK, "reveal": REVEAL, "since": SINCE, "htp": HTP, "count": COUNT, "list": LIST, "max": MAX_LOADS,
       "reveal_htp": REVEAL_HTP, "fallback": FALLBACK,
       "hold": HOLD, "hold_at": HOLD_AT, "empty": EMPTY},
        why="screen changes: black at once, the new screen shown whole")
    jsr = lambda to: bytes.fromhex("4EB9") + to.to_bytes(4, "big")
    rom.write(TITLE_END, jsr(code), expect=jsr(title_cleanup), why="title over: black if a game is starting")
    rom.write(LOAD_WAIT, jsr(code + 4), expect=jsr(0xE856), why="palette loader: noted while black")
    rom.write(HTP_FRAME, jsr(code + 8), expect=bytes.fromhex("1D7C000130DF"), why="how-to-play: its reveal")
    rom.write(HTP_END, jsr(code + 16) + bytes.fromhex("4E71"), expect=bytes.fromhex("422E3005422E309B"),
              why="how-to-play over: black at once")
    rom.write(HTP_START, jsr(code + 20), expect=jsr(0x15696), why="how-to-play setting up: its own reveal")
    rom.write(VBLANK_END, bytes.fromhex("4EF9") + (code + 12).to_bytes(4, "big"), expect=bytes.fromhex("4CDF3FFE4E75"),
              why="vblank wait's end: the reveal")
