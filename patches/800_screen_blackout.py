NAME = "screen-blackout"
DESCRIPTION = "Screen changes: the old screen goes black at once and the new one appears whole (title to how-to-play)"

# Changing screens, the game takes the old one down a piece a frame (the title: its text, then JOURNEY, then the
# scenery strips - scraps on black for a couple of frames) and builds the new one the same way (how-to-play: a
# background strip drawn partway down the screen, then the scene, the item bar, Blue - four frames). Now, as a screen
# ends (BLACKOUT_AT), every colour goes black (palette RAM cleared: sprites, the fix layer, the backdrop) and the
# palette loads that follow (the game's loader, 0xBC86 - each loads palettes from the ROM's palette bank after a
# vblank; LOAD_WAIT) are only noted (LIST); when the new screen is whole they're all copied in at once, at the start
# of a vblank (TICK: the end of the game's vblank wait, 0xE856, every frame) - the screen appears in one frame.
#   * The title ends (TITLE_END: its last calls, the title loop over) - a game starting, or its timeout to the
#     attract sequence (the story; the demo - DEMO_IN - shown whole after its GAME_REVEAL-th frame of play).
#   * No lives left, to the continue screen (CONT_IN); the continue screen answered (CONT_OUTS: back to the level -
#     shown after its GAME_REVEAL-th frame of play - or on to TODAY'S BEST 5).
#   * A stage's title card ends (CARD_ENDS: held out, or skipped) - all but the fix layer (the card's text stays up
#     while the level's built: skipped, the level showed round the text) - shown as the wipe starts.
#   * Each of the story cinema's scenes starts (STORY_SCENES) - each revealed by the fallback.
#   * How-to-play ends (HTP_END: its time up or a button pressed) - blacked out before it's taken down.
#   * How-to-play asks for the reveal on its loop's REVEAL_HTP-th frame (HTP_FRAME: once a loop frame) - the
#     scene, the item bar and Blue all drawn by then.
#   * While it's black, the waits that showed something once are left out (nothing shows): the fix layer's fade-out
#     (FADE_WAIT: 13 steps, 52 frames - in one), every sprite cleared 100 a frame (CLEAR_STEPS - in one), a level's /
#     room's palettes loaded in brightness steps (STEP_WAITS, and the loader's own wait) - entering a house was ~95
#     frames of black.
#   * pause-menu's RESTART LEVEL / QUIT TO TITLE (its pick hooked: REQUEST - black at the next vblank, before the menu's
#     taken down; a
#     restart's level shown after its GAME_REVEAL-th frame of play - stage-wipe's iris waits while it's black).
#   * Direct palette writes while it's black are left out where they'd show early: the game's palette animation
#     (PAL_ANIM), hud's lives (its face colours - the stage's fix palettes have them), how-to-play-look's buttons.
#   * Anything else (a stage's title card, OPTIONS, a picked level ...): FALLBACK frames after the last noted load
#     (held off while how-to-play sets up - HTP_START - for HOLD frames at most), so nothing stays black.
TITLE_END = 0x1B026            # jsr <title's clean-up, title-banner's> ; jsr 0xA136 ; rts
PLAYERS = 0x106800
LOAD_WAIT = 0xBCAA             # jsr 0xE856 - the loader's wait, a0 = the palettes' address, a1 = the source, d2 =
                               # count-1
VBLANK_END = 0xE8B2            # movem.l (sp)+,d1-a5 ; rts - the vblank wait's end
HTP_END = 0x1124A              # clr.b 0x3005(a6) ; clr.b 0x309B(a6) - how-to-play over, before it's taken down
ROOM_INS = [0x12FDE, 0x130F2, 0x131BA]   # jsr 0x15566 - a shop / room entered: the level taken down
DOOR_IN = 0x13098              # jsr 0x13660 - through a door: the sprites cleared (a few hundred a frame), then the
                               # room
