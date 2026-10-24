NAME = "throw-follow-linger"
DESCRIPTION = "The big hero's throw: its last pose, the follow-through, held a little longer"

# The animation player (0x434A8) gives every step of an animation the same length: the object's +0x60 (frames - 1;
# 2 for the throws), its +0x61 counting up to it (STEP_TEST). Its lists hold only frame numbers (and must lie within
# 0x68800-0x787FF), so a step can't simply be listed twice there without moving lists. Instead the test gives a
# hero's follow-through (FOLLOW: hero-big-art's THROW_FOLLOW, the throws' last step) EXTRA more frames.
# (Its own patch, last, so its code moves nothing.)
STEP_TEST = 0x434F6            # move.b 0x60(a5),d0 ; cmp.b 0x61(a5),d0 (then bcc: the step goes on)
FOLLOW = 0x9C
EXTRA = 4                      # frames (a step is 3)
HEROES = (0x104000, 0x104080)


def apply(rom):
    code = rom.place_code("""
    move.b 0x60(%%a5),%%d0
    cmpi.w #0x%(follow)X,8(%%a5)       | the follow-through ...
    bne 1f
    cmpa.l #0x%(p1)X,%%a5              | ... of a hero: longer
    beq 2f
    cmpa.l #0x%(p2)X,%%a5
    bne 1f
2:  addq.b #%(extra)d,%%d0
1:  cmp.b 0x61(%%a5),%%d0
    rts
""" % {"follow": FOLLOW, "extra": EXTRA, "p1": HEROES[0], "p2": HEROES[1]}, why="the throw's follow-through held longer")
    rom.write(STEP_TEST, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("102D0060B02D0061"), why="animation step: the hero's follow-through longer")
