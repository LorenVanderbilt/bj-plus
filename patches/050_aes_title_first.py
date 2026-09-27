NAME = "aes-title-first"
DESCRIPTION = "Home console (AES): boot to the title screen first, then the story cinema if nobody presses anything"

# The BIOS calls the game's USER routine (0x9400) with request 2 over and over. Request 2 (0x10674)
# alternates between two "cycles", and the first one (0x1083C) runs the story cinema (0x15472), which
# ends by dropping into the title screen. So a home console powered on showed the cinema first, with
# the title only after it, and Start during the cinema jumped straight into the game.
# The arcade cycle, second half, runs demo -> high scores -> item list -> title (0x10882 -> 0x1AE10).
#
# On the AES (system-mode byte 0x10FD82 is 0; the arcade sets bit 7) this patch turns the two cycles into
#     cycle 1:  TITLE (waits ~7 s, Start begins the game) -> story cinema
#     cycle 2:  demo -> high scores -> item list            (the title at the end is skipped: it now
#                                                            opens cycle 1, so it would show twice)
# The arcade keeps the original order.
CYCLE1 = 0x1083C   # clr.b 26624(a6) ; jsr 0x15472  (cinema) ; then tests 26624(a6) and returns
TITLE_CALL = 0x106D2   # jsr 0x10882 (title) ; bne 0x10DA0 (an rts either way)
QUEUE_MUSIC = 0x152FE
TITLE_BODY = 0x1AE10
CINEMA = 0x15472
START_GAME = 0x10CE8   # runs a whole game; the caller tail-jumps here when a start button was pressed
SYSTEM_MODE = 0x10FD82


def apply(rom):
    cycle1 = rom.place_code(
        "    clr.b 26624(%%a6)\n"
        "    tst.b 0x%X\n"
        "    bne.s 2f\n"                   # arcade: original order
        "    moveq #21,%%d0\n"             # title music, exactly what the original title call does
        "    jsr 0x%X\n"
        "    clr.b 26624(%%a6)\n"
        "    clr.b 30927(%%a6)\n"
        "    jsr 0x%X\n"                   # title screen
        "    tst.b 26624(%%a6)\n"
        "    beq.s 1f\n"
        "    jmp 0x%X\n"                   # Start pressed: play the game
        "1:  clr.b 26624(%%a6)\n"
        "2:  jsr 0x%X\n"                   # story cinema
        "    move.b 26624(%%a6),%%d0\n"
        "    beq.s 3f\n"
        "    jmp 0x%X\n"
        "3:  moveq #0,%%d0\n"
        "    rts\n" % (SYSTEM_MODE, QUEUE_MUSIC, TITLE_BODY, START_GAME, CINEMA, START_GAME),
        why="AES cycle 1: title first, then the story cinema (arcade: unchanged)")
    rom.write(CYCLE1, bytes.fromhex("4EF9") + cycle1.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("422E68004EB900015472"), why="start of the first attract cycle")

    skip = rom.place_code(
        "    tst.b 0x%X\n"
        "    beq.s 1f\n"                   # AES: no title here
        "    jsr 0x10882\n"
        "1:  rts\n" % SYSTEM_MODE,
        why="AES: skip the title at the end of the demo cycle (arcade: unchanged)")
    rom.write(TITLE_CALL, bytes.fromhex("4EF9") + skip.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("4EB9000108826600" "06C6"), why="end of the second attract cycle")
