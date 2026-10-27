NAME = "fruit-popup"
DESCRIPTION = "Fruit: its points pop-up (+100 / +150) in invincible-points' style, above the hero's head, like the 1UP's"

# The fruit (pickup types 48-52) shows score pop-ups 100 or 150 (the pop-ups' frames FRUIT_FRAMES). Like one-up-popup's
# 1UP, those now go to invincible-points' pop-up: "+100" / "+150" in its small gold font, from above the head of the
# hero who got it, rising, slowing, thinned out, gone. 8 tiles (creature-tiles freed the room). one-up-popup's hook
# at the pop-up set-up's end (SET_UP_END) now calls ours first. Over a shrunk hero (form 0) these and the 1UP start
# SHRUNK_DROP px lower.
import importlib.util
import os

SET_UP_END = 0x5E1C6           # jsr <one-up-popup's> (was move.w #64,0x78(a1))
FRUIT_FRAMES = {0x31C8: "+100", 0x31E4: "+150"}
BLOCKS = (0x107000, 0x107400)  # players 1 / 2's blocks (+1: the form - 0 shrunk)
SHRUNK_DROP = 26               # px lower over a shrunk hero (one-up-popup's UP is for the big one)


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def apply(rom):
    inv, one = load("740_invincible_points"), load("850_one_up_popup")
    inv.GLYPHS.update(one.GLYPHS)
    popup = rom.u32(one.POINTS_SITE + 2) - 4
    assert rom.u16(SET_UP_END) == 0x4EB9
    one_up = rom.u32(SET_UP_END + 2)
    bases = {}
    for frame, text in FRUIT_FRAMES.items():
        frames = []
        for fade in range(len(inv.FADES) + 1):
            pic = inv.picture(text, fade)
            tiles = [rom.add_sprite_tile([row[c * 16:c * 16 + 16] for row in pic], share=True,
                                         why="fruit pop-up %s (fade %d)" % (text, fade)) for c in range(2)]
            frames.append(rom.add_frame([tiles], inv.PALETTE, why="fruit pop-up %s (fade %d)" % (text, fade)))
        assert frames == [frames[0] + 4 * f for f in range(len(frames))]
        bases[frame] = frames[0]
    checks = "".join("""
    cmpi.w #0x%X,8(%%a1)
    bne 1f
    move.w #%d,0x52(%%a1)
    bra 5f
1:""" % (frame, base) for frame, base in bases.items())
    code = rom.place_code("""
    jsr 0x%(one_up)X                    | (the 1UP's: its set-up's last instruction, then the 1UP above the hero)%(checks)s
    cmpi.l #0x%(popup)X,4(%%a1)        | (not fruit: the 1UP's, just started? - then only the shrunk hero's drop)
    bne 9f
    tst.b 0x29(%%a1)
    bne 9f
    movem.l %%d0-%%d1/%%a0/%%a2,-(%%sp)
    bsr hero
    bra 6f
5:  move.l #0x%(popup)X,4(%%a1)        | (invincible-points' pop-up)
    clr.b 0x29(%%a1)
    movem.l %%d0-%%d1/%%a0/%%a2,-(%%sp)
    bsr hero
    move.l (%%a0),(%%a1)                | above his head
    addi.w #%(up)d,(%%a1)
    addi.w #%(right)d,2(%%a1)
6:  tst.b 1(%%a2)                       | (shrunk: lower, nearer his head)
    bne 7f
    subi.w #%(drop)d,(%%a1)
7:  movem.l (%%sp)+,%%d0-%%d1/%%a0/%%a2
9:  rts

hero:                                   | a0 / a2: the hero who got it, his player block (player 2's if he's
    lea 0x%(hero1)X,%%a0               | playing and nearer the game's place)
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
1:  rts
""" % {"one_up": one_up, "checks": checks, "popup": popup, "hero1": one.HEROES[0], "hero2": one.HEROES[1],
       "block1": BLOCKS[0], "block2": BLOCKS[1], "hero_code": one.HERO_CODE, "up": one.UP * 128,
       "right": (one.RIGHT - 16) * 128, "drop": SHRUNK_DROP * 128},
        why="fruit pop-ups: invincible-points' style; any pop-up lower over a shrunk hero")
    rom.write(SET_UP_END + 2, code.to_bytes(4, "big"), expect=one_up.to_bytes(4, "big"),
              why="score pop-up set up: the fruit's in the small gold style too")
