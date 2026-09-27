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
#
# The music: the Z80 sound driver (022-m1.m1) already has a pause and a resume, they are just never
# used by the game. Command 0xF2 (handled at Z80 0xD35D) copies the whole channel state (0x2C0 bytes
# at 0xF900) to a save area and silences everything; command 0xF3 (0xD36A) restores it and carries on
# where it left off. The game's pause and unpause routines (0x1541A / 0x15446) now queue those
# commands with the game's own sound queue (0xA27A), which its wait routine delivers every frame,
# including while the game is frozen.
PAUSE_ENTER = 0x1541A     # move.w 706(a6),d0 ; bset #3,d0   = 302E 02C2 08C0 0003
PAUSE_EXIT = 0x15446      # move.w 706(a6),d0 ; bclr #3,d0   = 302E 02C2 0880 0003
SOUND_PAUSE, SOUND_RESUME = 0xF2, 0xF3
QUEUE_SOUND = 0xA27A      # enqueue the sound command in d0
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
    for site, cmd, orig, why in ((PAUSE_ENTER, SOUND_PAUSE, "08C00003", "pause the music"),
                                 (PAUSE_EXIT, SOUND_RESUME, "08800003", "resume the music")):
        bit = "bset" if cmd == SOUND_PAUSE else "bclr"
        cave = rom.place_code(
            "    movem.l %%d0-%%d7/%%a0-%%a5,-(%%sp)\n"
            "    move.w #0x%02X,%%d0\n"
            "    jsr 0x%X\n"
            "    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a5\n"
            "    move.w 706(%%a6),%%d0\n"       # the two original instructions
            "    %s #3,%%d0\n"
            "    rts\n" % (cmd, QUEUE_SOUND, bit),
            why="sends the sound driver's %s command, then runs the original first two instructions" % why)
        rom.write(site, bytes.fromhex("4EB9") + cave.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  expect=bytes.fromhex("302E02C2" + orig), why=why + " when the game pauses / resumes")
    for site in CHECK_SITES:
        rom.write(site, bytes.fromhex("4EB9") + check.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
                  expect=bytes.fromhex("10390010FDAD0240000A"), why="pause / unpause on a new press of player 1 Start")
