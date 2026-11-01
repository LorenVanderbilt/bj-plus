NAME = "blackout-gaps"
DESCRIPTION = ("Screen changes: screen-blackout's last gaps - the story's last scene and its beam, a room's way out, "
               "TODAY'S BEST 5 in the attract, the title after the story, elevator-spin's colours")

# screen-blackout blacks out the old screen at once and shows the new one only when it's complete. These are the
# screens it missed:
#   * The story's last scene (STORY_LAST) loads no colours of its own, keeping the previous scene's, so it couldn't
#     be blacked out and its sprites appeared while the screen was drawn (one torn frame). Its colours are now saved
#     to BUF, the screen is blacked out like the other scenes (screen-blackout's story path, BLACKOUT_STORY2), and
#     BUF is registered as a palette load so the reveal puts them back once the scene is complete.
#   * The last scene's cut to the beam (BEAM_CUT, as its last text box closes, where story-last-line also hooks)
#     redraws its layers over about 3 frames. It now goes black first, saving the colours the same way, and is shown
#     once drawn.
#   * The way out of the third room (ROOM_OUT3, the room at 0x130EC) now goes through screen-blackout's room_out like
#     the others. Its way in was already covered; the attract demo walks into it too.
#   * The attract's TODAY'S BEST 5 (BEST_IN) appeared in pieces. It's now blacked out at a vblank as it starts, held,
#     and shown complete as its loop starts (BEST_LOOP, also used after a game over).
#   * The title set-up (TITLE_SETUP, which the end of the story jumps into) now blacks out at once first, since the
#     story's last frames were cleared in strips over their colours. screen-blackout's fallback then shows the title.
#   * elevator-spin's colour cycling (ELEVATOR_PAL) kept writing its palette while the screen was black, leaving the
#     cone alone on a black screen. While black it now writes to spare RAM (NOWHERE) instead.
# BUF is RAM that shops and NPC rooms use for the level's objects, free during the story; round-clear-dim uses it at
# ROUND CLEAR.
STORY_LAST = (0x1552E, 0x3533E)  # jsr <screen-blackout's story_last> for the last scene; the scene
BLACKOUT_STORY_LAST = 64        # offsets of screen-blackout's entries (a bra.w each): story_last, story2, room_out
BLACKOUT_STORY2 = 60            # pea <scene> ; jsr 0xE856 ; bra blackout
BLACKOUT_ROOM_OUT = 36
ROOM_OUT3 = 0x1316A             # jsr 0x13660, leaving the room at 0x130EC: clears its sprites, rebuilds the level
ELEVATOR_PAL = bytes.fromhex("41F900401EE2720E30D9")   # elevator-spin: lea 0x401EE2,a0 ; moveq #14,d1 ;
                                                       # move.w (a1)+,(a0)+
BEST_IN = 0x10854               # jsr 0x152FE (its music), as the attract's TODAY'S BEST 5 starts
BEST_LOOP = 0x549D0             # move.w #512,0x3800(a6), as TODAY'S BEST 5's loop starts
BEST_HOLD = 120                 # the most frames screen-blackout's fallback waits
BEAM_CUT = 0x35494              # jsr <story-last-line>, just before the beam's layers are drawn
TITLE_SETUP = 0x1AE76           # move.b #32,0x3005(a6) in the title set-up; the story's end branches here
BUF = 0x10B000                  # 256 x 32 bytes, to 0x10CFFF
NOWHERE = 0x10D510              # 30 bytes of spare RAM for elevator-spin's colours while black


def branch_target(rom, at):
    """Where the bra / bra.w at `at` goes."""
    op = rom.u16(at)
    if op == 0x6000:
        d = rom.u16(at + 2)
        return at + 2 + (d - 0x10000 if d & 0x8000 else d)
    assert op >> 8 == 0x60, "not a bra at 0x%X" % at
    return at + 2 + ((op & 0xFF) - 0x100 if op & 0x80 else op & 0xFF)


