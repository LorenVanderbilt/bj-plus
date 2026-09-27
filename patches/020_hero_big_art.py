NAME = "hero-big-art"
DESCRIPTION = "Draw the normal-size hero with the big (powerup) artwork; hitbox and gameplay unchanged"

# How the game picks a hero frame: every object has an "art set" word at object+98 (0x104062 for
# player 1's hero): 0 = normal, 0x40 = shrunk (the C-button shrink), 0x80 = the big powerup form.
# The animation lookup at 0x434C4 adds it to the animation number to index the animation table,
# so animation N exists in three variants: N, 0x40+N and 0x80+N. This patch makes that lookup use
# the 0x80 (big) variants for the hero whenever its art set is 0 (normal). The shrunk and powerup
# forms are untouched, and the hitbox is chosen separately (from the form byte at 0x107001), so it
# does not change.
#
# The big art is drawn from the same top-left anchor as the small art, so it hangs lower and
# extends further right than it should. The sprite drawing routine (0xA5B2-0xA6E0) writes each
# object's position to the video chip in two variants (the plain one, and one used while the object
# is being zoomed during transformation animations); an object's first word (a0@(0)) becomes its
# SCB3 Y and its second word (a0@(2)) its SCB4 X. Four small hooks nudge the hero's big art back:
#   * up by HERO_UP_PX pixels (SCB3 is 496-y in units of 128 per pixel, so bigger = higher),
#   * left by HERO_LEFT_PX pixels facing right, or HERO_LEFT_PX_FACING_LEFT facing left (both measured).
# The genuine powerup (art set 0x80) is left alone: the game already shifts the hero on pickup.
LOOKUP = 0x434C4
HERO_OBJECTS = [0x104000, 0x104080]   # the objects for player 1 and player 2
BIG_SET = 0x80
HERO_UP_PX = 15
HERO_LEFT_PX = 5           # facing right: the big art is centred ~5px right of the small art's centre
HERO_LEFT_PX_FACING_LEFT = 10   # facing left: it sits ~10px right of centre (measured), so it needs twice the nudge

DRAW_X_ZOOMED = 0xA604    # subi.w #0x4000,d5 ; move.w #256,d6
DRAW_X_PLAIN = 0xA6AA     # subi.w #0x4000,d6 ; move.w d6,(a2)
DRAW_Y_ZOOMED = 0xA64A    # subi.w #-18433,d5 ; moveq #1,d6
DRAW_Y_PLAIN = 0xA6C0     # subi.w #-18433,d7 ; add.w d3,d7 ; move.w d7,(a2)
# The hero is drawn as a main sprite (the four hooks above) plus extra pieces written by the routine
# at 0xAF1C, whose base position is built here as d7 = (Y << 16) | X:
#   subi.w #-18433,d7 ; swap d7 ; move.w 664(a6),d7 ; subi.w #0x4000,d7
PIECES_BASE = 0xA6E6
# All of the above is the variant for a hero facing RIGHT (the game draws left-facing art and flips
# it: the main drawing function at 0xA426 jumps to 0xA67A when bit 7 of object+33 is set). A hero
# facing LEFT and not being zoomed is drawn by an inline copy of the same three steps instead:
LEFT_X = 0xA480           # subi.w #0x4000,d5 ; move.w d5,(a2)
LEFT_Y = 0xA496           # subi.w #-18433,d7 ; add.w d3,d7 ; move.w d7,(a2)
LEFT_PIECES = 0xA4BE      # subi.w #-18433,d7 ; swap d7 ; move.w 2(a0),d7 ; subi.w #0x4000,d7


import os
_DEBUG_MARKS = bool(os.environ.get("BJ_DEBUG_MARKS"))   # diagnostic build: count hero draws per hook
_marks = {}


def hero_only(reg, body, tag=""):
    """68000 source that runs `body` only for our hero (in the normal-size form), else skips it.
    `tag` makes the labels unique when one routine uses this more than once."""
    checks = "".join("    cmpa.l #0x%X,%%%s\n    beq hero%s\n" % (obj, reg, tag) for obj in HERO_OBJECTS)
    mark = ""
    if _DEBUG_MARKS:
        mark = "    addq.b #1,0x%X\n" % (0x10C000 + len(_marks))
        _marks[len(_marks)] = tag
    return (checks + "    bra done%s\nhero%s:\n%s    tst.w 98(%%%s)\n    bne done%s\n%sdone%s:\n"
            % (tag, tag, mark, reg, tag, body, tag))


