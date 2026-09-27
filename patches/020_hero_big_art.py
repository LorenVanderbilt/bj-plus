NAME = "hero-big-art"
DESCRIPTION = "Draw the normal-size hero with the big (powerup) artwork; hitbox and gameplay unchanged"

# How the game picks a hero frame (see the notes in TODO.md): every object has an "art set"
# word at object+98 (0x104062 for player 1's hero): 0 = normal, 0x40 = shrunk (the C-button
# shrink), 0x80 = the big powerup form. The animation lookup at 0x434C4 adds it to the animation
# number to index the animation table, so animation N exists in three variants: N, 0x40+N and
# 0x80+N. This patch makes that lookup use the 0x80 (big) variants for the hero whenever its art
# set is 0 (normal), so the normal hero is drawn big. The shrunk and powerup forms are untouched.
# The hitbox is chosen separately (from the form byte at 0x107001), so it does not change.
LOOKUP = 0x434C4
HERO_OBJECTS = [0x104000]   # player 1's hero object; player 2's is checked later
BIG_SET = 0x80


def apply(rom):
    # Original:  D06D 0062  add.w  98(a5),d0   ; art set + animation number
    #            D040       add.w  d0,d0       ; (x4 to index a table of longs, with the next D040)
    # Replace those 6 bytes with `jsr cave`; the cave repeats both instructions, adding the
    # big-art offset in between when this is the hero and its art set is 0.
    checks = "".join(
        "    cmpa.l #0x%X,%%a5\n    beq hero\n" % obj for obj in HERO_OBJECTS)
    cave = rom.place_code(
        "    add.w 98(%%a5),%%d0\n"
        "%s"
        "    bra done\n"
        "hero:\n"
        "    tst.w 98(%%a5)\n"
        "    bne done\n"
        "    add.w #%d,%%d0\n"
        "done:\n"
        "    add.w %%d0,%%d0\n"
        "    rts\n" % (checks, BIG_SET),
        why="animation lookup: use the big variants for the normal-size hero")
    rom.write(LOOKUP, bytes.fromhex("4EB9") + cave.to_bytes(4, "big"),
              expect=bytes.fromhex("D06D0062D040"), why="animation lookup now goes through the cave")