def apply(rom):
    blackout = rom.other_patch("screen-blackout")
    blackout_code = rom.u32(STORY_LAST[0] + 2) - BLACKOUT_STORY_LAST
    story2 = branch_target(rom, blackout_code + BLACKOUT_STORY2)
    assert rom.u16(story2) == 0x4879 and rom.u16(story2 + 6) == 0x4EB9, "screen-blackout's story path moved"
    black_now = branch_target(rom, story2 + 12)
    assert rom.u16(black_now) == 0x4A39, "screen-blackout's blackout moved"   # tst.b <BLACK>
    assert rom.u16(BEAM_CUT) == 0x4EB9
    beam_hook = rom.u32(BEAM_CUT + 2)
    code = rom.place_code("""
    bra.w story_last                    | +0
    bra.w elevator_pal                  | +4
    bra.w best_in                       | +8
    bra.w best_loop                     | +12
    bra.w title_setup                   | +16
    bra.w beam_cut                      | +20

| the story's last scene: save its colours, black out as screen-blackout does, and register them as a load
story_last:
    bsr keep_colours
    pea 0x%(scene_last)X
    pea story_noted(%%pc)
    jmp 0x%(story_black)X               | black at a vblank; its rts goes to story_noted

| the cut to the beam: the same, black while its layers are drawn
beam_cut:
    bsr keep_colours
    jsr 0xE856
    jsr 0x%(blackout)X
    bsr story_noted
    jmp 0x%(beam_hook)X

keep_colours:
    movem.l %%d0/%%a0-%%a1,-(%%sp)
    lea 0x400000,%%a0
    lea 0x%(buf)X,%%a1
    move.w #256*8-1,%%d0
1:  move.l (%%a0)+,(%%a1)+
    dbf %%d0,1b
    movem.l (%%sp)+,%%d0/%%a0-%%a1
    rts

story_noted:
    movem.l %%d0/%%a0,-(%%sp)
    move.w 0x%(b_count)X,%%d0
    cmpi.w #%(b_max)d,%%d0
    bcc 1f
    addq.w #1,0x%(b_count)X
    mulu #10,%%d0
    lea 0x%(b_list)X,%%a0
    adda.w %%d0,%%a0
    move.l #0x400000,(%%a0)+            | to: every palette
    move.l #0x%(buf)X,(%%a0)+           | from: the saved colours
    move.w #255,(%%a0)
    move.b #1,0x%(b_reveal)X            | shown at its first vblank wait, once the scene is set up
1:  movem.l (%%sp)+,%%d0/%%a0
    rts                                 | into the scene

| elevator-spin's colours go to palette 0xF7, or nowhere while black
elevator_pal:
    lea 0x401EE2,%%a0
    tst.b 0x%(b_black)X
    beq 1f
    lea 0x%(nowhere)X,%%a0
1:  rts

| the attract's TODAY'S BEST 5 starting: black at once, at a vblank
best_in:
    jsr 0xE856
    jsr 0x%(blackout)X
    move.w #%(best_hold)d,0x%(b_hold_at)X
    jmp 0x152FE

| TODAY'S BEST 5 set up: show it at its loop's first vblank
best_loop:
    move.w #512,0x3800(%%a6)
    tst.b 0x%(b_black)X
    beq 1f
    move.b #1,0x%(b_reveal)X
1:  rts

| the title being set up: black at once, at a vblank, first
title_setup:
    jsr 0xE856
    jsr 0x%(blackout)X
    move.b #32,0x3005(%%a6)
    rts
""" % {"buf": BUF, "scene_last": STORY_LAST[1], "story_black": story2 + 6, "b_count": blackout.COUNT,
       "b_list": blackout.LIST, "b_max": blackout.MAX_LOADS, "b_reveal": blackout.REVEAL, "b_black": blackout.BLACK,
       "b_hold_at": blackout.HOLD_AT, "nowhere": NOWHERE, "blackout": black_now, "best_hold": BEST_HOLD,
       "beam_hook": beam_hook},
        why="screen-blackout's last gaps")
    rom.write(STORY_LAST[0] + 2, code.to_bytes(4, "big"),
              expect=(blackout_code + BLACKOUT_STORY_LAST).to_bytes(4, "big"), why="story cinema: its last scene blacked out too")
    rom.write(ROOM_OUT3 + 2, (blackout_code + BLACKOUT_ROOM_OUT).to_bytes(4, "big"),
              expect=(0x13660).to_bytes(4, "big"), why="out of the room at 0x130EC: black at once, the level shown whole")
    rom.write(BEST_IN, bytes.fromhex("4EB9") + (code + 8).to_bytes(4, "big"), expect=bytes.fromhex("4EB9000152FE"),
              why="attract: TODAY'S BEST 5 blacked out at once")
    rom.write(BEST_LOOP, bytes.fromhex("4EB9") + (code + 12).to_bytes(4, "big"), expect=bytes.fromhex("3D7C02003800"),
              why="TODAY'S BEST 5: shown whole as its loop starts")
    rom.write(BEAM_CUT + 2, (code + 20).to_bytes(4, "big"), expect=beam_hook.to_bytes(4, "big"),
              why="story: the beam's cut blacked out while its layers are drawn")
    rom.write(TITLE_SETUP, bytes.fromhex("4EB9") + (code + 16).to_bytes(4, "big"), expect=bytes.fromhex("1D7C00203005"),
              why="the title's set-up: black at once first")
    at = bytes(rom.data).find(ELEVATOR_PAL)
    assert at > 0 and bytes(rom.data).find(ELEVATOR_PAL, at + 1) < 0, "elevator-spin's palette copy not found"
    rom.write(at, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"), expect=ELEVATOR_PAL[:6],
              why="elevator-spin: its colours nowhere while the screen's black")