FADE_IN = 0x1572C              # lea 0x1576A,a4 ; (bra 0x15732) - the fix layer's fade-in, as a room opens
ROOM_OUTS = [0x1303E, 0x1324C] # jsr 0x13660 - leaving a shop / an NPC room: its sprites cleared, the level rebuilt
GAME_FRAME = 0x11720           # jsr <weapon-switch's> - a frame of play (the gameplay loop's, how-to-play's)
DEMO_IN = 0x106E0              # jsr 0x152FE - the attract demo setting up
STORY_SCENES = [(0x15504, 0x34ACC), (0x15512, 0x34F9A), (0x15520, 0x355B6)]   # (jsr site, scene) - not the last
                               # (0x3533E, at 0x1552E: its colours aren't the loader's and it waits many frames a call -
                               # black, it stayed black; it's only started at a vblank - STORY_LAST)
STORY_LAST = (0x1552E, 0x3533E)
CONT_IN = 0x10E24              # jsr 0xA1BC - no lives left: every sprite cleared, the continue screen next
CONT_OUTS = [0x3475C, 0x34816] # jsr 0xA37A - the continue screen answered (no / time up, yes): its layers cleared
CARD_ENDS = [0x13AFA, 0x13B1C] # jsr <stage-wipe's: the fix layer cleared> - a stage's title card over (held out /
                               # a button pressed)
FADE_WAIT = 0x1573A            # jsr 0xE858 - the fix layer's fade, a step's wait (a4: its table - FADE_OUT_TABLE
                               # fading out)
FADE_OUT_TABLE = 0x15784
CLEAR_STEPS = 0x13676          # moveq #0,d0 ; move.w #99,d1 - every sprite cleared, 100 a frame (0x13660)
STEP_WAITS = [0x5AEE6, 0x5AEFE]   # jsr 0xE856 - the palettes loaded in brightness steps (0x5AED2)
PAL_ANIM = 0x4365A             # movem.l (a2)+,d0-d7 ; movem.l d0-d7,-(a1) - the palette animation's copy of a step
HTP_START = 0x1111C            # jsr 0x15696 - how-to-play setting up
HTP_FRAME = 0x111E6            # move.b #1,0x30DF(a6) - how-to-play's loop, each frame
PALETTES, PALETTE_BYTES = 0x400000, 0x2000
REVEAL_HTP = 5                 # (how-to-play's loop frames: its 4th frame's drawing is whole - shown on the 5th)
FALLBACK = 5                   # (frames after the last noted load: a plain screen, e.g. a stage's title card, is up)
EMPTY = 60                     # (... or after the blackout, if nothing has loaded)
GAME_REVEAL = 5                # (frames of play after a room: the level's drawing whole by its 4th)
ROOM_HOLD = 300                # (a room: frames the fallback waits for its fade-in, at most)
HOLD = 120                     # (how-to-play: frames the fallback waits for its own reveal, at most)
MAX_LOADS = 16
SPRITES = 380                  # (sprites 1-380: hidden for the reveal's first frame)
SAVED = 0x10D000               # spare RAM (see RAM): their SCB3 words, meanwhile
RAM = 0x10E600                 # spare RAM (0x10D000-0x10E6FF: the game only clears it, at the attract cycle's start)
BLACK, REVEAL, SINCE, HTP, COUNT, HOLD_AT = RAM, RAM + 1, RAM + 2, RAM + 4, RAM + 6, RAM + 8
PHASE = RAM + 11               # (a byte: the reveal's sprites hidden - its second vblank next)
GAME_ARM = RAM + 10            # (a byte: 1 + frames of play counted; 0 = not armed)
REQUEST = RAM + 12             # (a byte: pause-menu's pick, 1 RESTART LEVEL / 2 QUIT TO TITLE - black at the next
                               # vblank)
MENU_CURSOR = 0x10E816         # (pause-menu's cursor: its pick is `move.b cursor,d0 ; beq.w resume ; bsr.w close`,
                               # found
                               # in its code - left as it is, its size unchanged: later patches' code doesn't move)
LIST = RAM + 16                # (10 bytes a load)


