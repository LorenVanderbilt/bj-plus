import math

NAME = "special-stage"
DESCRIPTION = "PROTOTYPE: the travel agent's ride as a special stage - steer the bug with the stick and catch the orbs"

# The user, 2026-11-12: a Sonic-style special stage from the travel agent's ride (ride-grid's 3D grid), with the bug
# under the player's control flying through things coming at it. A first prototype, in the ride itself:
#   * The bug (five segments, objects 09-0D, code SEGMENT) shrank 0x0101 a frame and the head ending at 0x2F2F
#     switched the ride off (RIDE_ON). Now it stops shrinking at FLY_SIZE and the ride lasts STAGE_FRAMES once it
#     has (the clock and the count start again while the head is still shrinking).
#   * Once it's flying its own motion stops; the stick moves the head STEP a frame within BOUNDS; Blue (object 00)
#     follows segment 0A as before.
#   * The orbs come out of the vanishing point every 8 frames, growing 0x1010 a frame - now half as fast, and half
#     their speed (ORB_GROWTH, ORB_SPEEDS), so they reach full size as far out but take twice as long. One at full
#     size whose middle is within CATCH of the bug's (segment 0A) is caught: gone, the Flower Get sound, counted.
#   * As in the cinema (its swoop, measured: the head's path, each segment ~4 frames behind the one before) the body
#     follows the leader: the head moves with the stick plus a slow bob (WIGGLE, applied as the change from its last,
#     at +0x14, so it never drifts), and each segment takes the head's place DELAY frames per segment ago (TRAIL)
#     plus its own place in the body - which eases back to REST (a 16th a frame), so the body lines up again after
#     a turn. Up / down are flight controls: up dives, down climbs.
ENABLED = False               # parked 2026-11-17 (a prototype); True to fly it again
SEGMENT_END = 0x278AA         # cmpi.w #0x2F2F,38(a5) ; bne ; clr.b 0x78AE(a6) ; subi.w #0x101,38(a5) ; nop
SEGMENT_END_LEN = 20
SEGMENT_REST = 0x278BE        # the wiggle, then the drawing
ORB_DRAW = 0x27994            # jsr 0xA258: an orb on screen drawn
DRAW = 0xA258
RIDE_ON = 0x1078AE
HEAD = 0x104480               # segment 09: counts the stage's frames (once a frame)
BODY = 0x104500               # segment 0A: where the bug is, for catching
STICK = 0x10FD96              # player 1's stick held: bits 0-3 up, down, left, right
FLY_SIZE = 0x8F8F             # the bug's size once it's flying (+0x26/+0x27)
STAGE_FRAMES = 30 * 60
STEP = 0x180                  # 3 px a frame
BOUNDS = (0x4800, 0xD800, 0x5800, 0xB000)   # x min / max, y min / max (x: 0x4000 + screen x * 128; y counts up)
CATCH = 0x1800                # 24 px each way
SOUND = 0x62                  # Flower Get
WIGGLE = [int(round(0x400 * math.sin(2 * math.pi * i / 32))) for i in range(32)]   # the head's slow bob: 8 px
                              # each way, 128 frames round (a step every 4)
TRAIL, TRAIL_N = 0x10EF20, 32 # spare RAM: the head's last 32 places (y, x: a long each)
DELAY = 4                     # frames each segment is behind the one before (the cinema's 3-5)
REST = [(-0x300 * k, x) for k, x in zip(range(1, 5), (-0x800, -0x800, -0x800, 0))]   # segments 0A-0D's place in
                              # the body at rest, from the head's (y, x): stacked 6 px apart, lined up as the cinema
                              # starts them (x 0x7000 / 0x7800 for their frames' widths)
EASE = 4                      # a 16th of the way there each frame
ORB_GROWTH = 0x27970          # the orbs' growth a frame (addi.w #0x1010,38(a5)): halved
ORB_SPEEDS = 0x279A2          # 16 (y, x) speeds an orb picks from: halved
PLAY_SOUND = 0x152FE
RAM = 0x10EF10                # spare RAM: +0 frames flown, +2 orbs caught, +4 / +6 this frame's x / y move (words)


