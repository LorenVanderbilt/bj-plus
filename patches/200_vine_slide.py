NAME = "vine-slide"
DESCRIPTION = "Swinging vines: hold Up / Down to slide along the vine"

# A swinging vine is a root object at the pivot plus a chain of segment objects (code 0x4FD30), each with its
# distance from the pivot at +56 (0, 6, 12 ...) and moving with the swing. The hero hangs from one segment:
# player 1's attach flag is that segment's +52 (player 2's +53), 2 while holding; every frame the segment code
# (0x4FD82) calls 0x4FE72 (player 1) / 0x4FEEE (player 2), which puts the hero at that segment's position plus
# a fixed offset. Grabbing picks the segment touched - normally the bottom one - and the hero stays there.
#
# Both routines start with `move.l (a5),hero` (6 bytes); that is now a call to `slide`, which does the same
# after this: while the player holds Up or Down, every RATE frames (starting at the press) it moves the
# attach flag to the next segment up / down the same vine - found by distance +-6 and closeness - so the hero
# slides along it. It stops at the bottom segment and at MIN_DISTANCE from the pivot. Only vine segments with
# the steady "holding" value are touched, so grabbing and letting go work as before.
SITES = [(0x4FE72, "2D6D00004000", 52, 0x10FD96, 0x104000), (0x4FEEE, "2D6D00004080", 53, 0x10FD9C, 0x104080)]
SEGMENT_CODE = 0x4FD30
HOLDING = 2
STEP = 6                  # distance between segments (+56)
MIN_DISTANCE = 6          # don't slide right up to the pivot
RATE = 6                  # frames per segment while held
NEAR = 0x1000             # a neighbouring segment of the same vine is within 16 px
HOLD_COUNT = 0x10C302     # spare RAM, one byte per player: frames Up/Down has been held


def apply(rom):
    for n, (site, orig, flag, joy, hero) in enumerate(SITES):
        code = rom.place_code(r"""
    movem.l %d0-%d3/%a0-%a2,-(%sp)
    cmp.l #SEGMENT_CODE,4(%a5)      | only vine segments, only while holding
    bne done
    cmp.b #HOLDING,FLAG(%a5)
    bne done
    lea HOLD_COUNT,%a1
    move.b JOY,%d0                  | bit 0 up, bit 1 down
    and.b #3,%d0
    bne 1f
    clr.b (%a1)
    bra done
1:  moveq #0,%d2
    move.b (%a1),%d2
    addq.b #1,(%a1)
    divu #RATE,%d2                  | move on the press, then every RATE frames
    swap %d2
    tst.w %d2
    bne done
    moveq #0,%d1
    move.b 56(%a5),%d1              | this segment's distance from the pivot
    btst #0,%d0
    beq 2f
    cmp.w #MIN_DISTANCE+STEP,%d1    | up
    bcs done
    sub.w #STEP,%d1
    bra 3f
2:  add.w #STEP,%d1                 | down
3:  lea 0x104000,%a2                | find that segment of this vine
    moveq #95,%d3
4:  cmp.l #SEGMENT_CODE,4(%a2)
    bne 5f
    cmp.b 56(%a2),%d1
    bne 5f
    move.w (%a2),%d2
    sub.w (%a5),%d2
    bpl 6f
    neg.w %d2
6:  cmp.w #NEAR,%d2
    bcc 5f
    move.w 2(%a2),%d2
    sub.w 2(%a5),%d2
    bpl 7f
    neg.w %d2
7:  cmp.w #NEAR,%d2
    bcc 5f
    move.b FLAG(%a5),FLAG(%a2)      | hand the hero over to it
    clr.b FLAG(%a5)
    bra done
5:  lea 0x80(%a2),%a2
    dbf %d3,4b
done:
    movem.l (%sp)+,%d0-%d3/%a0-%a2
    move.l (%a5),HERO               | the instruction this call replaced
    rts
""".replace("SEGMENT_CODE", "0x%X" % SEGMENT_CODE).replace("HOLD_COUNT", "0x%X" % (HOLD_COUNT + n))
   .replace("HOLDING", str(HOLDING)).replace("FLAG", str(flag)).replace("JOY", "0x%X" % joy)
   .replace("MIN_DISTANCE", str(MIN_DISTANCE)).replace("STEP", str(STEP)).replace("RATE", str(RATE))
   .replace("NEAR", "0x%X" % NEAR).replace("HERO", "0x%X" % hero),
            why="vine slide: Up / Down moves the hero along the vine (player %d)" % (n + 1))
        rom.write(site, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex(orig),
                  why="swinging vine: hero placement goes through the vine slide")
