NAME = "best-clouds"
DESCRIPTION = "TODAY'S BEST 5: banks of Strange Space's pink cloud along the bottom and top, drifting by (parallax); shown longer"

# The high score screen (attract mode, sta/aes/todays_best.sta) stood still. Strange Space 2's ground is a pink
# cloud bank drawn from an 8-column pattern (sta/aes/strange2_cloud.sta): tiles 0x1E80 + column, + 0x08 ... + 0x20
# top to bottom (5 rows, 80 px: the first its puffy top), palette 0xD6 there - 128 px that repeat. Now the screen
# draws BANKS of it: each a chain of CHAIN sprites (from its first sprite) across the screen, in palette PALETTE
# (empty on that screen; the cloud's colours copied in), moved left a pixel every SPEED frames and wrapped every
# 128 px - it drifts by for good - and bobbing gently (BOB_PX either way, a sine of the drift's steps; it moves only
# when the drift does). The top bank is upside down (its tiles flipped, its rows reversed: its puffy edge hangs
# down; the fix layer's title stays in front), half a pattern along and a quarter of a bob out of step with the
# bottom one. All of it is written every frame (the screen does little) by a hook on the screen's frame loop
# (0x549D6: wait a frame, 0x1B034, its timer, the buttons); every way out of the loop goes through 0x54A08, where
# the banks are hidden again. The screen's timer (0x549D0: 256 frames) is SCREEN_FRAMES.
FRAME_CALL = 0x549DC         # jsr 0x1B034
LEAVE = 0x54A08              # clr.b 0x3005(a6) ; rts
SCREEN_TIMER = 0x549D0       # move.w #0x100,0x3800(a6)
SCREEN_FRAMES = 512
FRAME = 0x100206
CHAIN = 28                   # 320 px + one 128 px pattern, and a column to spare
BANKS = [   # (first sprite, screen y of its top, upside down, x offset px, bob phase (256 a bob))
    (300, 176, False, 0, 0),           # the bottom: its top just below the 5th score row
    (330, -66, True, 64, 64),          # the top: its puffy edge (now its bottom) at y 14, near the screen's top
]
SPEED = 3                    # frames a pixel (a pixel at a time: 4 looked like a step every 4 frames)
BOB_PX = 3                   # it bobs up and down this far either way ...
BOB_STEP = 3                 # ... a sine step (256 a bob) a drift step: one bob every 256 / BOB_STEP drift steps
SINE = 0x5E596               # d0 = phase (0-255) -> d0 = sine, +-256
PALETTE = 0x7E
COLOURS = [0x0000, 0x9ECD, 0x5DBC, 0xEDAC, 0x2D9B, 0x5C9A, 0x2C8A, 0xAC8A, 0x5B89, 0xDB89, 0x2B79, 0xAB79,
           0x5A78, 0xDA78, 0x2A68, 0xAA68]   # Strange Space 2's palette 0xD6
TILE, PERIOD, ROWS = 0x1E80, 8, 5
V_FLIP = 2                   # (tile attribute bit)


