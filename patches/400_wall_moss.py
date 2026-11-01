NAME = "wall-moss"
DESCRIPTION = "Lower Earth Empire 2: the moss on the brick wall by the water a row lower, and a second tuft beside it"

# Lower Earth Empire 2 (stage 4; see sta/aes/pocket_moss.sta) has a tuft of moss on its brick wall above the water:
# wall layer tiles 0x754 / 0x755 (palette 0xBA) at level cells (78-79, 38), surrounded by brick tiles 0x740-0x74F.
# The tuft is now a row lower at (78-79, 39), with a second one beside it at (80-81, 39) and plain bricks where it
# was.
#
# They're drawn over the wall by their own sprites (CHAINS). Those sprites are free in this stage, between the wall
# layer (109-131) and the next layer (150-170), and objects such as the hero are drawn after them. Each gameplay
# frame they're placed from the level camera (CAM_X / CAM_Y: level x = screen x + 0x10021A, level y = screen y -
# 0x10020E - 384) while on screen, and hidden otherwise. Leaving the stage hides them once (SHOWN). The hook is on
# the gameplay loop's call for the front object group (0x11804).
FRONT_CALL = 0x11804         # jsr 0xA3A6 - the front object group
STAGE = 4
ATTR = 0xBA70                # the wall's tile attributes (palette 0xBA)
CHAINS = [   # (first sprite, level cell x, top cell y, each column's tiles top to bottom)
    (140, 78, 38, [[0x743, 0x754], [0x744, 0x755]]),   # the tuft moved down, bricks where it was
    (142, 80, 39, [[0x754], [0x755]]),                 # the second tuft
]
SHOWN = 0x10E828             # byte
CAM_X, CAM_Y = 0x10021A, 0x10020E   # the level's own camera. 0x100216 / 0x10020A match it until a respawn moves
                                    # their origin, 1024 px over and up after dying by the wall


def chain_code(i, first, cx, cy, columns):
    rows = len(columns[0])
    tiles = ""
    for k, col in enumerate(columns):
        tiles += "    move.w #0x%X,0x3C0000\n" % ((first + k) * 64)
        for t in col:
            tiles += "    move.w #0x%X,0x3C0002\n    move.w #0x%X,0x3C0002\n" % (t, ATTR)
        tiles += "    move.w #0x%X,0x3C0000\n    move.w #0x0FFF,0x3C0002\n" % (0x8000 + first + k)
    sticky = "".join("    move.w #0x%X,0x3C0000\n    move.w #0x40,0x3C0002\n" % (0x8200 + first + k)
                     for k in range(1, len(columns)))
    return r"""
    move.w #%(x)d,%%d0                  | chain %(i)d: screen x = level x - camera x
    sub.w 0x%(cam_x)X,%%d0
    cmp.w #-%(w)d,%%d0
    blt 6%(i)df
    cmp.w #320,%%d0
    bgt 6%(i)df
    move.w #%(y)d+384,%%d1              | screen y = level y + camera y + 384
    add.w 0x%(cam_y)X,%%d1
    cmp.w #-%(h)d,%%d1
    blt 6%(i)df
    cmp.w #240,%%d1
    bgt 6%(i)df
%(tiles)s%(sticky)s
    neg.w %%d1                          | y (496 - screen y) and height
    add.w #496,%%d1
    and.w #511,%%d1
    lsl.w #7,%%d1
    or.w #%(rows)d,%%d1
    move.w #0x%(scb3)X,0x3C0000
    move.w %%d1,0x3C0002
    and.w #511,%%d0
    lsl.w #7,%%d0
    move.w #0x%(scb4)X,0x3C0000
    move.w %%d0,0x3C0002
    bra 7%(i)df
6%(i)d: move.w #0x%(scb3)X,0x3C0000      | off screen: hide it
    move.w #0,0x3C0002
7%(i)d:
""" % {"i": i, "x": cx * 16, "y": cy * 16, "w": 16 * len(columns), "h": 16 * rows, "cam_x": CAM_X, "cam_y": CAM_Y,
       "tiles": tiles, "sticky": sticky, "rows": rows, "scb3": 0x8200 + first, "scb4": 0x8400 + first}


def apply(rom):
    before = rom.u32(FRONT_CALL + 2)
    chains = "".join(chain_code(i, *c) for i, c in enumerate(CHAINS))
    hides = "".join("    move.w #0x%X,0x3C0000\n    move.w #0,0x3C0002\n" % (0x8200 + c[0]) for c in CHAINS)
    code = rom.place_code(r"""
    jsr 0x%(before)X
    movem.l %%d0-%%d1,-(%%sp)
    cmpi.b #%(stage)d,0x103005
    bne 8f
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
%(chains)s
    move.w (%%sp)+,%%sr
    st 0x%(shown)X
    bra 9f
8:  tst.b 0x%(shown)X                   | another stage: hide them, once
    beq 9f
    clr.b 0x%(shown)X
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
%(hides)s
    move.w (%%sp)+,%%sr
9:  movem.l (%%sp)+,%%d0-%%d1
    rts
""" % {"before": before, "stage": STAGE, "chains": chains, "hides": hides, "shown": SHOWN},
        why="Lower Earth Empire 2: the wall's moss")
    rom.write(FRONT_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + before.to_bytes(4, "big"), why="gameplay frame: the wall's moss")
