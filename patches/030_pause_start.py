NAME = "pause-start"
DESCRIPTION = "Pause the game with the Start button (the game's own pause is on Select, which arcade panels lack)"

# The game already has a pause. Its main loop at 0x11ABC checks the BIOS button-change byte
# 0x10FDAD for the SELECT buttons (bits 1 and 3, mask 0x0A): a press calls 0x1541A (prints PAUSE and
# freezes the hardware tile animation), the loop then waits a frame at a time until SELECT is pressed
# again, and 0x15446 resumes (erases PAUSE). Select does not exist on an arcade (MVS) panel and the
# open-source AES BIOS does not report it, so the pause was unreachable in MAME.
#
# This patch checks player 1's START instead (bit 0; bit 2 is player 2's, which is how player 2 joins,
# so it is left alone). It also detects the press itself rather than trusting 0x10FDAD: the official
# BIOS sets that "changed" byte for one frame per press, but the open-source AES BIOS keeps it set
# for as long as the button is held, which made the pause flip on and off every frame. So the check
# below looks at the "current" byte 0x10FDAC and remembers last frame's state in spare RAM.
CHECK_SITES = [0x11AC0, 0x11B06]   # move.b 0x10FDAD,d0 ; andi.w #10,d0  = 1039 0010 FDAD 0240 000A
PREV_STATE = 0x10C100              # one spare byte of RAM (0x10A3B0-0x10F2FF is unused by the game)


def apply(rom):
    check = rom.place_code(
        "    move.l %%d1,-(%%sp)\n"
        "    moveq #0,%%d0\n"
        "    move.b 0x10FDAC,%%d0\n"      # current buttons
        "    and.b #1,%%d0\n"              # player 1 Start
        "    move.b 0x%X,%%d1\n"           # was it down last frame?
        "    move.b %%d0,0x%X\n"
        "    not.b %%d1\n"
        "    and.b %%d1,%%d0\n"            # down now and not before = a new press
        "    move.l (%%sp)+,%%d1\n"
        "    tst.b %%d0\n"                 # Z set = no new press (what the caller's beq tests)
        "    rts\n" % (PREV_STATE, PREV_STATE),
        why="Start press detector (returns Z clear on a new press)")
    for site in CHECK_SITES:
        rom.write(site, bytes.fromhex("4EB9") + check.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
                  expect=bytes.fromhex("10390010FDAD0240000A"), why="pause / unpause on a new press of player 1 Start")
