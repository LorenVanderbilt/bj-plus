NAME = "story-fa"
DESCRIPTION = "Story cinema: Princess Fa glides in beside Blue as BLUE LOVES PRINCESS FA starts (her continue-screen art, shrunk)"

# The user, 2026-11-12: the continue screen's big Fa, brought into the story's Blue scene. She glides in from the
# right as its second line (BLUE LOVES PRINCESS FA / OF RAGUY'S ROYAL FAMILY.) starts, and stops beside Blue.
#
# The continue screen builds her from four objects (its 0xA158 records at 0x34566 ...): her top (frame 0x33C0,
# palette 0xA6), her bottom (0x3428, palette 0x81), her eyes (0x33C4 ...) and her mouth (0x33D8 ...), placed relative
# to each other as PARTS has them. Both palettes are loaded at boot (a table at 0x6020 / 0x64C0) and are still there
# in the story, so the frames show in her colours as they are.
#
# Line 1's countdown object (0x35772) clears the box (LINE2, jsr 0x34ED4) and prints line 2: there the parts are made
# (0xA158, in free object slots from SLOTS), shrunk by SHRINK (the object's +0x26: width 0-15 in its high nibble, the low nibble 0xF for an even shrink;
# +0x27: height 0-255)
# with their offsets from her top scaled to match, starting off the right edge (START_X). Each frame their code moves
# them STEP left until her top reaches TARGET_X (each part's own stop is kept at +0x10).
ENABLED = False               # parked 2026-11-12 (the background scroll and her faces still to work out); True to
                              # try it again
LINE2 = 0x3577C               # jsr 0x34ED4 (clear the text box), then line 2 printed
CLEAR_BOX = 0x34ED4
SLOTS = (0x6180, 12)          # object slots tried (0x43-0x4E): the first's offset from 0x100000, how many. Slots
                              # 0x3C on are drawn from sprite 199 down (the object list at 0x1002F0), behind the
                              # text box (sprites 200-220); slots below 0x3C from 379 down, in front of it
PARTS = [   # (frame, x and y on the continue screen, draw order: lower is in front)
    (0x33C0, 0x9800, 0x9800, 0x7000),    # top: head, arms, dress
    (0x3428, 0x9800, 0x6000, 0x7000),    # bottom: the dress's hem and her wings
    (0x33C4, 0xA800, 0x8800, 0x6000),    # eyes
    (0x33D8, 0xA800, 0x7800, 0x6000),    # mouth
]
WIDTH_16THS = 16              # her size: full (the hardware shrinks width in 16ths; 16 = none)
SCALE = WIDTH_16THS / 16
SHRINK = ((WIDTH_16THS - 1) << 4 | 0xF, int(256 * SCALE) - 1)   # +0x26: width - 1 in its high nibble (low nibble
                                                                  # 0xF: an even shrink), +0x27: height in 256ths - 1
# A shrunk frame is drawn around the middle of its width and from its bottom (the drawing routine, 0xA5B2), so each
# part's x and y are worked out from where its middle and bottom go, scaled about her feet (FEET: the middle of her
# top's width, the lowest bottom). x: screen x * 128 + 0x4000; y counts up the screen, 128 a pixel.
FEET_Y = 0x4B00               # her eyes level with Blue's (most of her behind the text box)
TARGET_X = 0xB300             # her middle once she's in (screen x 230)
START_X = 0xF300              # off the right edge (screen x 358)
STEP = 0x100                  # 2 px a frame
GROUP = 5                     # +0x20 word (as Blue's parts)


def placed(rom, mid_x):
    """Each part's (frame, x, y, order) shrunk by SCALE about her feet, her middle at mid_x."""
    size = {}
    for frame, x, y, order in PARTS:
        p = rom.u32(0x60772 + frame)
        cols, rows = rom.data[p] + 1, rom.data[p + 1] + 1
        size[frame] = (cols * 16 * 128, rows * 16 * 128)
    top = PARTS[0]
    pivot_x = top[1] + size[top[0]][0] // 2
    pivot_y = min(y - size[f][1] for f, x, y, o in PARTS)
    out = []
    for frame, x, y, order in PARTS:
        w, h = size[frame]
        mid = mid_x + int((x + w // 2 - pivot_x) * SCALE)
        bottom = FEET_Y + int((y - h - pivot_y) * SCALE)
        out.append((frame, (mid - w // 2) & 0xFFFF, (bottom + h) & 0xFFFF, order))
    return out


def apply(rom):
    if not ENABLED:
        return
    assert rom.u32(LINE2 + 2) == CLEAR_BOX
    mover = rom.place_code("""
| each part, every frame: STEP left until its own stop (+0x10)
    move.w 2(%%a5),%%d0
    sub.w #%(step)d,%%d0
    cmp.w 0x10(%%a5),%%d0
    bgt 1f
    move.w 0x10(%%a5),%%d0
1:  move.w %%d0,2(%%a5)
    rts
""" % {"step": STEP}, why="story Fa: a part gliding in")
    records = ""
    for (frame, x, y, order), (_, stop, _, _) in zip(placed(rom, START_X), placed(rom, TARGET_X)):
        records += """
    jsr 0xA158
    .word 0x%(slot)X, %(tries)d
    .word 0x%(y)X, 0x%(x)X
    .long 0x%(mover)X
    .word 0x%(frame)X, 0, 0, 0, 0x%(stop)X, 0
    .word %(group)d
    .word 0x%(shrink)X, 0x%(order)X
""" % {"slot": SLOTS[0], "tries": SLOTS[1] - 1, "y": y, "x": x,
       "mover": mover, "group": GROUP, "frame": frame, "stop": stop, "shrink": SHRINK[0] << 8 | SHRINK[1],
       "order": order}
    code = rom.place_code("""
| line 2 starting: the box cleared, then Fa's parts made off the right edge
    jsr 0x%(clear)X
    movem.l %%d0-%%d2/%%a0-%%a1,-(%%sp)%(records)s
    movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    rts
""" % {"clear": CLEAR_BOX, "records": records}, why="story Fa: made as line 2 starts")
    rom.write(LINE2, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("4EB9") + CLEAR_BOX.to_bytes(4, "big"),
              why="story: Fa comes in with line 2")
