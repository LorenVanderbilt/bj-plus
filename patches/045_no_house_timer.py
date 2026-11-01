NAME = "no-house-timer"
DESCRIPTION = "No answer countdown in the NPC houses (the travel agent, the drinker, the magician ...) or on the map screen; its banner reads SELECT A PATH, centred"

# Each NPC question screen, and the card game, starts a countdown in the counter at 0x10783F (BCD seconds, 5 to 16)
# and draws it with 0x218D4. The per-frame tick, 0x218A0, counts it down a second at a time and on expiry sets the
# time-up flag 0x107868, which picks an answer for you. no-shop-timer stopped it on the shop and three other screens
# by changing their start-ups, but there are dozens more. Now the tick and the digit drawing both just return the
# time-up flag, which is never set, so no screen counts down or shows digits. Only the shop and the NPC screens use
# these two. The duel mini-game and the ending's timed scene have their own copies (0x28474, 0x245C8) and keep them.
#
# The empty box the digits sat in (top right, part of the brick-wall background every NPC screen shares) is painted
# over with bricks just before each screen fades in, as no-shop-timer does for its three - here only when the box
# is there (its top tile 0x535D at sprite 17 row 10), since some of these fade-ins are other screens.
TICK = 0x218A0               # cmpi.b #0x99,0x783F(a6) ...
DRAW = 0x218D4               # move.w #1,0x3C0004 ...
FLAG_RTS = 0x21926           # tst.b 0x7868(a6) ; rts
# The continue screen (after a game over) counts down with the same two routines: it calls an untouched copy of
# them (they only branch within themselves) and keeps its countdown and digits.
ROUTINES = (0x218A0, 0x2192C)
CONTINUE_CALLS = [(0x34750, TICK), (0x3469C, DRAW)]   # jsr TICK / jsr DRAW
FADE_IN = 0x1572C
FADE_SITES = [0x1F7C2, 0x22EAE, 0x2340A, 0x236EE, 0x238EE, 0x23BB4, 0x26790, 0x27016, 0x27AAE, 0x285EE,
              0x2BABA, 0x2C024, 0x2C488, 0x2D33C, 0x2DDCA, 0x2F076]   # no-shop-timer has 0x21AA4, 0x228B0, 0x25A0C
BOX_TOP = (17 * 64 + 10 * 2, 0x535D)
# The map screen between areas ("SELECT PLEASE") used the same countdown. Its empty box sits at the frame's top
# right, in background sprites 16-17, rows 11-12 (box tile 0x581E at sprite 16 row 11). It's replaced by what the
# mirrored left side of the frame has there: the gold bar (0x5812, as beside both corner stars) and the map's top
# edge, continuing its neighbours' tiles (0x4A84-0x4A86 at sprites 13-15 row 12 run on to 0x4A87; 0x4B45 at sprite
# 18 is matched by 0x4B44 at 17).
MAP_BOX_TOP = (16 * 64 + 11 * 2, 0x581E)
# Red's duel for the torch, in Lower Earth Empire's house: after a tie or a loss, the result text's callback
# (0x288B8) sets the screen's done flag 0x107861. After a win, its callback (0x288C0, which shows Red's torch as
# object 0x104600 and gives it through 0x4BEF0) doesn't. The screen's loop (0x2865C) relied on the countdown expiring,
# which now never happens, so the win screen stayed up forever. A win now starts WIN_COUNT at WIN_HOLD, and the loop
# counts it down once a frame in place of its tick (so Red's torch keeps animating), setting the done flag at 0.
WIN_GIVE = 0x288E0           # jsr 0x4BEF0 ; rts, the end of the win callback
LOOP_TICK = 0x28660          # jsr 0x218A0, the countdown tick in the screen's loop
GIVE_ITEM, DONE = 0x4BEF0, 0x107861
WIN_COUNT = 0x10E81C         # word
WIN_HOLD = 150
MAP_COVER = [   # VRAM address of the first tile word, (tile, attribute) going down
    (16 * 64 + 11 * 2, [(0x5812, 0xDD00), (0x4A87, 0xF000)]),
    (17 * 64 + 11 * 2, [(0x5812, 0xDD00), (0x4B44, 0xF000)]),
]
# The map screen's banner, SELECT PLEASE, sat left of centre to leave room for the box. It's painted letters in the
# background (sprites 4-15, rows 10-11, screen x 52-235). It now reads SELECT A PATH and is moved one 16 px strip
# right, centring it at 159.5. The area from sprite 3 to 18 (x 32-287, y 0-31) is rebuilt as one pixel canvas: the
# gold bar over bricks (sprite 3's tiles) all the way across, the banner pasted one strip right, and its text area
# refilled with its diagonal stripes (period 16, so the shift keeps them in step). The letters are laid out again:
# SELECT as it was, A, P and T taken from PLEASE, and an H drawn in the same serif style. The canvas is then cut back
# into tiles, adding new ones only where needed.
BANNER_COLS = [(0x5813, 0x5812), (0x5802, 0x580A), (0x583A, 0x5842), (0x583B, 0x5843), (0x583C, 0x5844),
               (0x583D, 0x5845), (0x583E, 0x5846), (0x583F, 0x5847), (0x5840, 0x5848), (0x5841, 0x5849),
               (0x584C, 0x584A), (0x584D, 0x584B), (0x581D, 0x5825), (0x5813, 0x581E), (0x5813, 0x581F),
               (0x5813, 0x5812)]          # sprites 3-18, (row 10, row 11), with the box, as the screen draws them