def bank_code(i, first, top, flipped, x_offset, phase):
    """One bank's sprites for this frame (d1 = the drift's step count, kept)."""
    return r"""
    lea tiles%(i)d(%%pc),%%a0           | bank %(i)d: its tiles (each sprite's 5, and their attribute words)
    move.w #%(first)d*64,%%d3
    moveq #%(chain)d-1,%%d2
2%(i)d: move.w %%d3,0x3C0000
    moveq #%(rows)d*2-1,%%d0
3%(i)d: move.w (%%a0)+,0x3C0002
    dbf %%d0,3%(i)db
    add.w #64,%%d3
    dbf %%d2,2%(i)db
    move.w #0x8000+%(first)d,0x3C0000   | full size
    moveq #%(chain)d-1,%%d2
4%(i)d: move.w #0x0FFF,0x3C0002
    dbf %%d2,4%(i)db
    move.w %%d1,%%d0                    | the bob: BOB_PX x sine of the drift's steps
    mulu #%(bob_step)d,%%d0
    add.w #%(phase)d,%%d0
    and.w #255,%%d0
    jsr 0x%(sine)X
    muls #%(bob)d,%%d0
    asr.l #8,%%d0
    add.w #%(y_field)d,%%d0             | its y (496 - screen y - 16) moved by it
    and.w #511,%%d0
    lsl.w #7,%%d0
    or.w #%(rows)d,%%d0
    move.w #0x8200+%(first)d,0x3C0000   | the first sprite: y and height; the rest chained to it
    move.w %%d0,0x3C0002
    moveq #%(chain)d-2,%%d2
5%(i)d: move.w #0x40,0x3C0002
    dbf %%d2,5%(i)db
    move.w %%d1,%%d0                    | x: a pixel left a drift step, wrapped every 128 px
    add.w #%(x_offset)d,%%d0
    and.w #127,%%d0
    neg.w %%d0
    and.w #511,%%d0
    lsl.w #7,%%d0
    move.w #0x8400+%(first)d,0x3C0000
    move.w %%d0,0x3C0002
""" % {"i": i, "first": first, "chain": CHAIN, "rows": ROWS, "bob_step": BOB_STEP, "phase": phase, "sine": SINE,
       "bob": BOB_PX, "y_field": 496 - (top + 16), "x_offset": x_offset}


def bank_tiles(flipped):
    rows = range(ROWS - 1, -1, -1) if flipped else range(ROWS)
    out = []
    for k in range(CHAIN):
        for r in rows:
            out += [TILE + k % PERIOD + 8 * r, PALETTE << 8 | (V_FLIP if flipped else 0)]
    return out


def apply(rom):
    banks = "".join(bank_code(i, *b) for i, b in enumerate(BANKS))
    tables = "".join("tiles%d:\n    .word %s\n" % (i, ",".join("0x%04X" % t for t in bank_tiles(b[2])))
                     for i, b in enumerate(BANKS))
    hides = "".join("    move.w #0x8200+%d,0x3C0000\n    moveq #%d-1,%%d0\n7%d: move.w #0,0x3C0002\n"
                    "    dbf %%d0,7%db\n" % (b[0], CHAIN, i, i) for i, b in enumerate(BANKS))
    code = rom.place_code(r"""
    bra.w frame
    bra.w leave

| every frame on the screen: its own call, then the cloud banks
frame:
    jsr 0x1B034
    movem.l %%d0-%%d3/%%a0-%%a1,-(%%sp)
    lea colours(%%pc),%%a0              | the colours
    lea 0x%(pal_ram)X,%%a1
    moveq #15,%%d0
1:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,1b
    move.w 0x%(frame)X,%%d1             | d1 = the drift's steps: a pixel every SPEED frames
    and.l #0xFFFF,%%d1
    divu #%(speed)d,%%d1
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
%(banks)s
    move.w (%%sp)+,%%sr
    movem.l (%%sp)+,%%d0-%%d3/%%a0-%%a1
    rts

| leaving the screen: the banks hidden
leave:
    clr.b 0x3005(%%a6)
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
%(hides)s
    move.w (%%sp)+,%%sr
    rts

colours:
    .word %(colours)s
%(tables)s""" % {"pal_ram": 0x400000 + PALETTE * 32, "frame": FRAME, "speed": SPEED, "banks": banks,
                 "hides": hides, "tables": tables, "colours": ",".join("0x%04X" % c for c in COLOURS)},
        why="TODAY'S BEST 5: drifting cloud banks")
    rom.write(FRAME_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90001B034"), why="TODAY'S BEST 5: the cloud banks every frame")
    rom.write(LEAVE, bytes.fromhex("4EF9") + (code + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("422E30054E75"), why="TODAY'S BEST 5: the cloud banks hidden as it ends")
    rom.write(SCREEN_TIMER + 2, SCREEN_FRAMES.to_bytes(2, "big"), expect=(0x100).to_bytes(2, "big"),
              why="TODAY'S BEST 5: shown %d frames (was 256)" % SCREEN_FRAMES)
