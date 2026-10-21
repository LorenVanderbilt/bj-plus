import hashlib

NAME = "round-clear-dim"
DESCRIPTION = ("ROUND CLEAR: the frozen level dims to half while the stats are up, so the bonus lines are easy to read; "
               "and screen-blackout's last gaps (the story's last scene and its beam, back to the title, a room's way "
               "out, TODAY'S BEST 5 in the attract)")

# ROUND CLEAR's routines (ROUTINES: after the goal, after a boss - each called once, running the whole stats
# screen) draw its letters and bonus lines in the fix layer over the frozen level, and over the bells and leaves they
# were hard to read. Now, as a routine starts (its first call, hud's - hooked here), every palette but
# the text's (TEXT_PAL) is kept in BUF and eased down to DIM over STEPS steps
# (STEP_FRAMES frames each - half the palettes each frame: a step is too much work for one) each frame of the
# game's vblank wait (FRAME_LOOP). When the routine returns (its return address swapped for ours):
# after the goal (GOAL_RETURN) and the final boss (FINAL_RETURN) the dim stays - the next stage, the ending, loads its
# palettes; after another boss the level eases back up the same way, the last step the kept colours exactly (BOSS_DIM:
# False, no dim there at all). The frozen frame before the stats is shorter too (FREEZE).
# Each step scales each colour's 4-bit channels by a table (its low bits, bits 12-14, left out while dimmed; the dark
# bit kept). BUF is RAM a shop / NPC room keeps the level's objects in (0x10A800-0x10CFFF) - free at ROUND CLEAR.
# (Its own patch, last, so its code moves nothing.)
# Also screen-blackout's last gap: the story's last scene (STORY_LAST) loads no colours (it keeps the scene before's) so
# it couldn't be blacked out - its sprites came on as the screen was drawn (one torn frame). Now the colours are kept in
# BUF, the screen's blacked out like the other scenes (screen-blackout's story path) and BUF noted as a load: the
# reveal puts them back with the scene whole. And the third room's way out (ROOM_OUT3: the room at 0x130EC
# - its way in is screen-blackout's, its way out was missed; the attract demo's walk into it too) goes through
# screen-blackout's room_out like the others: the level shown whole after its first frames of play. elevator-spin's
# colour cycling (ELEVATOR_PAL) wrote its palette while black (the cone alone on the black screen): now, while black,
# into spare RAM. And the attract's TODAY'S BEST 5 (BEST_IN) is blacked out at a vblank as it starts (it came in in
# pieces), held, and shown whole as its loop starts (BEST_LOOP - the one after a game over too). And the title's set-up
# (TITLE_SETUP - the story over jumps into it): black at once first (the story's last frames were cleared in strips
# over their colours), the title shown whole by screen-blackout's fallback. And the last scene's cut to the beam
# (BEAM_CUT, as its last text box goes - story-last-line's hook there): its layers are redrawn over ~3 frames, so
# black first (the colours kept as for the scene's start) and shown whole once drawn.
# Also the C of ROUND CLEAR (C_TILES): its bottom curl's tip had a lone pixel sticking up - touched up (C_ART, the user's).
ROUTINES = [0x54CD0, 0x54FD8]  # jsr <hud's> ; nop - each ROUND CLEAR routine's first call
GOAL_RETURN = 0x11658          # (after the goal's routine: the dim stays - the next stage loads its palettes)
FINAL_RETURN = 0x36F94         # (after the final boss's: the dim stays too - the ending comes next)
BOSS_RETURN = 0x28E4C          # (after any other boss's: the level eases back up)
BOSS_DIM = True                # False: no dim after a boss (the final one aside) - e.g. for a victory dance there
FREEZE_WAIT = 0x11648          # move.w #48,d0 (then jsr 0xE858) - the stage's end: the frozen frame before the stats
FREEZE = 12                    # frames (was 48: with the 16 before it, over a second of freeze)
FRAME_LOOP = 0xE8AC            # move.w (sp)+,d0 ; dbf d0,0xE85C - the vblank wait's loop, once a frame (a long wait
                               # is one call: its end would come round once in hundreds of frames)
