NAME = "stage-wipe"
DESCRIPTION = "After a stage's title card, the level is revealed by a wipe from the screen's centre (a spiral or an iris)"

import math

# A stage starts, after its title card or after losing a life, by building the level over a few frames (SETUPS),
# clearing the fix layer (CLEARS) and setting MODE to 1 (STARTS). Now SETUPS first cover the screen with black fix
# tiles, since the fix layer is drawn above everything, and CLEARS fill it with black again instead of blank.
#
# STARTS then begin the wipe. After START_DELAY frames it runs for DURATION frames, each frame writing only the cells
# that change. The order is worked out here: whole cells cleared in turn, or with SMOOTH, the iris's edge drawn with
# partly black tiles. It runs at the start of the HUD each frame (HUD_ENTRY, before the hud patch's routine). The HUD
# isn't drawn while the screen is covered or wiping, and is drawn in full afterwards: TIMER_HIDDEN is set with the
# cover, and the hud patch redraws every part when that changes.
#
# SHAPE "iris" is a ring growing from the centre. "spiral" is a wiper blade pinned at the centre that sweeps round
# TURNS times, growing to the corners, clearing each cell the first time it reaches it.
SHAPE = "iris"
SMOOTH = True                 # draw the iris's edge with partly black tiles instead of whole cells
EDGE_DIRECTIONS = 8           # the fix layer can't flip tiles, so each direction the edge faces needs its own
PRECISION = 9                 # decimals that distances are rounded to before comparing, so near-ties come out
                              # the same on every Python (math functions differ in the last bit)
EDGE_COVERS = (0.25, 0.5, 0.75)   # how much of an edge tile is clear; 8 x 3 = 24 new fix tiles
TURNS = 2
CLOCKWISE = False
START_DELAY = 0               # frames of black after the title card, before the wipe
DURATION = 30                 # frames from the centre to the corners (60 = a second)
TITLE_HOLD = 105              # frames the title card stays up (was 189); a button press ends it
MUSIC_AT = DURATION           # frames into play before the stage music starts, letting the title card's jingle
                              # finish; after losing a life the music starts as before

SETUPS = [0x114E0, 0x115B0]   # jsr 0x5AED2: the level set-up starts
SETUP = 0x5AED2
CLEARS = [0x1154C, 0x11612]   # jsr 0x9FBE: clears the fix layer (0x4FE cells from 0x7002 to BLANK)
FIX_CLEAR = 0x9FBE
STARTS = [0x11552, 0x11618]   # move.b #1,0x3004(a6): play starts
HOLD = 0x13A98                # move.w #189,d7: the title card's hold in frames
MUSIC = 0x11532               # jsr 0x151CE: stop the sound and start the stage music, after the title card
STAGE_MUSIC = 0x151CE
CARD_ENDS = [0x13AFA, 0x13B1C]   # jsr 0x9FBE: clears the title card's text (timed out, or a button pressed)
# The top corner of a player who isn't playing is redrawn blank every 32 frames (see no-join-prompts), which would
# punch through the cover. CORNERS (andi.w #31,d1 ; bne.w <past it>) skip that while the wipe is on.
CORNERS = [(0x11B58, 0x11CBA), (0x11CD6, 0x11E28)]   # (site, address past the corner's drawing)
MODE = 0x103004
HUD_ENTRY = 0x4E4B8           # jsr <the hud patch's frame routine> ; nop
NO_HUD = 0x10309B
TIMER_HIDDEN = 0x10E9FE       # the hud patch's flag
BLACK_PALETTE, BLACK_PIXEL = 7, 1   # fix palette 7, entry 1, which the hud patch keeps black
BLANK = 0x0520
COLUMNS, ROWS = range(40), range(2, 30)   # the visible fix cells
BLACKOUT = 0x10E600           # screen-blackout's flag; the wipe waits while the screen is held black
WIPE_ON, WIPE_T = 0x10EA60, 0x10EA62   # spare RAM: a byte (1 = covered, 2 = running) and the frame count
MUSIC_DUE = 0x10EA66          # byte: set while the stage music is still to start
BLINKS = [0x107009, 0x107409] # each hero's invincibility timer: none as a stage starts, only after a death