def x_shift(dreg, px=None):
    return "    sub.w #%d,%%%s\n" % ((HERO_LEFT_PX if px is None else px) * 128, dreg)


def y_shift(dreg):
    return "    add.w #%d,%%%s\n" % (HERO_UP_PX * 128, dreg)


def hook(rom, site, expect_hex, source, why):
    """Replace the instructions at `site` (expect_hex) with a jsr into new code holding `source`."""
    expect = bytes.fromhex(expect_hex)
    assert len(expect) >= 6
    cave = rom.place_code(source, why=why)
    rom.write(site, bytes.fromhex("4EB9") + cave.to_bytes(4, "big") + bytes.fromhex("4E71") * ((len(expect) - 6) // 2),
              expect=expect, why="now goes through the new code above")


def apply(rom):
    # Animation lookup: `add.w 98(a5),d0 ; add.w d0,d0` -> add the big-art offset for the hero.
    checks = "".join("    cmpa.l #0x%X,%%a5\n    beq hero\n" % obj for obj in HERO_OBJECTS)
    hook(rom, LOOKUP, "D06D0062D040",
         "    add.w 98(%%a5),%%d0\n%s    bra done\nhero:\n    tst.w 98(%%a5)\n    bne done\n"
         "    add.w #%d,%%d0\ndone:\n    add.w %%d0,%%d0\n    rts\n" % (checks, BIG_SET),
         "animation lookup: use the big variants for the normal-size hero")

    hook(rom, DRAW_X_ZOOMED, "044540003C3C0100",
         "    sub.w #0x4000,%d5\n" + hero_only("a0", x_shift("d5")) + "    move.w #256,%d6\n    rts\n",
         "sprite X (zoomed path)")
    hook(rom, DRAW_X_PLAIN, "044640003486",
         "    sub.w #0x4000,%d6\n" + hero_only("a0", x_shift("d6")) + "    move.w %d6,(%a2)\n    rts\n",
         "sprite X (usual path)")
    hook(rom, DRAW_Y_ZOOMED, "0445B7FF7C01",
         "    sub.w #-18433,%d5\n" + hero_only("a0", y_shift("d5")) + "    moveq #1,%d6\n    rts\n",
         "sprite Y (zoomed path)")
    hook(rom, DRAW_Y_PLAIN, "0447B7FFDE433487",
         "    sub.w #-18433,%d7\n    add.w %d3,%d7\n" + hero_only("a0", y_shift("d7")) + "    move.w %d7,(%a2)\n    rts\n",
         "sprite Y (usual path)")
    hook(rom, PIECES_BASE, "0447B7FF48473E2E029804474000",
         "    sub.w #-18433,%d7\n" + hero_only("a0", y_shift("d7"), "y") +
         "    swap %d7\n    move.w 664(%fp),%d7\n    sub.w #0x4000,%d7\n" + hero_only("a0", x_shift("d7"), "x") +
         "    rts\n",
         "sprite pieces' base position")

    # The same three hooks for the hero facing left.
    hook(rom, LEFT_X, "044540003485",
         "    sub.w #0x4000,%d5\n" + hero_only("a0", x_shift("d5", HERO_LEFT_PX_FACING_LEFT), "lx") + "    move.w %d5,(%a2)\n    rts\n",
         "sprite X (facing left)")
    hook(rom, LEFT_Y, "0447B7FFDE433487",
         "    sub.w #-18433,%d7\n    add.w %d3,%d7\n" + hero_only("a0", y_shift("d7"), "ly") + "    move.w %d7,(%a2)\n    rts\n",
         "sprite Y (facing left)")
    hook(rom, LEFT_PIECES, "0447B7FF48473E28000204474000",
         "    sub.w #-18433,%d7\n" + hero_only("a0", y_shift("d7"), "py") +
         "    swap %d7\n    move.w 2(%a0),%d7\n    sub.w #0x4000,%d7\n" + hero_only("a0", x_shift("d7", HERO_LEFT_PX_FACING_LEFT), "px") +
         "    rts\n",
         "sprite pieces' base position (facing left)")