FRAME_LOOP_TOP, FRAME_LOOP_END = 0xE85C, 0xE8B2
DIM = 0.5
STEPS, STEP_FRAMES = 8, 2
FIRST_PAL, PALS = 0, 256
TEXT_PAL = 6                   # (the stats' text: fix palette 6 - left as it is; every other palette dims, the crowns' too)
BUF = 0x10B000                 # 256 x 32 bytes: to 0x10CFFF
C_TILES = [0x906, 0x907, 0x916, 0x917]  # fix tiles: the C's top left, top right, bottom left, bottom right (palette 6)
C_SHA = "8e6d755c"                 # (the original four)
C_ART = """
....ffffff..f...
...ff77777ff7ff.
..f666aaaa666faf
.f555aaafff55aaf
.f444aaf...f4aaf
f333aaaf....ffaf
f222aaf.......f.
f111aaf.........
f222aaf.........
f333aaf.........
.f444af.....f.f.
.f555aaf...f4faf
..f666affff55aaf
...ff66666666aaf
....fffaaaaa7faf
.......ffffff.f.
"""
STORY_LAST = (0x1552E, 0x3533E)  # jsr <screen-blackout's story_last> - its last scene; (the scene)
BLACKOUT_STORY2 = 60           # screen-blackout's jump table: its story's 3rd scene (pea <scene>; jsr 0xE856; bra blackout)
BLACKOUT_RAM = 0x10E600        # screen-blackout's REVEAL (+1), COUNT (+6), LIST (+16: 10 bytes a load), MAX_LOADS
BLACKOUT_COUNT, BLACKOUT_LIST, BLACKOUT_MAX = BLACKOUT_RAM + 6, BLACKOUT_RAM + 16, 16
BLACKOUT_REVEAL = BLACKOUT_RAM + 1  # (its REVEAL: shown at the next vblank)
ROOM_OUT3 = 0x1316A             # jsr 0x13660 - out of the room at 0x130EC: its sprites cleared, the level rebuilt
BLACKOUT_ROOM_OUT = 36          # screen-blackout's jump table: room_out
ELEVATOR_PAL = bytes.fromhex("41F900401EE2720E30D9")   # elevator-spin: lea 0x401EE2,a0 ; moveq #14,d1 ; move.w (a1)+,(a0)+
BLACKOUT_BLACK = BLACKOUT_RAM   # (its BLACK)
BEST_IN = 0x10854               # jsr 0x152FE (its music) - the attract's TODAY'S BEST 5 starting
BEST_LOOP = 0x549D0             # move.w #512,0x3800(a6) - TODAY'S BEST 5 set up, its loop starting
BEST_HOLD = 120                 # (frames screen-blackout's fallback waits, at most)
BLACKOUT_HOLD_AT = BLACKOUT_RAM + 8
BEAM_CUT = 0x35494              # jsr <story-last-line's> - the story's last scene: the beam's layers about to be drawn
TITLE_SETUP = 0x1AE76           # move.b #32,0x3005(a6) - the title being set up (the story over: bra here)
RAM = 0x10D500                 # spare RAM: ACTIVE (byte), DIR (byte: 1 down, -1 up, 0 holding), STEP (byte), HALF
ACTIVE, DIR, STEP, HALF, RET = RAM, RAM + 1, RAM + 2, RAM + 3, RAM + 4   # (byte), RET: the routine's return (long)
NOWHERE = RAM + 16              # (30 bytes: elevator-spin's colours while black)


