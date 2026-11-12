import hashlib
import os

from png_tiles import neo_to_rgb, read_indices

NAME = "round-clear-dim"
DESCRIPTION = "ROUND CLEAR: the frozen level dims to half while the stats are up, so the bonus lines are easy to read"

# The two ROUND CLEAR routines (ROUTINES: after the goal and after a boss) are each called once and run the whole
# stats screen. They draw the letters and bonus lines on the fix layer over the frozen level, where they were hard to
# read over the bells and leaves.
#
# When a routine starts (at its first call, hud's, which is hooked here), every palette except the text's (TEXT_PAL)
# is saved to BUF (by palette-timing, a quarter in each of the next four vblanks, which then starts the dim: read
# while the picture was drawn, palette RAM flashed snow on real hardware - 2026-11-11) and eased down to DIM over STEPS steps of STEP_FRAMES frames. That happens in the game's vblank wait
# (FRAME_LOOP, after tunnel-life-ball and wall-light-keep), half the palettes per frame, since a whole step is too
# much work for one frame. The routine's return address is swapped for ours. After the goal (GOAL_RETURN) and the
# final boss (FINAL_RETURN) the dim stays, since the next stage or the ending loads its own palettes. After any other
# boss the level eases back up the same way, ending on the saved colours exactly. BOSS_DIM = False turns off the dim
# after bosses. The frozen pause before the stats is shorter too (FREEZE).
#
# Each step scales a colour's 4-bit channels through a table. The low bits (12-14) are dropped while dimmed and the
# dark bit is kept. BUF is RAM that shops and NPC rooms use to store the level's objects (0x10A800-0x10CFFF), free
# at ROUND CLEAR.
#
# The C of ROUND CLEAR (C_TILES) had a stray pixel sticking up from the tip of its bottom curl. It's drawn from C_ART,
# a 16x16 PNG in the C's palette (C_COLOURS, fix palette 6; c_reference.png next to it is the original, kept local).
ROUTINES = [0x54CD0, 0x54FD8]  # jsr <hud> ; nop: each ROUND CLEAR routine's first call
GOAL_RETURN = 0x11658          # after the goal: the dim stays, the next stage loads its palettes
FINAL_RETURN = 0x36F94         # after the final boss: the dim stays, the ending is next
BOSS_RETURN = 0x28E4C          # after any other boss: the level eases back up
BOSS_DIM = True                # False: no dim after a boss other than the final one, e.g. for a victory dance
FREEZE_WAIT = 0x11648          # move.w #48,d0, then jsr 0xE858: the frozen pause before the stats
FREEZE = 12                    # frames; 48 plus the 16 before it froze for over a second
FRAME_LOOP = 0xE8AC            # move.w (sp)+,d0 ; dbf d0,0xE85C: the vblank wait's loop, once a frame. Hooking the
                               # wait's end wouldn't do, since one long wait can last hundreds of frames
FRAME_LOOP_TOP, FRAME_LOOP_END = 0xE85C, 0xE8B2
DIM = 0.5
STEPS, STEP_FRAMES = 8, 2
FIRST_PAL, PALS = 0, 256
TEXT_PAL = 6                   # fix palette 6, the stats' text, isn't dimmed; every other palette is, the
                               # crowns' too
BUF = 0x10B000                 # 256 x 32 bytes, to 0x10CFFF
C_TILES = [0x906, 0x907, 0x916, 0x917]  # fix tiles of the C: top left, top right, bottom left, bottom right
C_SHA = "8e6d755c"                 # the original four tiles
C_ART = "art/round_clear/c.png"
C_COLOURS = [0xA080, 0xFFFF, 0xEFFB, 0x9FF6, 0x8FF2, 0xAFD2, 0x9FC1, 0xBFA1, 0x8F91, 0xAF81, 0x8F71, 0xDE50, 0xFE30,
             0xAE10, 0x8E00, 0x8000]   # fix palette 6 (index 0 clear)