BANNER = (20, 203)                    # its columns in that canvas (x 52-235)
TEXT_AREA = (27, 196, 6, 26)          # inside its frame: x0, x1 (exclusive), y0, y1 (exclusive)
STRIPES, STRIPE_PHASE = "aaaaaaa9988999a9", 14   # the text area's background: STRIPES[(x + y + phase) % 16]
GLYPHS = {"SELECT": (35, 106), "A": (152, 165), "P": (114, 124), "T": (95, 106)}   # columns in the canvas
H = ["11111d.11111d", "dd1ddd.dd1ddd"] + ["..1d.....1d.."] * 4 + ["..11111111d..", "..1dddddd1d.."] + \
    ["..1d.....1d.."] * 4 + ["11111d.11111d", "dddddd.dddddd"]     # rows 9-24 of the text area
WORD_GAP, LETTER_GAP = 7, 1
COVER = [   # as no-shop-timer: (VRAM address of the first tile word, tiles going down)
    (16 * 64 + 10 * 2, [0x535E, 0x5343, 0x5343]),
    (17 * 64 + 10 * 2, [0x533D] * 3),
    (18 * 64 + 10 * 2, [0x533D] * 3),
]


def banner_tiles(rom):
    """The rebuilt banner area: [(VRAM address of sprite n's row 10 tile word, (tile, tile))] for sprites 3-18."""
    canvas = [[0] * 256 for _ in range(32)]
    for i, (t0, t1) in enumerate(BANNER_COLS):
        for r, t in ((0, t0), (1, t1)):
            px = rom.sprite_tile(t)
            for y in range(16):
                canvas[r * 16 + y][i * 16:i * 16 + 16] = px[y]
    stripes = [int(c, 16) for c in STRIPES]

    def stripe(x, y):
        return stripes[(x + y + STRIPE_PHASE) % 16]

    def glyph(a, b):
        x0, x1, y0, y1 = TEXT_AREA
        return [[canvas[y][x] if canvas[y][x] != stripe(x, y) else None for x in range(a, b + 1)] for y in range(y0, y1)]
    glyphs = {k: glyph(*v) for k, v in GLYPHS.items()}
    x0, x1, y0, y1 = TEXT_AREA
    h = [[None] * len(H[0]) for _ in range(y1 - y0)]
    for j, row in enumerate(H):
        for i, ch in enumerate(row):
            if ch != ".":
                h[3 + j][i] = int(ch, 16)
    glyphs["H"] = h
    bar = [[canvas[y][x % 16] for x in range(256)] for y in range(32)]     # sprite 3: bricks over the gold bar
    new = [row[:] for row in bar]
    a, b = BANNER
    for y in range(32):
        new[y][a + 16:b + 17] = canvas[y][a:b + 1]
    for y in range(y0, y1):
        for x in range(x0 + 16, x1 + 16):
            new[y][x] = stripe(x, y)
    layout = [("SELECT", WORD_GAP), ("A", WORD_GAP), ("P", LETTER_GAP), ("A", LETTER_GAP), ("T", LETTER_GAP), ("H", 0)]
    width = sum(len(glyphs[g][0]) + gap for g, gap in layout)
    x = x0 + 16 + (x1 - x0 - width) // 2
    for g, gap in layout:
        for y, row in enumerate(glyphs[g]):
            for i, v in enumerate(row):
                if v is not None:
                    new[y0 + y][x + i] = v
        x += len(glyphs[g][0]) + gap
    known = {}
    for t0, t1 in BANNER_COLS:
        for t in (t0, t1):
            known.setdefault(tuple(map(tuple, rom.sprite_tile(t))), t)
    out = []
    for i in range(16):
        pair = []
        for r in range(2):
            px = [new[r * 16 + y][i * 16:i * 16 + 16] for y in range(16)]
            key = tuple(map(tuple, px))
            if key not in known:
                known[key] = rom.add_sprite_tile(px, why="map screen banner: SELECT A PATH, centred")
            pair.append(known[key])
        out.append(((3 + i) * 64 + 10 * 2, tuple(pair)))
    return out


