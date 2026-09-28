NAME = "vine-slide"
DESCRIPTION = "Swinging vines: hold Up / Down to slide smoothly along the vine"

# A swinging vine is a root object at the pivot plus a chain of segment objects (code 0x4FD30), each with its
# distance from the pivot at +56 (0, 6, 12 ...) and moving with the swing. The hero hangs from one segment:
# player 1's attach flag is that segment's +52 (player 2's +53), 1 (shrunk hero) or 2 while holding, negative
# while letting go; every frame the segment code
# (0x4FD82) calls 0x4FE72 (player 1) / 0x4FEEE (player 2), which puts the hero at that segment's position plus
# a fixed offset. Grabbing picks the segment touched - normally the bottom one - and the hero stays there.
#
# Both routines start with `move.l (a5),hero` (6 bytes); that is now a call to `slide`. Pressing Up / Down
# starts a step toward the next segment up / down the same vine (found by distance +-6 and closeness to the
# current one); over UP_RATE / DOWN_RATE frames the hero's position is blended from the current segment to that one, and
# at the end the attach flag is handed over (after the game's routine has added its hanging offset, which
# it only does while the calling segment still has the flag). A step in progress always finishes; while the button is still
# held the next one starts straight away. It stops at the bottom segment and at MIN_DISTANCE from the pivot.
# Only vine segments with a "holding" value are touched, so letting go works as before.
SITES = [(0x4FE72, "2D6D00004000", 52, 0x10FD96, 0x104000), (0x4FEEE, "2D6D00004080", 53, 0x10FD9C, 0x104080)]
SEGMENT_CODE = 0x4FD30
STEP = 6                  # distance between segments (+56)
MIN_DISTANCE = 6          # don't slide right up to the pivot
UP_RATE = 10              # frames per segment climbing up
DOWN_RATE = 6             # and sliding down
NEAR = 0x1000             # a neighbouring segment of the same vine is within 16 px
RAM = 0x10EA04            # spare RAM, 4 bytes per player: segment (low word), step direction, step progress
LAST_FRAME = 0x10EA0C     # and one byte per player: the frame counter's low byte when it last moved


def apply(rom):
    for n, (site, orig, flag, joy, hero) in enumerate(SITES):
        src = r"""
| a5 = the segment holding this player's hero. RAM: +0 word = that segment (low word of its address, to spot a
| new grab), +2 = step direction (0 none, 1 up, 2 down), +3 = frames into the step.
    movem.l %d0-%d4/%a0-%a2,-(%sp)
    move.l (%a5),%d4                | d4 = where the hero goes: the segment's position (y, x) ...
    cmp.l #SEGMENT_CODE,4(%a5)
    bne done
    tst.b FLAG(%a5)                 | holding: 1 (shrunk) or 2 (normal); 0 / negative = not holding / letting go
    ble done
    lea RAM,%a1
    move.b 0x100207,%d0             | at most one step of progress per frame (going down, the segment it was
    cmp.b LAST(%a1),%d0             | handed to runs again later in the same frame)
    beq done
    move.b %d0,LAST(%a1)
    move.w %a5,%d0
    cmp.w (%a1),%d0
    beq 1f
    move.w %d0,(%a1)                | a different segment than last time (a new grab): no step going on
    clr.w 2(%a1)
1:  tst.b 2(%a1)
    bne 2f
    move.b JOY,%d0                  | no step going on: start one if Up (bit 0) or Down (bit 1) is held
    and.b #3,%d0
    beq done
    moveq #1,%d1
    btst #0,%d0
    bne 11f
    moveq #2,%d1
11: move.b %d1,2(%a1)
    clr.b 3(%a1)
2:  bsr neighbour                   | a2 = the segment the step goes to
    bne 3f
    clr.w 2(%a1)                    | none (end of the vine): stop
    bra done
3:  addq.b #1,3(%a1)
    moveq #UP_RATE,%d3              | d3 = frames per segment in this step's direction
    cmp.b #1,2(%a1)
    beq 14f
    moveq #DOWN_RATE,%d3
14: cmp.b 3(%a1),%d3
    bhi 4f
    move.b FLAG(%a5),FLAG(%a2)      | step done: hand the hero over to that segment
    move.w %a2,(%a1)
    clr.w 2(%a1)
    move.l (%a2),%d4
    move.l %d4,HERO
    movem.l (%sp)+,%d0-%d4/%a0-%a2
    addq.l #4,%sp                   | the rest of the game's routine (hanging offset) runs now, while this
    jsr TAIL                        | segment still has the flag it checks - then the flag is cleared
    clr.b FLAG(%a5)
    rts
4:  moveq #0,%d2                    | ... blended toward the next one: y, then x
    move.b 3(%a1),%d2
    move.w (%a2),%d0
    sub.w (%a5),%d0
    muls %d2,%d0
    divs %d3,%d0
    add.w (%a5),%d0
    move.w 2(%a2),%d1
    sub.w 2(%a5),%d1
    muls %d2,%d1
    divs %d3,%d1
    add.w 2(%a5),%d1
    swap %d0
    move.w %d1,%d0
    move.l %d0,%d4
done:
    move.l %d4,HERO                 | the instruction this call replaced, with the blended position
    movem.l (%sp)+,%d0-%d4/%a0-%a2
    rts

| a2 = the segment next to a5 on the same vine in the step's direction (RAM +2); Z set if there is none
neighbour:
    moveq #0,%d1
    move.b 56(%a5),%d1              | this segment's distance from the pivot
    cmp.b #1,2(%a1)
    bne 5f
    cmp.w #MIN_DISTANCE+STEP,%d1    | up
    bcs 9f
    sub.w #STEP,%d1
    bra 6f
5:  add.w #STEP,%d1                 | down
6:  lea 0x104000,%a2
    moveq #95,%d3
7:  cmp.l #SEGMENT_CODE,4(%a2)
    bne 8f
    cmp.b 56(%a2),%d1
    bne 8f
    move.w (%a2),%d2
    sub.w (%a5),%d2
    bpl 12f
    neg.w %d2
12: cmp.w #NEAR,%d2
    bcc 8f
    move.w 2(%a2),%d2
    sub.w 2(%a5),%d2
    bpl 13f
    neg.w %d2
13: cmp.w #NEAR,%d2
    bcc 8f
    and.b #0xFB,%ccr                | found: Z clear
    rts
8:  lea 0x80(%a2),%a2
    dbf %d3,7b
9:  or.b #4,%ccr                    | none: Z set
    rts
"""
        for k, v in (("SEGMENT_CODE", "0x%X" % SEGMENT_CODE), ("MIN_DISTANCE", str(MIN_DISTANCE)),
                     ("FLAG", str(flag)), ("JOY", "0x%X" % joy),
                     ("STEP", str(STEP)), ("UP_RATE", str(UP_RATE)), ("DOWN_RATE", str(DOWN_RATE)), ("NEAR", "0x%X" % NEAR),
                     ("HERO", "0x%X" % hero), ("RAM", "0x%X" % (RAM + 4 * n)), ("TAIL", "0x%X" % (site + 6)),
                     ("LAST", "0x%X" % (LAST_FRAME + n - (RAM + 4 * n)))):
            src = src.replace(k, v)
        code = rom.place_code(src, why="vine slide: Up / Down glides the hero along the vine (player %d)" % (n + 1))
        rom.write(site, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex(orig),
                  why="swinging vine: hero placement goes through the vine slide")
