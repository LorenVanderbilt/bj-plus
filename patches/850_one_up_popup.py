NAME = "one-up-popup"
DESCRIPTION = "1UP (the gold cocoon): its pop-up in invincible-points' style - the small gold font, rising, slowing and fading"

# The game's score pop-ups (0x5E132 / 0x5E158 -> 0x5E17C: a new object, code 0x5E1CE, rising 64 frames) take their
# frame from a table (0x5E1E6): points, and 1UP (ONE_UP_FRAME - the gold cocoon, ...). The 1UP one is now handed to
# invincible-points' pop-up (its code's first entry; frame base in +0x52, +0x29 clear to start it): "1UP" in its small
# gold font (palette 6, black outline), above the head of the hero who got it (UP / RIGHT), rising and slowing, thinned out at the
# end, gone. Its frames: the text and its fade (two tiles each). Hooked at the pop-up set-up's last instruction
# (SET_UP_END). The fruit's points next. (Its own patch, last, so its code moves nothing.)
import importlib.util
import os

SET_UP_END = 0x5E1C6           # move.w #64,0x78(a1) ; rts - the pop-up set up (a1)
ONE_UP_FRAME = 0x2FD0
POINTS_SITE = 0x42C9E          # invincible-points' first hook: jsr <its code + 4>
UP, RIGHT = 28, 16             # px: from the hero who got it (his x / y fields: the pop-up then starts above his head,
                               # centred - the game put it by the item, level with his head)
HEROES = (0x104000, 0x104080)  # players 1 / 2's hero objects
HERO_CODE = 0x3BD10            # (a hero's +4 while he's playing)
GLYPHS = {
    "1": [".1.", "11.", ".1.", ".1.", ".1.", ".1.", "111"],
    "U": ["1..1", "1..1", "1..1", "1..1", "1..1", "1..1", ".11."],
    "P": ["111.", "1..1", "1..1", "111.", "1...", "1...", "1..."],
}


def apply(rom):
    spec = importlib.util.spec_from_file_location("inv", os.path.join(os.path.dirname(__file__),
                                                                       "740_invincible_points.py"))
    inv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inv)
    inv.GLYPHS.update(GLYPHS)
    popup = rom.u32(POINTS_SITE + 2) - 4
    assert rom.u16(popup) == 0x6000, "invincible-points' code moved"
    frames = []
    for fade in range(len(inv.FADES) + 1):
        pic = inv.picture("1UP", fade)
        tiles = [rom.add_sprite_tile([row[c * 16:c * 16 + 16] for row in pic], share=True,
                                     why="1UP pop-up (fade %d)" % fade) for c in range(2)]
        frames.append(rom.add_frame([tiles], inv.PALETTE, why="1UP pop-up (fade %d)" % fade))
    assert frames == [frames[0] + 4 * f for f in range(len(frames))]
    code = rom.place_code("""
    move.w #64,0x78(%%a1)
    cmpi.w #0x%(one_up)X,8(%%a1)
    bne 9f
    move.l #0x%(popup)X,4(%%a1)        | (invincible-points' pop-up)
    move.w #%(frame)d,0x52(%%a1)
    clr.b 0x29(%%a1)
    movem.l %%d0-%%d1/%%a0,-(%%sp)
    lea 0x%(hero1)X,%%a0               | (player 2's hero if he's playing and nearer the game's place)
    cmpi.l #0x%(hero_code)X,0x%(hero2)X+4
    bne 1f
    move.w 2(%%a1),%%d0
    sub.w 0x%(hero1)X+2,%%d0
    bpl 2f
    neg.w %%d0
2:  move.w 2(%%a1),%%d1
    sub.w 0x%(hero2)X+2,%%d1
    bpl 3f
    neg.w %%d1
3:  cmp.w %%d0,%%d1
    bcc 1f
    lea 0x%(hero2)X,%%a0
1:  move.l (%%a0),(%%a1)
    addi.w #%(up)d,(%%a1)
    addi.w #%(right)d,2(%%a1)
    movem.l (%%sp)+,%%d0-%%d1/%%a0
9:  rts
""" % {"one_up": ONE_UP_FRAME, "popup": popup, "frame": frames[0], "up": UP * 128, "right": (RIGHT - 16) * 128,
       "hero1": HEROES[0], "hero2": HEROES[1], "hero_code": HERO_CODE},
        why="1UP pop-up: invincible-points' style")
    rom.write(SET_UP_END, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("337C00400078"),
              why="score pop-up set up: the 1UP one in the small gold style")