def order():
    """The visible cells' fix addresses in the order they're cleared, and how many are cleared by each frame."""
    cx, cy = (len(COLUMNS) - 1) / 2, (ROWS[0] + ROWS[-1]) / 2
    far = math.hypot(cx, cy - ROWS[0])
    def key(c, r):
        d = math.hypot(c - cx, r - cy) / far
        if SHAPE == "iris":
            return round(d, PRECISION)
        turn = (math.atan2(r - cy, c - cx) / (2 * math.pi)) % 1
        turn = turn if CLOCKWISE else 1 - turn
        reach = d * TURNS                       # in turns: when the blade first reaches this far
        return round(reach + (turn - reach) % 1, PRECISION)   # then the next time it points this way
    cells = sorted(((c, r) for c in COLUMNS for r in ROWS), key=lambda cr: key(*cr))
    keys = [key(c, r) for c, r in cells]
    # how many are cleared by each frame: the edge moves at a steady pace, since a fixed cell count per frame would
    # open the iris with a jump (its area grows with the square of its size)
    counts = [sum(1 for k in keys if k <= keys[-1] * (f + 1) / DURATION) for f in range(DURATION)]
    return [0x7000 + c * 32 + r for c, r in cells], counts


def edge_tiles():
    """{(direction, cover): 8x8 pixels}, clear (0) on the side toward the centre and black outward."""
    tiles = {}
    for k in range(EDGE_DIRECTIONS):
        a = 2 * math.pi * k / EDGE_DIRECTIONS
        out = sorted((round((x - 3.5) * math.cos(a) + (y - 3.5) * math.sin(a), PRECISION), x, y)
                     for y in range(8) for x in range(8))
        for cover in EDGE_COVERS:
            px = [[BLACK_PIXEL] * 8 for _ in range(8)]
            for _, x, y in out[:round(64 * cover)]:
                px[y][x] = 0
            tiles[k, cover] = px
    return tiles


def smooth_frames():
    """The cells that change each frame, as [(fix address, None for clear / "black" / an edge tile's key)]. Each
    cell gets whichever of black, clear or an edge tile best matches the circle's pixels there."""
    tiles = edge_tiles()
    cx, cy = len(COLUMNS) * 4, (ROWS[0] + ROWS[-1] + 1) * 4      # the visible area's centre, in pixels
    far = math.hypot(cx, cy - ROWS[0] * 8)
    now = {(c, r): "black" for c in COLUMNS for r in ROWS}
    frames = []
    for f in range(DURATION):
        radius, changes = far * (f + 1) / DURATION, []
        for (c, r), was in now.items():
            if was is None:
                continue
            mask = [[0 if round(math.hypot(c * 8 + x + 0.5 - cx, r * 8 + y + 0.5 - cy) - radius, PRECISION) <= 0
                     else BLACK_PIXEL
                     for x in range(8)] for y in range(8)]
            flat = sum(mask, [])
            if not any(flat):
                best = None
            elif all(flat):
                best = "black"
            else:
                facing = round(math.atan2(r * 8 + 4 - cy, c * 8 + 4 - cx) / (2 * math.pi) * EDGE_DIRECTIONS) \
                    % EDGE_DIRECTIONS
                options = [None, "black"] + [(facing, cover) for cover in EDGE_COVERS]
                def miss(o):
                    px = [[0] * 8] * 8 if o is None else [[BLACK_PIXEL] * 8] * 8 if o == "black" else tiles[o]
                    return sum(1 for y in range(8) for x in range(8) if px[y][x] != mask[y][x])
                best = min(options, key=miss)
            if best != was:
                now[c, r] = best
                changes.append((0x7000 + c * 32 + r, best))
        frames.append(changes)
    return frames, tiles