def apply(rom):
    if not ENABLED:
        return
    assert rom.data[SEGMENT_END:SEGMENT_END + SEGMENT_END_LEN] == bytes.fromhex(
        "0C6D2F2F00266604422E78AE046D010100264E71")
    assert rom.u16(ORB_DRAW) == 0x4EB9 and rom.u32(ORB_DRAW + 2) == DRAW
    code = rom.place_code("""
    bra.w segment                       | +0
    bra.w orb                           | +4

| a bug segment, every frame (a5): its size, the stage's clock, the stick
segment:
    cmpi.w #0x%(fly)X,38(%%a5)
    bls 1f
    subi.w #0x101,38(%%a5)              | still shrinking: the ride as it was (its own wiggle and drift)
    clr.w 0x14(%%a5)                    | (its bob from 0)
    cmpa.l #0x%(head)X,%%a5
    bne 0f
    clr.l 0x%(ram)X                     | (the ride's start: the clock and count from 0)
0:  jmp 0x%(rest)X
1:  cmpa.l #0x%(head)X,%%a5
    bne 5f
    addq.w #1,0x%(ram)X                 | the head, first each frame: the clock, the stick, its trail
    cmpi.w #%(frames)d,0x%(ram)X
    bcs 2f
    clr.b 0x%(ride_on)X                 | the stage's time is up
2:  move.b 0x%(stick)X,%%d0
    moveq #0,%%d1                       | x move
    btst #2,%%d0
    beq 3f
    move.w #-%(step)d,%%d1
3:  btst #3,%%d0
    beq 4f
    move.w #%(step)d,%%d1
4:  move.w 2(%%a5),%%d2
    add.w %%d1,%%d2
    cmpi.w #0x%(xmin)X,%%d2
    bcs 41f
    cmpi.w #0x%(xmax)X,%%d2
    bhi 41f
    move.w %%d2,2(%%a5)
41: moveq #0,%%d1                       | y move (flight controls: up dives, down climbs)
    btst #0,%%d0
    beq 43f
    move.w #-%(step)d,%%d1
43: btst #1,%%d0
    beq 44f
    move.w #%(step)d,%%d1
44: move.w (%%a5),%%d2
    add.w %%d1,%%d2
    cmpi.w #0x%(ymin)X,%%d2
    bcs 45f
    cmpi.w #0x%(ymax)X,%%d2
    bhi 45f
    move.w %%d2,(%%a5)
45: move.w 0x%(ram)X,%%d0               | its slow bob: the change since last frame's
    lsr.w #2,%%d0
    andi.w #31,%%d0
    add.w %%d0,%%d0
    lea wiggle(%%pc),%%a0
    move.w (%%a0,%%d0.w),%%d0
    move.w %%d0,%%d1
    sub.w 0x14(%%a5),%%d0
    add.w %%d0,(%%a5)
    move.w %%d1,0x14(%%a5)
    lea 0x%(trail)X,%%a0                | where it is now, into the trail
    move.w 0x%(ram)X,%%d0
    cmpi.w #1,%%d0
    bne 46f
    moveq #%(trail_n)d-1,%%d1            | (the first flying frame: the whole trail here)
47: move.l (%%a5),(%%a0)+
    dbf %%d1,47b
    bra 48f
46: andi.w #%(trail_n)d-1,%%d0
    lsl.w #2,%%d0
    move.l (%%a5),(%%a0,%%d0.w)
48: clr.l 12(%%a5)
    jmp 0x%(draw)X

| the other segments: the head's place DELAY frames ago per segment back, plus their own place in the body (taken
| on the first flying frame, kept at +0x14 / +0x16)
5:  move.l %%a5,%%d1
    sub.l #0x%(head)X,%%d1
    lsr.w #7,%%d1                       | 1-4 segments behind the head
    move.w 0x%(ram)X,%%d0
    cmpi.w #1,%%d0
    bne 51f
    move.w (%%a5),%%d2                  | (the first flying frame: its place in the body)
    sub.w 0x%(head)X,%%d2
    move.w %%d2,0x14(%%a5)
    move.w 2(%%a5),%%d2
    sub.w 0x%(head)X+2,%%d2
    move.w %%d2,0x16(%%a5)
51: move.w %%d1,%%d2                    | its place eases toward the body's rest (REST), an EASE-th a frame
    subq.w #1,%%d2
    lsl.w #2,%%d2
    lea body_rest(%%pc),%%a0
    move.w (%%a0,%%d2.w),%%d3           | y
    sub.w 0x14(%%a5),%%d3
    asr.w #%(ease)d,%%d3
    bne 52f
    move.w (%%a0,%%d2.w),%%d3           | (close enough: there)
    sub.w 0x14(%%a5),%%d3
52: add.w %%d3,0x14(%%a5)
    move.w 2(%%a0,%%d2.w),%%d3          | x
    sub.w 0x16(%%a5),%%d3
    asr.w #%(ease)d,%%d3
    bne 53f
    move.w 2(%%a0,%%d2.w),%%d3
    sub.w 0x16(%%a5),%%d3
53: add.w %%d3,0x16(%%a5)
    mulu #%(delay)d,%%d1
    sub.w %%d1,%%d0
    andi.w #%(trail_n)d-1,%%d0
    lsl.w #2,%%d0
    lea 0x%(trail)X,%%a0
    move.w (%%a0,%%d0.w),%%d1
    add.w 0x14(%%a5),%%d1
    move.w %%d1,(%%a5)
    move.w 2(%%a0,%%d0.w),%%d1
    add.w 0x16(%%a5),%%d1
    move.w %%d1,2(%%a5)
    clr.l 12(%%a5)
    jmp 0x%(draw)X

wiggle:
    .word %(wiggle)s
body_rest:
    .word %(body_rest)s

| an orb on screen (a5): caught if it's full size and over the bug, else drawn
orb:
    cmpi.w #0xFFFF,38(%%a5)
    bne 9f
    move.w 2(%%a5),%%d0
    sub.w 0x%(body)X+2,%%d0
    bpl 1f
    neg.w %%d0
1:  cmpi.w #%(catch)d,%%d0
    bhi 9f
    move.w (%%a5),%%d0
    sub.w 0x%(body)X,%%d0
    bpl 2f
    neg.w %%d0
2:  cmpi.w #%(catch)d,%%d0
    bhi 9f
    clr.b 40(%%a5)                      | caught: gone (as when it leaves the screen)
    addq.w #1,0x%(ram)X+2
    moveq #%(sound)d,%%d0
    jmp 0x%(play)X
9:  jmp 0x%(draw)X
""" % {"head": HEAD, "body": BODY, "ram": RAM, "frames": STAGE_FRAMES, "ride_on": RIDE_ON, "fly": FLY_SIZE,
       "stick": STICK, "step": STEP, "xmin": BOUNDS[0], "xmax": BOUNDS[1], "ymin": BOUNDS[2], "ymax": BOUNDS[3],
       "rest": SEGMENT_REST, "catch": CATCH, "sound": SOUND, "play": PLAY_SOUND, "draw": DRAW, "trail": TRAIL, "trail_n": TRAIL_N, "delay": DELAY, "ease": EASE,
       "body_rest": ",".join("%d,%d" % (y, x) for y, x in REST),
       "wiggle": ",".join(str(w) for w in WIGGLE)},
        why="special stage prototype")
    rom.write(SEGMENT_END, bytes.fromhex("4EF9") + code.to_bytes(4, "big") + bytes.fromhex("4E71") * 7,
              expect=rom.data[SEGMENT_END:SEGMENT_END + SEGMENT_END_LEN], why="special stage: the bug flies and steers")
    rom.write(ORB_GROWTH, (0x0808).to_bytes(2, "big"), expect=(0x1010).to_bytes(2, "big"),
              why="special stage: the orbs grow half as fast")
    speeds = bytes(rom.data[ORB_SPEEDS:ORB_SPEEDS + 64])
    halved = b"".join((int.from_bytes(speeds[i:i + 2], "big", signed=True) // 2).to_bytes(2, "big", signed=True)
                      for i in range(0, 64, 2))
    rom.write(ORB_SPEEDS, halved, expect=speeds, why="special stage: the orbs at half speed")
    rom.write(ORB_DRAW, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + DRAW.to_bytes(4, "big"), why="special stage: orbs can be caught")