def apply(rom):
    assert all(rom.u16(a) == 0x4EB9 for a in ROUTINES)
    hud = rom.u32(ROUTINES[0] + 2)
    assert rom.u32(ROUTINES[1] + 2) == hud
    tables = []
    for k in range(STEPS + 1):
        f = 1 - (1 - DIM) * k / STEPS
        s = [min(15, int(n * f + 0.5)) for n in range(16)]
        tables.append((bytes(s[b >> 4] << 4 | s[b & 15] for b in range(256)), bytes(s)))
    tab_src = "".join("tab%d_lo:\n    .byte %s\ntab%d_r:\n    .byte %s\n" % (
        k, ",".join(str(v) for v in lo), k, ",".join(str(v) for v in r)) for k, (lo, r) in enumerate(tables))
    blackout_code = rom.u32(STORY_LAST[0] + 2) - 64
    assert rom.u16(blackout_code + BLACKOUT_STORY2) == 0x6000
    d = rom.u16(blackout_code + BLACKOUT_STORY2 + 2)
    story2 = blackout_code + BLACKOUT_STORY2 + 2 + (d - 0x10000 if d & 0x8000 else d)
    assert rom.u16(story2) == 0x4879 and rom.u16(story2 + 6) == 0x4EB9, "screen-blackout's story path moved"
    bra = rom.u16(story2 + 12)        # bra blackout
    if bra == 0x6000:
        d = rom.u16(story2 + 14)
        blackout = story2 + 14 + (d - 0x10000 if d & 0x8000 else d)
    else:
        assert bra >> 8 == 0x60
        blackout = story2 + 14 + ((bra & 0xFF) - 0x100 if bra & 0x80 else bra & 0xFF)
    assert rom.u16(blackout) == 0x4A39, "screen-blackout's blackout moved"   # tst.b <BLACK>
    assert rom.u16(BEAM_CUT) == 0x4EB9
    beam_hook = rom.u32(BEAM_CUT + 2)
    code = rom.place_code("""
    bra.w entry                         | (+0)
    bra.w frame                         | (+4)
    bra.w story_last                    | (+8)
    bra.w elevator_pal                  | (+12)
    bra.w best_in                       | (+16)
    bra.w best_loop                     | (+20)
    bra.w title_setup                   | (+24)
    bra.w beam_cut                      | (+28)

| a ROUND CLEAR routine starting: the palettes kept, the dim on; its return swapped for ours
entry:
%(no_boss_dim)s
0:  movem.l %%d0/%%a0-%%a1,-(%%sp)
    lea 0x400000+%(first)d*32,%%a0
    lea 0x%(buf)X,%%a1
    move.w #%(longs)d-1,%%d0
1:  move.l (%%a0)+,(%%a1)+
    dbf %%d0,1b
    move.b #1,0x%(dir)X
    clr.b 0x%(step)X
    clr.b 0x%(half)X
    st 0x%(active)X
    movem.l (%%sp)+,%%d0/%%a0-%%a1
    move.l 4(%%sp),0x%(ret)X            | (the routine's own return: ours first)
    move.l #after,4(%%sp)
    jmp 0x%(hud)X

| the routine done: after the goal the dim stays (the next stage loads its palettes); after a boss, eased back up
after:
    move.l 0x%(ret)X,-(%%sp)
    cmpi.l #0x%(goal)X,(%%sp)
    beq 0f
    cmpi.l #0x%(final)X,(%%sp)
    bne 1f
0:  clr.b 0x%(active)X                  | (the dim stays)
    rts
1:  move.b #-1,0x%(dir)X
    rts

| the vblank wait's loop, a frame over (d1-a5 free: its caller's are kept): the dim on by half a step
frame:
    move.w (%%sp)+,%%d0
    bsr tick
    dbf %%d0,1f
    jmp 0x%(loop_end)X
1:  jmp 0x%(loop_top)X

tick:
    tst.b 0x%(active)X
    beq 9f
    move.b 0x%(dir)X,%%d1
    beq 9f
    moveq #0,%%d2
    move.b 0x%(step)X,%%d2              | d2 = the step to show
    tst.b %%d1
    bmi 1f
    cmpi.b #%(steps)d,%%d2
    bcc 9f                              | (all the way down: holding)
    addq.w #1,%%d2
    bra 2f
1:  tst.b %%d2
    beq 8f                              | (all the way back: off)
    subq.w #1,%%d2
2:  moveq #0,%%d3                       | this frame's half
    move.b 0x%(half)X,%%d3
    mulu #%(half_bytes)d,%%d3
    lea 0x%(buf)X,%%a0
    adda.l %%d3,%%a0
    lea 0x400000+%(first)d*32,%%a1
    adda.l %%d3,%%a1
    move.w #%(half_pals)d-1,%%d4        | the half's palettes
    moveq #0,%%d1
    move.b 0x%(half)X,%%d1
    mulu #%(half_pals)d,%%d1            | d1 = the first's number
    lea tables(%%pc),%%a2
    move.w %%d2,%%d3
    lsl.w #3,%%d3
    movea.l (%%a2,%%d3.w),%%a3          | the step's low-byte table
    movea.l 4(%%a2,%%d3.w),%%a4         | ... its red table
3:  moveq #15,%%d3
    tst.w %%d2                          | (step 0, or the text's palette: the kept colours exactly)
    beq 4f
    cmpi.w #%(text_pal)d,%%d1
    bne 5f
4:  move.w (%%a0)+,(%%a1)+
    dbf %%d3,4b
    bra 7f
5:  move.w (%%a0)+,%%d5
    moveq #0,%%d6
    move.b %%d5,%%d6
    move.b (%%a3,%%d6.w),%%d6           | green, blue
    move.w %%d5,%%d7
    lsr.w #8,%%d7
    andi.w #15,%%d7
    move.b (%%a4,%%d7.w),%%d7           | red
    lsl.w #8,%%d7
    or.w %%d7,%%d6
    andi.w #0x8000,%%d5                 | (the dark bit kept; the low bits left out)
    or.w %%d6,%%d5
    move.w %%d5,(%%a1)+
    dbf %%d3,5b
7:  addq.w #1,%%d1
    dbf %%d4,3b
6:  addq.b #1,0x%(half)X                | both halves done: the step's done
    cmpi.b #%(halves)d,0x%(half)X
    bcs 9f
    clr.b 0x%(half)X
    move.b %%d2,0x%(step)X
    bra 9f
8:  clr.b 0x%(active)X
9:  rts

| the story's last scene: its colours kept, then black (the screen-blackout's way) and the kept colours noted as a load
story_last:
    bsr keep_colours
    pea 0x%(scene_last)X
    pea story_noted(%%pc)
    jmp 0x%(story_black)X               | (a vblank, black: its rts to story_noted)

| the beam's cut in the last scene: the same - black while its layers are drawn
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
    move.l #0x400000,(%%a0)+            | (to: every palette)
    move.l #0x%(buf)X,(%%a0)+           | (from: the kept colours)
    move.w #255,(%%a0)
    move.b #1,0x%(b_reveal)X            | (shown at its first vblank wait: the scene's set up whole before it)
1:  movem.l (%%sp)+,%%d0/%%a0
    rts                                 | (into the scene)

| elevator-spin's colours: into palette 0xF7 - while black, nowhere
elevator_pal:
    lea 0x401EE2,%%a0
    tst.b 0x%(b_black)X
    beq 1f
    lea 0x%(nowhere)X,%%a0
1:  rts

| the attract's TODAY'S BEST 5 starting: black at once (at a vblank)
best_in:
    jsr 0xE856
    jsr 0x%(blackout)X
    move.w #%(best_hold)d,0x%(b_hold_at)X
    jmp 0x152FE

| TODAY'S BEST 5 set up: shown at its loop's first vblank
best_loop:
    move.w #512,0x3800(%%a6)
    tst.b 0x%(b_black)X
    beq 1f
    move.b #1,0x%(b_reveal)X
1:  rts

| the title being set up: black at once (at a vblank) first
title_setup:
    jsr 0xE856
    jsr 0x%(blackout)X
    move.b #32,0x3005(%%a6)
    rts

tables:
    .long %(table_ptrs)s
%(tab_src)s
    .even
""" % {"first": FIRST_PAL, "buf": BUF, "longs": PALS * 8, "dir": DIR, "step": STEP, "half": HALF, "active": ACTIVE,
       "ret": RET, "hud": hud, "goal": GOAL_RETURN, "final": FINAL_RETURN, "no_boss_dim": "" if BOSS_DIM else
       "    cmpi.l #0x%X,4(%%sp)              | (no dim after a boss: switched off)\n    bne 0f\n    jmp 0x%X" % (BOSS_RETURN, hud), "steps": STEPS, "half_bytes": PALS * 32 // STEP_FRAMES,
       "half_pals": PALS // STEP_FRAMES, "text_pal": TEXT_PAL, "halves": STEP_FRAMES, "loop_top": FRAME_LOOP_TOP, "loop_end": FRAME_LOOP_END,
       "table_ptrs": ",".join("tab%d_lo,tab%d_r" % (k, k) for k in range(STEPS + 1)), "tab_src": tab_src,
       "scene_last": STORY_LAST[1], "story_black": story2 + 6, "b_count": BLACKOUT_COUNT, "b_list": BLACKOUT_LIST,
       "b_max": BLACKOUT_MAX, "b_reveal": BLACKOUT_REVEAL, "b_black": BLACKOUT_BLACK,
       "nowhere": NOWHERE, "blackout": blackout, "best_hold": BEST_HOLD, "beam_hook": beam_hook,
       "b_hold_at": BLACKOUT_HOLD_AT},
        why="ROUND CLEAR: the level dimmed behind the stats")
    rom.write(FREEZE_WAIT, bytes.fromhex("303C") + FREEZE.to_bytes(2, "big"), expect=bytes.fromhex("303C0030"),
              why="the stage's end: a shorter freeze before ROUND CLEAR")
    for at in ROUTINES:
        rom.write(at + 2, code.to_bytes(4, "big"), expect=hud.to_bytes(4, "big"), why="ROUND CLEAR: the dim on")
    rom.write(FRAME_LOOP, bytes.fromhex("4EF9") + (code + 4).to_bytes(4, "big"), expect=bytes.fromhex("301F51C8FFAC"),
              why="vblank wait, each frame: ROUND CLEAR's dim")
    rom.write(STORY_LAST[0] + 2, (code + 8).to_bytes(4, "big"), expect=(blackout_code + 64).to_bytes(4, "big"),
              why="story cinema: its last scene blacked out too")
    rom.write(ROOM_OUT3 + 2, (blackout_code + BLACKOUT_ROOM_OUT).to_bytes(4, "big"), expect=(0x13660).to_bytes(4, "big"),
              why="out of the room at 0x130EC: black at once, the level shown whole")
    rom.write(BEST_IN, bytes.fromhex("4EB9") + (code + 16).to_bytes(4, "big"), expect=bytes.fromhex("4EB9000152FE"),
              why="attract: TODAY'S BEST 5 blacked out at once")
    rom.write(BEST_LOOP, bytes.fromhex("4EB9") + (code + 20).to_bytes(4, "big"), expect=bytes.fromhex("3D7C02003800"),
              why="TODAY'S BEST 5: shown whole as its loop starts")
    rom.write(BEAM_CUT + 2, (code + 28).to_bytes(4, "big"), expect=beam_hook.to_bytes(4, "big"),
              why="story: the beam's cut blacked out while its layers are drawn")
    rom.write(TITLE_SETUP, bytes.fromhex("4EB9") + (code + 24).to_bytes(4, "big"), expect=bytes.fromhex("1D7C00203005"),
              why="the title's set-up: black at once first")
    at = bytes(rom.data).find(ELEVATOR_PAL)
    assert at > 0 and bytes(rom.data).find(ELEVATOR_PAL, at + 1) < 0, "elevator-spin's palette copy not found"
    rom.write(at, bytes.fromhex("4EB9") + (code + 12).to_bytes(4, "big"), expect=ELEVATOR_PAL[:6],
              why="elevator-spin: its colours nowhere while the screen's black")
    old = b"".join(bytes(rom.fix[t * 32:t * 32 + 32]) for t in C_TILES)
    assert hashlib.sha1(old).hexdigest()[:8] == C_SHA, "ROUND CLEAR's C: not the original tiles"
    art = [[int(c, 16) if c != "." else 0 for c in row] for row in C_ART.split()]
    for n, t in enumerate(C_TILES):
        rom.fix[t * 32:t * 32 + 32] = bytes(32)
        for y in range(8):
            for x in range(8):
                b = rom.FIX_COLUMN_BYTE[x] + y
                rom.fix[t * 32 + b] |= (art[n // 2 * 8 + y][n % 2 * 8 + x] & 15) << (0 if x % 2 == 0 else 4)
    rom.log.append("  fix 0x%03X-0x%03X  tiles  ROUND CLEAR's C: touched up" % (C_TILES[0], C_TILES[-1]))