def apply(rom):
    assert rom.u16(HUD_ENTRY) == 0x4EB9, "expected the hud patch's call"
    hud = rom.u32(HUD_ENTRY + 2)
    black = BLACK_PALETTE << 12 | rom.add_fix_tile([[BLACK_PIXEL] * 8 for _ in range(8)], why="stage wipe: black",
                                                   share=True)
    if SHAPE == "iris" and SMOOTH:
        frames, tiles = smooth_frames()
        words = {None: BLANK, "black": black}
        for key in sorted({k for fr in frames for _, k in fr if k not in (None, "black")}):
            words[key] = BLACK_PALETTE << 12 | rom.add_fix_tile(tiles[key], why="stage wipe: an edge, facing %d, %d%% clear"
                                                                % (key[0], key[1] * 100), share=True)
        writes = [[(a, words[k]) for a, k in fr] for fr in frames]
    else:
        cells, counts = order()
        writes = [[(a, BLANK) for a in cells[(counts[f - 1] if f else 0):counts[f]]] for f in range(DURATION)]
    offsets = [0]
    for fr in writes:
        offsets.append(offsets[-1] + len(fr))
    code = rom.place_code(r"""
    bra.w start
    bra.w frame
    bra.w cover
    bra.w music
    bra.w card_end
| the level set-up: cover the screen first, unless the title card's end already did
    tst.b 0x%(on)X
    bne 1f
    move.b #1,0x%(on)X
    st 0x%(hidden)X
    bsr fill
1:  jmp 0x%(setup)X
| the title card's end: cover the screen except its text, which stays up while the level is built
card_end:
    move.b #1,0x%(on)X
    st 0x%(hidden)X
    movem.l %%d0-%%d1,-(%%sp)
    move.w #0x7002,%%d1
1:  move.w %%d1,0x3C0000
    move.w 0x3C0002,%%d0
    andi.w #0xFFF,%%d0
    cmpi.w #0x020,%%d0
    beq 2f
    cmpi.w #0x520,%%d0
    beq 2f
    tst.w %%d0
    bne 3f
2:  move.w %%d1,0x3C0000
    move.w #0x%(black)X,0x3C0002
3:  addq.w #1,%%d1
    cmpi.w #0x7500,%%d1
    bcs 1b
    movem.l (%%sp)+,%%d0-%%d1
    rts
| the fix layer's clear before play: black, not blank
cover:
fill:
    move.l %%d1,-(%%sp)
    move.w #0x7002,0x3C0000
    move.w #1,0x3C0004
    move.w #0x4FE-1,%%d1
1:  move.w #0x%(black)X,0x3C0002
    dbf %%d1,1b
    move.l (%%sp)+,%%d1
    rts
| each frame, before the HUD: if covered or wiping, skip the HUD; otherwise draw it as usual
frame:
    tst.b 0x%(on)X
    bne 1f
    jmp 0x%(hud)X
1:  tst.b 0x%(no_hud)X
    beq 2f
    jmp 0x%(hud)X
2:  tst.b 0x%(blackout)X                | while screen-blackout holds the screen black, wait for it
    bne 10f
    cmpi.b #2,0x%(on)X
    bne 10f                             | covered: waiting for play
    movem.l %%d0-%%d3/%%a0,-(%%sp)
    move.w #1,0x3C0004
    addq.w #1,0x%(t)X
    tst.b 0x%(due)X                     | start the stage music when it's due
    beq 3f
    move.w 0x%(t)X,%%d0
    cmpi.w #%(music_at)d,%%d0
    blt 3f
    clr.b 0x%(due)X
    movem.l %%d4-%%d7/%%a1-%%a6,-(%%sp)
    jsr 0x%(stage_music)X
    movem.l (%%sp)+,%%d4-%%d7/%%a1-%%a6
3:  move.w 0x%(t)X,%%d0
    bmi 9f                              | still in the delay
    cmpi.w #%(frames)d-1,%%d0
    bcs 5f
    clr.b 0x%(on)X                      | the last frame: the HUD returns next frame
5:  add.w %%d0,%%d0                      | this frame's writes: changes[offsets[t]] to changes[offsets[t + 1]]
    lea offsets(%%pc),%%a0
    move.w 2(%%a0,%%d0.w),%%d1
    move.w (%%a0,%%d0.w),%%d0
    sub.w %%d0,%%d1
    beq 9f
    subq.w #1,%%d1
    lsl.w #2,%%d0
    lea changes(%%pc),%%a0
    add.w %%d0,%%a0
6:  move.w (%%a0)+,0x3C0000
    move.w (%%a0)+,0x3C0002
    dbf %%d1,6b
9:  movem.l (%%sp)+,%%d0-%%d3/%%a0
10: addq.l #4,%%sp                      | leave the HUD routine, as its own no-HUD case does
    rts
| after the title card: start the stage music later, letting the jingle play on
music:
    st 0x%(due)X
    rts
| play starts: the wipe
start:
    move.b #1,0x%(mode)X
    move.b #2,0x%(on)X
    move.w #-%(delay)d-1,0x%(t)X
    tst.b 0x%(due)X                     | after the title card the heroes don't blink; after a death they do
    beq 1f
    clr.b 0x%(blink1)X
    clr.b 0x%(blink2)X
1:  rts
offsets:
    .word %(offsets)s
changes:
    .word %(changes)s
""" % {"blackout": BLACKOUT, "on": WIPE_ON, "t": WIPE_T, "hud": hud, "no_hud": NO_HUD, "hidden": TIMER_HIDDEN,
       "black": black, "duration": DURATION, "blank": BLANK, "mode": MODE, "delay": START_DELAY,
       "setup": SETUP, "due": MUSIC_DUE, "music_at": min(MUSIC_AT, START_DELAY + DURATION - 1) - START_DELAY,
       "stage_music": STAGE_MUSIC, "blink1": BLINKS[0], "blink2": BLINKS[1],
       "frames": DURATION, "offsets": ",".join(str(n) for n in offsets),
       "changes": ",".join("0x%X,0x%X" % aw for fr in writes for aw in fr)}, why="stage wipe: %s over %d frames" % (SHAPE, DURATION))
    rom.write(HUD_ENTRY + 2, (code + 4).to_bytes(4, "big"), expect=hud.to_bytes(4, "big"),
              why="the HUD each frame: the stage wipe first")
    rom.write(MUSIC, bytes.fromhex("4EB9") + (code + 12).to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + STAGE_MUSIC.to_bytes(4, "big"),
              why="after the title card: the stage's music once the wipe's under way (the jingle plays on)")
    for at in SETUPS:
        rom.write(at, bytes.fromhex("4EB9") + (code + 20).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + SETUP.to_bytes(4, "big"), why="stage set-up: the screen covered first")
    for at in CARD_ENDS:
        rom.write(at, bytes.fromhex("4EB9") + (code + 16).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + FIX_CLEAR.to_bytes(4, "big"),
                  why="title card's end: covered but for its text (no black gap)")
    rom.write(HOLD, bytes.fromhex("3E3C") + TITLE_HOLD.to_bytes(2, "big"), expect=bytes.fromhex("3E3C00BD"),
              why="title card: held %d frames (was 189), then the stage wipe" % TITLE_HOLD)
    for at, past in CORNERS:
        skip = rom.place_code("""
    andi.w #31,%%d1
    bne 1f
    tst.b 0x%X
    bne 1f
    rts
1:  addq.l #4,%%sp
    jmp 0x%X
""" % (WIPE_ON, past), why="stage wipe: a player's empty corner not drawn through it")
        rom.write(at, bytes.fromhex("4EB9") + skip.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex("0241001F6600") + (past - at - 6).to_bytes(2, "big"),
                  why="empty corner: not while the stage wipe is on")
    for at in CLEARS:
        rom.write(at, bytes.fromhex("4EB9") + (code + 8).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + FIX_CLEAR.to_bytes(4, "big"), why="before play: the fix layer black")
    for at in STARTS:
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("1D7C00013004"),
                  why="title card done: the stage wipe")
