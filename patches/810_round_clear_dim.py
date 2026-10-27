import hashlib

NAME = "round-clear-dim"
DESCRIPTION = "ROUND CLEAR: the frozen level dims to half while the stats are up, so the bonus lines are easy to read"

# ROUND CLEAR's routines (ROUTINES: after the goal, after a boss - each called once, running the whole stats
# screen) draw its letters and bonus lines in the fix layer over the frozen level, and over the bells and leaves they
# were hard to read. Now, as a routine starts (its first call, hud's - hooked here), every palette but the text's
# (TEXT_PAL) is kept in BUF and eased down to DIM over STEPS steps (STEP_FRAMES frames each - half the palettes each
# frame: a step is too much work for one) each frame of the game's vblank wait (FRAME_LOOP - tunnel-life-ball and
# wall-light-keep run there too, before this). When the routine returns (its return address swapped for ours):
# after the goal (GOAL_RETURN) and the final boss (FINAL_RETURN) the dim stays - the next stage, the ending, loads its
# palettes; after another boss the level eases back up the same way, the last step the kept colours exactly (BOSS_DIM:
# False, no dim there at all). The frozen frame before the stats is shorter too (FREEZE).
# Each step scales each colour's 4-bit channels by a table (its low bits, bits 12-14, left out while dimmed; the dark
# bit kept). BUF is RAM a shop / NPC room keeps the level's objects in (0x10A800-0x10CFFF) - free at ROUND CLEAR.
# Also the C of ROUND CLEAR (C_TILES): its bottom curl's tip had a lone pixel sticking up - touched up (C_ART, the
# user's).
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
TEXT_PAL = 6                   # (the stats' text: fix palette 6 - left as it is; every other palette dims, the
                               # crowns' too)
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
RAM = 0x10D500                 # spare RAM: ACTIVE (byte), DIR (byte: 1 down, -1 up, 0 holding), STEP (byte), HALF
ACTIVE, DIR, STEP, HALF, RET = RAM, RAM + 1, RAM + 2, RAM + 3, RAM + 4   # (byte), RET: the routine's return (long)


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
    no_boss_dim = "" if BOSS_DIM else """
    cmpi.l #0x%X,4(%%sp)              | (no dim after a boss: switched off)
    bne 0f
    jmp 0x%X""" % (BOSS_RETURN, hud)
    code = rom.place_code("""
    bra.w entry                         | (+0)
    bra.w frame                         | (+4)

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

tables:
    .long %(table_ptrs)s
%(tab_src)s
    .even
""" % {"first": FIRST_PAL, "buf": BUF, "longs": PALS * 8, "dir": DIR, "step": STEP, "half": HALF, "active": ACTIVE,
       "ret": RET, "hud": hud, "goal": GOAL_RETURN, "final": FINAL_RETURN, "no_boss_dim": no_boss_dim,
       "steps": STEPS, "half_bytes": PALS * 32 // STEP_FRAMES, "half_pals": PALS // STEP_FRAMES, "text_pal": TEXT_PAL,
       "halves": STEP_FRAMES, "loop_top": FRAME_LOOP_TOP, "loop_end": FRAME_LOOP_END,
       "table_ptrs": ",".join("tab%d_lo,tab%d_r" % (k, k) for k in range(STEPS + 1)), "tab_src": tab_src},
        why="ROUND CLEAR: the level dimmed behind the stats")
    rom.write(FREEZE_WAIT, bytes.fromhex("303C") + FREEZE.to_bytes(2, "big"), expect=bytes.fromhex("303C0030"),
              why="the stage's end: a shorter freeze before ROUND CLEAR")
    for at in ROUTINES:
        rom.write(at + 2, code.to_bytes(4, "big"), expect=hud.to_bytes(4, "big"), why="ROUND CLEAR: the dim on")
    rom.write(FRAME_LOOP, bytes.fromhex("4EF9") + (code + 4).to_bytes(4, "big"), expect=bytes.fromhex("301F51C8FFAC"),
              why="vblank wait, each frame: ROUND CLEAR's dim")
    old = b"".join(bytes(rom.fix[t * 32:t * 32 + 32]) for t in C_TILES)
    assert hashlib.sha1(old).hexdigest()[:8] == C_SHA, "ROUND CLEAR's C: not the original tiles"
    art = [[int(c, 16) if c != "." else 0 for c in row] for row in C_ART.split()]
    for n, t in enumerate(C_TILES):
        rom.replace_fix_tile(t, [row[n % 2 * 8:n % 2 * 8 + 8] for row in art[n // 2 * 8:n // 2 * 8 + 8]],
                             why="ROUND CLEAR's C: touched up")