RAM = 0x10D500                 # spare RAM: ACTIVE, DIR (1 down, -1 up, 0 holding), STEP, HALF (bytes)
ACTIVE, DIR, STEP, HALF, RET = RAM, RAM + 1, RAM + 2, RAM + 3, RAM + 4   # RET: the routine's return address (long)
SAVING, SAVE_PARTS = RAM + 8, 4    # quarters of the palettes still to save to BUF (a byte): palette-timing saves
                                   # one a vblank, then sets ACTIVE


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
    cmpi.l #0x%X,4(%%sp)              | no dim after a boss: switched off
    bne 0f
    jmp 0x%X""" % (BOSS_RETURN, hud)
    code = rom.place_code("""
    bra.w entry                         | +0
    bra.w frame                         | +4

| a ROUND CLEAR routine starting: save the palettes, start the dim, and take over its return
entry:
%(no_boss_dim)s
0:  movem.l %%d0/%%a0-%%a1,-(%%sp)
    move.b #%(save_parts)d,0x%(saving)X     | the palettes saved to BUF in the next vblanks (palette-timing)
    nop                                 | (as long as the copy it replaced: the code after keeps its place, for
    nop                                 | saves made with RET pointing at after)
    nop
    nop
    nop
    nop
    nop
    move.b #1,0x%(dir)X
    clr.b 0x%(step)X
    clr.b 0x%(half)X
    nop                                 | (ACTIVE is set once the palettes are saved: palette-timing)
    nop
    nop
    movem.l (%%sp)+,%%d0/%%a0-%%a1
    move.l 4(%%sp),0x%(ret)X            | its own return, which ours goes on to
    move.l #after,4(%%sp)
    jmp 0x%(hud)X

| the routine done: after the goal the dim stays (the next stage loads its palettes); after a boss, ease back up
after:
    move.l 0x%(ret)X,-(%%sp)
    cmpi.l #0x%(goal)X,(%%sp)
    beq 0f
    cmpi.l #0x%(final)X,(%%sp)
    bne 1f
0:  clr.b 0x%(active)X                  | the dim stays
    rts
1:  move.b #-1,0x%(dir)X
    rts

| once a frame from the vblank wait (d1-a5 free; the caller's are saved): move the dim on by half a step
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
    bcc 9f                              | all the way down: hold
    addq.w #1,%%d2
    bra 2f
1:  tst.b %%d2
    beq 8f                              | all the way back up: done
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
    mulu #%(half_pals)d,%%d1            | d1 = the first one's number
    lea tables(%%pc),%%a2
    move.w %%d2,%%d3
    lsl.w #3,%%d3
    movea.l (%%a2,%%d3.w),%%a3          | the step's low-byte table
    movea.l 4(%%a2,%%d3.w),%%a4         | and its red table
3:  moveq #15,%%d3
    tst.w %%d2                          | step 0, or the text's palette: the saved colours exactly
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
    andi.w #0x8000,%%d5                 | keep the dark bit, drop the low bits
    or.w %%d6,%%d5
    move.w %%d5,(%%a1)+
    dbf %%d3,5b
7:  addq.w #1,%%d1
    dbf %%d4,3b
6:  addq.b #1,0x%(half)X                | both halves done: the step is done
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
       "ret": RET, "hud": hud, "saving": SAVING, "save_parts": SAVE_PARTS, "goal": GOAL_RETURN, "final": FINAL_RETURN, "no_boss_dim": no_boss_dim,
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
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    art = read_indices(os.path.join(root, C_ART), [neo_to_rgb(c) for c in C_COLOURS])
    assert (len(art[0]), len(art)) == (16, 16), "%s: not 16 x 16" % C_ART
    for n, t in enumerate(C_TILES):
        if [row[n % 2 * 8:n % 2 * 8 + 8] for row in art[n // 2 * 8:n // 2 * 8 + 8]] == rom.fix_tile(t):
            continue
        rom.replace_fix_tile(t, [row[n % 2 * 8:n % 2 * 8 + 8] for row in art[n // 2 * 8:n // 2 * 8 + 8]],
                             why="ROUND CLEAR's C: touched up")
