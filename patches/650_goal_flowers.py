NAME = "goal-flowers"
DESCRIPTION = "Hit the goal vine at the very top (its top score) and flowers sprout from the ground around it"

# The goal vine's touch (TOUCH: jsr 0x5E036 first, a5 = the segment touched) scores by the segment's height, 0x5F(a5)
# - TOP (9) is the top score, 7770. There it now also spawns FLOWERS: the pink currency flower (frame 0x209C - in every
# stage's palettes), on the ground (GROUND below the goal's base, BASE: its y / x, as the score
# popup uses it) either side of the vine. Each lies flat on the ground from the touch (vertical shrink +0x27 at 0:
# a 1-pixel line, full width), waits its delay, then stretches up through ZOOMS - the hero's crush in reverse - out
# of the ground, a little bounce at the end - and stays till the stage ends. It never moves: the drawer keeps a
# shrunken sprite's bottom where the full-size one's is (its y is the full-size top, GROUND below the base).
# (Its own patch, last, so its code moves nothing.)
ENABLED = False                # set aside (2026-10-18): the user isn't sold on it yet - True to try it again
TOUCH = 0x52994                # jsr 0x5E036
TOUCH_FIRST = 0x5E036
HEIGHT, TOP = 0x5F, 9
ALLOCATE = 0xFFEC              # a free object in a1 (ne: none)
BASE = 0x103C08                # the goal's base: y, x (128 a pixel; y upwards)
GROUND = -0x100                # a flower's top at full size, below the base (its foot 16 px lower, on the grass)
PRIORITY = 0x7F                # +0x28: drawn as the crowns are
PINK = 0x209C
# (x from the base in pixels, delay in frames, frame) - one object each: the goal's sparkles take most of the rest
FLOWERS = [(-28, 0, PINK), (28, 3, PINK), (-47, 6, PINK), (46, 9, PINK), (-68, 12, PINK), (66, 15, PINK),
           (-86, 18, PINK), (88, 21, PINK), (-108, 24, PINK), (106, 27, PINK)]
GROW = [0, 40, 78, 112, 142, 168, 190, 208, 222, 234, 244, 250, 255]
BOUNCE = [246, 234, 224, 218, 220, 228, 240, 250, 255]
ZOOMS = GROW + BOUNCE
WAIT, STEP = 0x50, 0x54       # the flower's own fields: delay, step


def apply(rom):
    if not ENABLED:
        return
    assert rom.u16(TOUCH) == 0x4EB9 and rom.u32(TOUCH + 2) == TOUCH_FIRST
    flower = rom.place_code("""
    movem.l %%d0/%%a0,-(%%sp)
    tst.w %(wait)d(%%a5)                | waiting its turn
    beq 1f
    subq.w #1,%(wait)d(%%a5)
    bra 9f
1:  move.w %(step)d(%%a5),%%d0
    cmpi.w #%(last)d,%%d0
    bcc 2f                              | (grown: holds the last)
    addq.w #1,%(step)d(%%a5)
2:  lea zooms(%%pc),%%a0
    move.b (%%a0,%%d0.w),0x27(%%a5)
9:  movem.l (%%sp)+,%%d0/%%a0
    rts
zooms:
    .byte %(zooms)s
""" % {"wait": WAIT, "step": STEP, "last": len(ZOOMS) - 1,
       "zooms": ",".join(str(z) for z in ZOOMS)},
        why="goal flowers: one growing out of the ground")
    hook = rom.place_code("""
    jsr 0x%(first)X
    cmpi.b #%(top)d,%(height)d(%%a5)
    bne 9f
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    lea flowers(%%pc),%%a3
    moveq #%(count)d,%%d7
1:  movem.l %%d7/%%a3,-(%%sp)
    jsr 0x%(allocate)X
    movem.l (%%sp)+,%%d7/%%a3
    bne 8f                              | (no free object)
    move.w 0x%(base)X,%%d0
    subi.w #%(ground)d,%%d0
    move.w %%d0,(%%a1)
    move.w 0x%(base)X+2,%%d0
    add.w (%%a3)+,%%d0
    move.w %%d0,2(%%a1)
    move.l #0x%(flower)X,4(%%a1)
    move.w (%%a3)+,%(wait)d(%%a1)
    move.w (%%a3)+,8(%%a1)              | its frame, flat till its turn
    clr.w %(step)d(%%a1)
    clr.b 0x20(%%a1)
    move.b #6,0x21(%%a1)
    st 0x26(%%a1)                       | full width throughout
    clr.b 0x27(%%a1)
    move.b #0x%(priority)X,0x28(%%a1)
    dbf %%d7,1b
8:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
9:  rts
flowers:
    .word %(flowers)s
""" % {"first": TOUCH_FIRST, "top": TOP, "height": HEIGHT, "count": len(FLOWERS) - 1, "allocate": ALLOCATE,
       "base": BASE, "ground": GROUND, "flower": flower, "wait": WAIT, "step": STEP,
       "priority": PRIORITY,
       "flowers": ",".join("%d,%d,0x%X" % ((dx * 128) & 0xFFFF, delay, frame) for dx, delay, frame in FLOWERS)},
        why="goal flowers: spawned at a top-score touch")
    rom.write(TOUCH, bytes.fromhex("4EB9") + hook.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + TOUCH_FIRST.to_bytes(4, "big"), why="goal: flowers at its top score")