def apply(rom):
    assert rom.u16(TITLE_END) == 0x4EB9 and rom.u32(TITLE_END + 6) == 0x4EB90000
    title_cleanup = rom.u32(TITLE_END + 2)
    assert rom.u16(GAME_FRAME) == 0x4EB9
    game_first = rom.u32(GAME_FRAME + 2)
    pick = bytes(rom.data).find(bytes.fromhex("1039") + MENU_CURSOR.to_bytes(4, "big") + bytes.fromhex("6700"))
    assert pick > 0 and rom.u16(pick + 10) == 0x6100, "screen-blackout: pause-menu's pick not found"
    menu_resume = pick + 8 + rom.u16(pick + 8)
    menu_close = pick + 12 + rom.u16(pick + 12)
    assert all(rom.u16(at) == 0x4EB9 for at in CARD_ENDS)
    card_ends = [rom.u32(at + 2) for at in CARD_ENDS]
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
    bra.w room_in                       | (+24)
    bra.w fade_in                       | (+28)
    bra.w door_in                       | (+32)
    bra.w room_out                      | (+36)
    bra.w game_frame                    | (+40)
    bra.w pal_anim                      | (+44)
    bra.w demo_in                       | (+48)
    bra.w story0                        | (+52 ... +64: the story's scenes)
    bra.w story1
    bra.w story2
    bra.w story_last                    | (+64)
    bra.w cont_in                       | (+68)
    bra.w cont_out                      | (+72)
    bra.w card_end0                     | (+76)
    bra.w card_end1                     | (+80)
    bra.w fade_wait                     | (+84)
    bra.w clear_all                     | (+88)
    bra.w step_wait                     | (+92)
    bra.w menu_pick                     | (+96)

| the title over: black, if a game is starting
title_end:
    jsr 0xE856                          | (at a vblank: all of it at once)
    bsr blackout
    jmp 0x%(cleanup)X

| every colour black; palette loads noted from here
blackout:
    tst.b 0x%(black)X                   | (black already: as it is - its noted loads kept)
    beq 0f
    rts
0:  movem.l %%d0-%%d7/%%a0,-(%%sp)
    lea 0x%(pal)X,%%a0
    move.w #%(pal_count)d-1,%%d0
    bra 3f
| the same, the fix layer's palettes (0-15) left as they are
blackout_sprites:
    tst.b 0x%(black)X
    beq 0f
    rts
0:  movem.l %%d0-%%d7/%%a0,-(%%sp)
    lea 0x%(pal)X+16*32,%%a0
    move.w #%(pal_count)d-16-1,%%d0
3:
    moveq #0,%%d1
    moveq #0,%%d2
    moveq #0,%%d3
    moveq #0,%%d4
    moveq #0,%%d5
    moveq #0,%%d6
    moveq #0,%%d7                       | (a palette a step: fast enough to be done within the vblank)
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
    tst.b 0x%(black)X                   | (black: no wait for a vblank - the load's only noted)
    bne 1f
    jmp 0xE856
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

| a shop / house / room entered: black at once (at a vblank) before the level's taken down; held till the room's
| fade-in starts
room_in:
    jsr 0xE856
    bsr blackout
    move.w #%(room_hold)d,0x%(hold_at)X
    jmp 0x15566

| a door (shop, house, the game of chance ...): the same, before its first clearing of the sprites
door_in:
    jsr 0xE856
    bsr blackout
    move.w #%(room_hold)d,0x%(hold_at)X
    jmp 0x13660

| out of a room (after its fade-out): black at once before it's taken down; the level shown whole after its
| GAME_REVEAL-th frame of play
room_out:
    jsr 0xE856
    bsr blackout
    move.w #%(room_hold)d,0x%(hold_at)X
    move.b #1,0x%(game_arm)X
    jmp 0x13660

| a frame of play (the gameplay loop's, how-to-play's): armed (back from a room), the reveal on the GAME_REVEAL-th
game_frame:
    tst.b 0x%(game_arm)X
    beq 1f
    tst.b 0x%(black)X
    beq 2f
    addq.b #1,0x%(game_arm)X
    cmpi.b #%(game_reveal)d+1,0x%(game_arm)X
    bcs 1f
    move.b #1,0x%(reveal)X
2:  clr.b 0x%(game_arm)X
1:  jmp 0x%(game_first)X

| the attract demo setting up (black since the title): shown whole after its GAME_REVEAL-th frame of play
demo_in:
    bsr blackout
    move.w #%(room_hold)d,0x%(hold_at)X
    move.b #1,0x%(game_arm)X
    jmp 0x152FE

| the story cinema's scenes, each: black at once (at a vblank) before it starts - its own clearing and loading
story0:
    pea 0x%(scene0)X
    bra 1f
story1:
    pea 0x%(scene1)X
    bra 1f
story2:
    pea 0x%(scene2)X
1:  jsr 0xE856
    bra blackout                        | (its rts: into the scene, which returns to the caller)

| the story's last scene: only started at a vblank (its own clearing then lands before the screen's drawn)
story_last:
    jsr 0xE856
    jmp 0x%(scene_last)X

| a life lost with none left: black at once before the level's taken down for the continue screen
cont_in:
    jsr 0xE856
    bsr blackout
    jmp 0xA1BC

| the continue screen over (yes or no): black at once before it's taken down; back in a level, shown whole after its
| GAME_REVEAL-th frame of play (or the fallback's, if sooner - TODAY'S BEST 5 has no frames of play)
cont_out:
    jsr 0xE856
    bsr blackout
    move.b #1,0x%(game_arm)X
    jmp 0xA37A

| a stage's title card over (held out, or a button): everything but the fix layer black at once (the card's text
| stays up, as stage-wipe has it, while the level's built behind it) - shown on the first frame of play, when the
| wipe starts (its cover over the whole screen by then: the text gone too)
card_end0:
    pea 0x%(card0)X
    bra 1f
card_end1:
    pea 0x%(card1)X
1:  jsr 0xE856
    bsr blackout_sprites
    move.w #%(room_hold)d,0x%(hold_at)X
    move.b #%(game_reveal)d,0x%(game_arm)X   | (shown on its first frame of play: the wipe's start - its cover whole)
    rts                                 | (on to the card's own end)

| pause-menu's pick (in place of its `beq resume ; bsr close`, d0 = the line): RESTART LEVEL / QUIT TO TITLE ask
| for black at the next vblank - and wait for it - before the menu's taken down
menu_pick:
    tst.b %%d0
    bne 1f
    addq.l #4,%%sp
    jmp 0x%(menu_resume)X
1:  move.b %%d0,0x%(request)X
    jsr 0xE856
    jmp 0x%(menu_close)X                | (its rts: back after the call)

| while black, the waits nothing shows any more are left out:
| the fix layer's fade (its 13 steps, 4 frames each): fading out, all at once
fade_wait:
    tst.b 0x%(black)X
    beq 1f
    cmpa.l #0x%(fade_out_table)X,%%a4
    bne 1f
    rts
1:  jmp 0xE858

| every sprite cleared (0x13660: 100 a frame) - all at once, one wait
clear_all:
    tst.b 0x%(black)X
    bne 1f
    moveq #0,%%d0
    move.w #99,%%d1
    jmp 0x1367C
1:  moveq #0,%%d0
    move.w #379,%%d1
    jsr 0xA1BC
    jsr 0xE856
    jmp 0x136C4

| a level's / room's palettes loaded in brightness steps (0x5AED2, a few frames each): no waits
step_wait:
    tst.b 0x%(black)X
    beq 1f
    rts
1:  jmp 0xE856

| the game's palette animation (a level's cycling colours): a step's palette left while black - the reveal puts in
| the loaded one, the next step comes after
pal_anim:
    tst.b 0x%(black)X
    bne 1f
    movem.l (%%a2)+,%%d0-%%d7
    movem.l %%d0-%%d7,-(%%a1)
    rts
1:  lea 32(%%a2),%%a2
    rts

| the fix layer's fade-in (rooms): the colours in as it starts
fade_in:
    tst.b 0x%(black)X
    beq 1f
    move.b #1,0x%(reveal)X
1:  lea 0x1576A,%%a4
    jmp 0x15732

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
    tst.b 0x%(request)X                 | (pause-menu's RESTART LEVEL / QUIT TO TITLE: black now)
    beq 0f
    move.b 0x%(request)X,%%d1
    clr.b 0x%(request)X
    bsr blackout
    cmpi.b #1,%%d1
    bne 9f
    move.w #%(room_hold)d,0x%(hold_at)X | (a restart: the level shown after its GAME_REVEAL-th frame of play - the
    move.b #1,0x%(game_arm)X            | stage wipe waits for it)
    bra 9f
0:  tst.b 0x%(phase)X                   | (the reveal's second vblank)
    bne 20f
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
| the reveal, over two vblanks: first every sprite hidden (its height 0 - the heights kept in SAVED) and every
| palette in but the fix layer's (0-15) and the backdrop's (255) - the copy runs on past the vblank, but nothing
| shows; then (the game held: a nested wait for the next frame) at the next vblank the heights back and those last
| palettes in - quick: the screen appears in one frame
1:  move.l %%d0,-(%%sp)
    bsr hide_all
    moveq #0,%%d6
    bsr replay
    move.b #1,0x%(phase)X
    jsr 0xE856                          | (its end comes back here: phase 2, below)
    move.l (%%sp)+,%%d0
    bra 9f
20: move.l %%d0,-(%%sp)
    bsr show_all
    moveq #1,%%d6
    bsr replay
    move.l (%%sp)+,%%d0
    clr.b 0x%(phase)X
    clr.b 0x%(black)X
    clr.b 0x%(reveal)X
    clr.w 0x%(count)X
    clr.w 0x%(hold_at)X
9:  movem.l (%%sp)+,%%d1-%%d7/%%a0-%%a5
    rts

| the noted loads again, in order (a palette loaded twice: its last load wins): d6 = 0 all but palettes 0-15 and
| 255, else just those
replay:
    lea 0x%(list)X,%%a2
    move.w 0x%(count)X,%%d3
    bra 4f
2:  movem.l (%%a2)+,%%a0-%%a1
    move.w (%%a2)+,%%d2
3:  move.l %%a0,%%d0
    sub.l #0x%(pal)X,%%d0
    lsr.l #5,%%d0
    cmpi.w #16,%%d0
    bcs 5f
    cmpi.w #255,%%d0
    beq 5f
    tst.b %%d6
    bne 7f
    bra 6f
5:  tst.b %%d6
    beq 7f
6:  movem.l (%%a1),%%d0-%%d1/%%d4-%%d5/%%d7/%%a3-%%a5
    movem.l %%d0-%%d1/%%d4-%%d5/%%d7/%%a3-%%a5,(%%a0)
7:  lea 32(%%a0),%%a0
    lea 32(%%a1),%%a1
    dbf %%d2,3b
4:  dbf %%d3,2b
    rts

| every sprite's height 0 (SCB3 kept in SAVED) / back
hide_all:
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    lea 0x3C0000,%%a3
    lea 0x3C0002,%%a4
    lea 0x%(saved)X,%%a0
    move.w #0x8201,%%d0
    move.w #%(sprites)d-1,%%d1
1:  move.w %%d0,(%%a3)
    move.w (%%a4),(%%a0)+
    addq.w #1,%%d0
    dbf %%d1,1b
    move.w #1,4(%%a3)
    move.w #0x8201,(%%a3)
    move.w #%(sprites)d-1,%%d1
2:  move.w #0,(%%a4)
    dbf %%d1,2b
    move.w (%%sp)+,%%sr
    rts

show_all:
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    lea 0x3C0002,%%a4
    lea 0x%(saved)X,%%a0
    move.w #1,0x3C0004
    move.w #0x8201,0x3C0000
    move.w #%(sprites)d-1,%%d1
1:  move.w (%%a0)+,(%%a4)
    dbf %%d1,1b
    move.w (%%sp)+,%%sr
    rts
""" % {"players": PLAYERS, "cleanup": title_cleanup, "pal": PALETTES, "pal_count": PALETTE_BYTES // 32,
       "black": BLACK, "reveal": REVEAL, "since": SINCE, "htp": HTP, "count": COUNT, "list": LIST, "max": MAX_LOADS,
       "reveal_htp": REVEAL_HTP, "fallback": FALLBACK,
       "hold": HOLD, "hold_at": HOLD_AT, "empty": EMPTY, "request": REQUEST, "menu_resume": menu_resume, "menu_close": menu_close, "fade_out_table": FADE_OUT_TABLE, "card0": card_ends[0], "card1": card_ends[1], "scene0": STORY_SCENES[0][1], "scene1": STORY_SCENES[1][1], "scene2": STORY_SCENES[2][1], "scene_last": STORY_LAST[1], "phase": PHASE, "saved": SAVED, "sprites": SPRITES, "room_hold": ROOM_HOLD,
       "game_arm": GAME_ARM, "game_reveal": GAME_REVEAL, "game_first": game_first},
        why="screen changes: black at once, the new screen shown whole")
    jsr = lambda to: bytes.fromhex("4EB9") + to.to_bytes(4, "big")
    rom.write(TITLE_END, jsr(code), expect=jsr(title_cleanup), why="title over: black if a game is starting")
    rom.write(LOAD_WAIT, jsr(code + 4), expect=jsr(0xE856), why="palette loader: noted while black")
    rom.write(HTP_FRAME, jsr(code + 8), expect=bytes.fromhex("1D7C000130DF"), why="how-to-play: its reveal")
    rom.write(HTP_END, jsr(code + 16) + bytes.fromhex("4E71"), expect=bytes.fromhex("422E3005422E309B"),
              why="how-to-play over: black at once")
    rom.write(HTP_START, jsr(code + 20), expect=jsr(0x15696), why="how-to-play setting up: its own reveal")
    for at in ROOM_INS:
        rom.write(at, jsr(code + 24), expect=jsr(0x15566), why="a room entered: black at once")
    rom.write(DOOR_IN, jsr(code + 32), expect=jsr(0x13660), why="through a door: black at once")
    for at in ROOM_OUTS:
        rom.write(at, jsr(code + 36), expect=jsr(0x13660), why="out of a room: black at once")
    rom.write(GAME_FRAME, jsr(code + 40), expect=jsr(game_first), why="a frame of play: the level's reveal")
    rom.write(DEMO_IN, jsr(code + 48), expect=jsr(0x152FE), why="attract demo: shown whole")
    for n, (at, scene) in enumerate(STORY_SCENES):
        rom.write(at, jsr(code + 52 + 4 * n), expect=jsr(scene), why="story cinema: a scene, black at once first")
    rom.write(STORY_LAST[0], jsr(code + 64), expect=jsr(STORY_LAST[1]), why="story cinema: its last scene from a vblank")
    rom.write(CONT_IN, jsr(code + 68), expect=jsr(0xA1BC), why="no lives left: black at once")
    for at in CONT_OUTS:
        rom.write(at, jsr(code + 72), expect=jsr(0xA37A), why="the continue screen over: black at once")
    for n, at in enumerate(CARD_ENDS):
        rom.write(at, jsr(code + 76 + 4 * n), expect=jsr(card_ends[n]), why="a title card over: black at once")
    rom.write(pick + 6, jsr(code + 96) + bytes.fromhex("4E71"), expect=rom.data[pick + 6:pick + 14],
              why="pause menu: restart / quit black at once")
    rom.write(FADE_WAIT, jsr(code + 84), expect=jsr(0xE858), why="fix layer fade: no waits fading out while black")
    rom.write(CLEAR_STEPS, bytes.fromhex("4EF9") + (code + 88).to_bytes(4, "big"), expect=bytes.fromhex("7000323C0063"),
              why="sprites cleared: all at once while black")
    for at in STEP_WAITS:
        rom.write(at, jsr(code + 92), expect=jsr(0xE856), why="palettes in steps: no waits while black")
    rom.write(PAL_ANIM, jsr(code + 44) + bytes.fromhex("4E71"), expect=bytes.fromhex("4CDA00FF48E1FF00"),
              why="palette animation: not while black")
    rom.write(FADE_IN, bytes.fromhex("4EF9") + (code + 28).to_bytes(4, "big"), expect=bytes.fromhex("49F90001576A"),
              why="a room's fade-in: its colours in")
    rom.write(VBLANK_END, bytes.fromhex("4EF9") + (code + 12).to_bytes(4, "big"), expect=bytes.fromhex("4CDF3FFE4E75"),
              why="vblank wait's end: the reveal")
