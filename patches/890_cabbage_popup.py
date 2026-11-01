NAME = "cabbage-popup"
DESCRIPTION = "The cabbage: its 10000 points pop-up in invincible-points' style, above the hero's head, like the fruit's"

# The cabbage (pickup type 10) shows a 10000 score pop-up (CABBAGE_FRAME). Like the fruit, it now uses
# invincible-points' pop-up: "+10000" in the small gold font, rising from above the hero's head (lower over a shrunk
# hero), then fading. It costs 4 tiles, which dev-tiles freed up. This chains into fruit-popup's hook at the end of
# the pop-up set-up (SET_UP_END).
SET_UP_END = 0x5E1C6           # jsr <fruit-popup>
CABBAGE_FRAME, TEXT = 0x3200, "+10000"


def apply(rom):
    inv, one, fruit = (rom.other_patch("invincible-points"), rom.other_patch("one-up-popup"),
                       rom.other_patch("fruit-popup"))
    inv.GLYPHS.update(one.GLYPHS)
    popup = rom.u32(one.POINTS_SITE + 2) - 4
    assert rom.u16(SET_UP_END) == 0x4EB9
    before = rom.u32(SET_UP_END + 2)
    frames = []
    for fade in range(len(inv.FADES) + 1):
        pic = inv.picture(TEXT, fade)
        tiles = [rom.add_sprite_tile([row[c * 16:c * 16 + 16] for row in pic], share=True,
                                     why="cabbage pop-up (fade %d)" % fade) for c in range(2)]
        frames.append(rom.add_frame([tiles], inv.PALETTE, why="cabbage pop-up (fade %d)" % fade))
    assert frames == [frames[0] + 4 * f for f in range(len(frames))]
    code = rom.place_code("""
    jsr 0x%(before)X                    | the fruit and 1UP checks first
    cmpi.w #0x%(frame)X,8(%%a1)
    beq 5f
    rts
5:  move.w #%(base)d,0x52(%%a1)
    move.l #0x%(popup)X,4(%%a1)        | invincible-points' pop-up
    clr.b 0x29(%%a1)
    movem.l %%d0-%%d1/%%a0/%%a2,-(%%sp)
    lea 0x%(hero1)X,%%a0               | player 2's hero if he's playing and nearer
    lea 0x%(block1)X,%%a2
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
    lea 0x%(block2)X,%%a2
1:  move.l (%%a0),(%%a1)                | above his head
    addi.w #%(up)d,(%%a1)
    addi.w #%(right)d,2(%%a1)
    tst.b 1(%%a2)                       | shrunk: start lower
    bne 4f
    subi.w #%(drop)d,(%%a1)
4:  movem.l (%%sp)+,%%d0-%%d1/%%a0/%%a2
    rts
""" % {"before": before, "frame": CABBAGE_FRAME, "base": frames[0], "popup": popup, "hero1": one.HEROES[0],
       "hero2": one.HEROES[1], "block1": fruit.BLOCKS[0], "block2": fruit.BLOCKS[1], "hero_code": one.HERO_CODE,
       "up": one.UP * 128, "right": (one.RIGHT - 16) * 128, "drop": fruit.SHRUNK_DROP * 128},
        why="cabbage pop-up: invincible-points' style")
    rom.write(SET_UP_END + 2, code.to_bytes(4, "big"), expect=before.to_bytes(4, "big"),
              why="score pop-up set up: the cabbage's in the small gold style too")
