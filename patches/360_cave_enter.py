NAME = "cave-enter"
DESCRIPTION = "Boss caves: once the hook is pulled, Blue walks on into the dark mouth, fading into its shadow, as the stage ends"

# After the PULL hook (see sta/aes/cave_enter.sta), Blue walks to the cave at the end of the stage and stands in front
# of its dark mouth while the stage ends, fully lit and drawn over the dark. The stage end (mode 2, 0x11622) is a
# script of waits during which no objects run. For a world's third act (stage < 0x21 and stage & 3 = 3, the boss
# cave) it's a 16-frame wait, a sound, another wait (WAITS), then the next stage.
#
# Those waits now go a frame at a time, and for a third act with the goal pulled (0x103C0C), each frame:
#   * each hero in the game moves WALK_ON / 128 px further in, with his walk animated (ANIMATE);
#   * every FADE_EVERY frames, the heroes' palettes (0x10 / 0x11) step one unit per 5-bit channel toward the mouth's
#     dark (DARK), so he fades into the shadow. The next stage loads them afresh.
WAITS = [0x1162A, 0x11672]   # move.w #16,d0 ; jsr 0xE858, which waits d0 frames
WAIT_FRAME = 0xE856
STAGE = 0x3005               # from a6
GOAL_PULLED = 0x3C0C         # from a6
HEROES = [(0x104000, 0), (0x104080, 1)]      # hero, its bit in 0x106808 when in the game
PLAYERS_IN = 0x106808
PALETTES = [0x10, 0x11]
WALK_ON = 96                 # 1/128 px a frame, so 0.75 px; over the 32 frames of waits, about 24 px in
ANIMATE = 0x434A8            # steps object a5's animation one frame, since no objects run in the stage end
FADE_EVERY = 2               # frames a step
DARK = (1, 2, 9)             # the mouth's dark navy, 5-bit r, g, b
FRAME = 0x100206


def apply(rom):
    walks = "".join("    btst #%d,0x%X\n    beq 1f\n    addi.w #%d,0x%X\n    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)\n"
                    "    lea 0x%X,%%a5\n    jsr 0x%X\n    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6\n1:\n"
                    % (bit, PLAYERS_IN, WALK_ON, hero + 2, hero, ANIMATE) for hero, bit in HEROES)
    code = rom.place_code(r"""
    move.l %%d7,-(%%sp)                  | the stage end's 16-frame waits, a frame at a time
    moveq #15,%%d7
20: jsr 0x%(wait_frame)X
    move.b 0x%(stage)X(%%a6),%%d0       | with a step in each frame after a third act's goal is pulled
    cmp.b #0x21,%%d0
    bcc 21f
    and.b #3,%%d0
    cmp.b #3,%%d0
    bne 21f
    tst.b 0x%(pulled)X(%%a6)
    beq 21f
    bsr step
21: dbf %%d7,20b
    move.l (%%sp)+,%%d7
    rts

step:
    movem.l %%d0-%%d6/%%a0,-(%%sp)
%(walks)s
    move.w 0x%(frame)X,%%d0             | the fade: a step every FADE_EVERY frames
    and.w #%(every)d-1,%%d0
    bne 8f
    lea 0x400000+%(pal0)d*32+2,%%a0     | both heroes' palettes, one after the other
    moveq #%(colours)d-1,%%d6
2:  move.w (%%a0),%%d0
    move.w %%d0,%%d1                    | r: bits 11-8, then bit 14
    lsr.w #7,%%d1
    and.w #0x1E,%%d1
    btst #14,%%d0
    beq 3f
    addq.w #1,%%d1
3:  moveq #%(r)d,%%d2
    bsr toward
    move.w %%d1,%%d3
    move.w %%d0,%%d1                    | g: bits 7-4, then bit 13
    lsr.w #3,%%d1
    and.w #0x1E,%%d1
    btst #13,%%d0
    beq 4f
    addq.w #1,%%d1
4:  moveq #%(g)d,%%d2
    bsr toward
    move.w %%d1,%%d4
    move.w %%d0,%%d1                    | b: bits 3-0, then bit 12
    add.w %%d1,%%d1
    and.w #0x1E,%%d1
    btst #12,%%d0
    beq 5f
    addq.w #1,%%d1
5:  moveq #%(b)d,%%d2
    bsr toward
    move.w %%d1,%%d5
    and.w #0x8000,%%d0                  | keep the dark bit, then repack
    move.w %%d3,%%d1
    lsr.w #1,%%d1
    lsl.w #8,%%d1
    or.w %%d1,%%d0
    move.w %%d4,%%d1
    lsr.w #1,%%d1
    lsl.w #4,%%d1
    or.w %%d1,%%d0
    move.w %%d5,%%d1
    lsr.w #1,%%d1
    or.w %%d1,%%d0
    btst #0,%%d3
    beq 6f
    bset #14,%%d0
6:  btst #0,%%d4
    beq 7f
    bset #13,%%d0
7:  btst #0,%%d5
    beq 10f
    bset #12,%%d0
10: move.w %%d0,(%%a0)+
    cmp.w #15,%%d6                      | after the first palette's 15, skip the second's colour 0
    bne 11f
    addq.l #2,%%a0
11: dbf %%d6,2b
8:  movem.l (%%sp)+,%%d0-%%d6/%%a0
    rts

toward:                                 | move d1 one unit toward d2
    cmp.w %%d2,%%d1
    beq 1f
    bcs 2f
    subq.w #1,%%d1
    rts
2:  addq.w #1,%%d1
1:  rts
""" % {"pulled": GOAL_PULLED, "wait_frame": WAIT_FRAME, "stage": STAGE, "walks": walks, "frame": FRAME,
       "every": FADE_EVERY, "pal0": PALETTES[0], "colours": 30, "r": DARK[0], "g": DARK[1], "b": DARK[2]},
        why="boss cave: Blue walks on into the dark, fading")
    for at in WAITS:
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
                  expect=bytes.fromhex("303C00104EB90000E858"), why="stage end: its wait a frame at a time (the cave walk)")
