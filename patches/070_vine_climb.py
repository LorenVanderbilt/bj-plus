NAME = "vine-climb"
DESCRIPTION = "Press Up/Down to slide along a vine instead of being stuck in place"

# Found by tracing a recorded vine-touch (recordings/vine.inp) with tools/find_writer.py: the hero's
# position froze completely (Y=0x7A74, X=0x8BF4 for 13+ seconds, then death) because the per-frame
# "on vine" state handler at 0x3C74A never gives the hero any vertical velocity, and nothing reads the
# joystick while this state is active. The hero's Y-velocity ("vy") lives at object offset +12 (added
# into the Y position, offset +0, by the shared position-integrator at 0xA258 that runs every frame
# regardless of state) - it's simply always 0 while grabbing a vine, so the position never changes.
#
# State 3 ("grabbing a vine") is entered at 0x3C730 and its per-frame handler at 0x3C74A is reached only
# through a stored function pointer (object offset +108), so it's hooked here at its own fixed address
# rather than at a call site. Each frame, before any of the state's own logic runs, this reads
# BIOS_P1CURRENT (0x10FD96: bit 0 = Up, bit 1 = Down, both held-down/active-high - see ngdevkit's
# asm/bios-ram.h) and sets vy to climb up, down, or hold still. It's rewritten every frame, so it wins
# over anything the state's own logic does to vy afterwards (e.g. it clears vy under some conditions).
#
# Not done / unverified: which way the hero actually moves on screen for a given vy sign (Y-down-screen
# is assumed, i.e. negative vy = up), whether CLIMB_SPEED feels right, and whether the state's own exit
# check (0x42B0E, which detects leaving the vine) still triggers correctly while sliding - all needs
# real play-testing, not just the static recording. Chosen deliberately >= 512 (2 px/frame in the
# game's 8.8 fixed point) because the handler has a special case that nudges Y by another 160 units
# when 0 < |vy| < 512, which a slower climb speed would trigures on every frame.
HANDLER = 0x3C74A
BIOS_P1CURRENT = 0x10FD96
CLIMB_SPEED = 512


def apply(rom):
    cave = rom.place_code(
        "    move.l %%d0,-(%%sp)\n"
        "    moveq #0,%%d0\n"
        "    move.b 0x%X,%%d0\n"        # BIOS_P1CURRENT
        "    btst #0,%%d0\n"            # Up
        "    beq.s 1f\n"
        "    move.w #-%d,12(%%a5)\n"    # vy = -CLIMB_SPEED (up)
        "    bra.s 3f\n"
        "1:  btst #1,%%d0\n"            # Down
        "    beq.s 2f\n"
        "    move.w #%d,12(%%a5)\n"     # vy = CLIMB_SPEED (down)
        "    bra.s 3f\n"
        "2:  clr.w 12(%%a5)\n"          # neither: hold still
        "3:  move.l (%%sp)+,%%d0\n"
        "    jsr 0x42B0E\n"             # the original first instruction
        "    jmp 0x%X\n" % (BIOS_P1CURRENT, CLIMB_SPEED, CLIMB_SPEED, HANDLER + 6),
        why="read Up/Down and set the vine vertical speed before the state's own logic runs")
    rom.write(HANDLER, bytes.fromhex("4EF9") + cave.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB900042B0E"), why="hook the per-frame vine-holding handler")