def apply(rom):
    lo, hi = ROUTINES
    copy = rom.alloc(hi - lo, align=2)
    rom.data[copy:copy + hi - lo] = rom.orig[lo:hi]
    for site, target in CONTINUE_CALLS:
        rom.write(site + 2, (copy + target - lo).to_bytes(4, "big"), expect=target.to_bytes(4, "big"),
                  why="continue screen: its countdown keeps the original routines (a copy)")
    win = rom.place_code("""
    jsr 0x%(give)X
    move.w #%(hold)d,0x%(count)X
    rts
""" % {"give": GIVE_ITEM, "hold": WIN_HOLD, "count": WIN_COUNT}, why="Red's duel won: the torch, then a hold")
    rom.write(WIN_GIVE, bytes.fromhex("4EB9") + win.to_bytes(4, "big"), expect=bytes.fromhex("4EB9") + GIVE_ITEM.to_bytes(4, "big"),
              why="Red's duel won: end the screen after a hold (it waited for the countdown)")
    tick = rom.place_code("""
    tst.w 0x%(count)X
    beq 1f
    subq.w #1,0x%(count)X
    bne 1f
    move.b #1,0x%(done)X                | the hold is over: the screen is done
1:  jmp 0x%(tick)X
""" % {"count": WIN_COUNT, "done": DONE, "tick": TICK}, why="Red's duel screen: the win's hold counted down")
    rom.write(LOOP_TICK, bytes.fromhex("4EB9") + tick.to_bytes(4, "big"), expect=bytes.fromhex("4EB9") + TICK.to_bytes(4, "big"),
              why="Red's duel screen: its tick also counts down the win's hold")
    rom.write(TICK, bytes.fromhex("4EF9") + FLAG_RTS.to_bytes(4, "big"), expect=bytes.fromhex("0C2E0099783F"),
              why="NPC screens: the answer countdown never ticks")
    rom.write(DRAW, bytes.fromhex("4EF9") + FLAG_RTS.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("33FC0001003C0004"), why="NPC screens: no countdown digits")
    def paint(cover):
        return "".join("    move.w #0x%X,0x3C0000\n" % addr + "".join("    move.w #0x%X,0x3C0002\n" % t for t in tiles)
                       for addr, tiles in cover)
    writes = paint(COVER)
    map_writes = "".join("    move.w #0x%X,0x3C0000\n" % addr + "".join(
        "    move.w #0x%X,0x3C0002\n    move.w #0x%X,0x3C0002\n" % ta for ta in cells) for addr, cells in MAP_COVER)
    map_writes += "".join("    move.w #0x%X,0x3C0000\n" % addr + "".join(
        "    move.w #0x%X,0x3C0002\n    move.w #0xDD00,0x3C0002\n" % t for t in pair) for addr, pair in banner_tiles(rom))
    cover = rom.place_code("""
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #0x%(box_at)X,0x3C0000
    cmp.w #0x%(box_tile)X,0x3C0002      | is the box there?
    bne.s 1f
    move.w #2,0x3C0004
%(writes)s    move.w #1,0x3C0004
    bra 2f
1:  move.w #0x%(map_box_at)X,0x3C0000
    cmp.w #0x%(map_box_tile)X,0x3C0002  | is the map screen's box there?
    bne 2f
%(map_writes)s2:  move.w (%%sp)+,%%sr          | map_writes: tile and attribute words, modulo already 1
    jmp 0x%(fade_in)X
""" % {"box_at": BOX_TOP[0], "box_tile": BOX_TOP[1], "writes": writes, "map_box_at": MAP_BOX_TOP[0],
       "map_box_tile": MAP_BOX_TOP[1], "map_writes": map_writes, "fade_in": FADE_IN},
        why="NPC screens: bricks over the empty timer box, then fade in")
    for site in FADE_SITES:
        rom.write(site, bytes.fromhex("4EB9") + cover.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + FADE_IN.to_bytes(4, "big"), why="cover the timer box if there, fade in")
