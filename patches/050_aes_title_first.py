NAME = "aes-title-first"
DESCRIPTION = "Home console (AES): boot to the title screen, then the story cinema; any button in the cinema returns to the title"

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
# and changes the cinema:
#   * no blinking "PUSH START" (each of the four story scenes calls the shared 0x1B034 text routine once
#     per frame; that call now goes to a small check routine instead),
#   * any button press (A/B/C/D of either player, or a Start) ends the cinema and shows the title again.
# Start is special: the BIOS itself notices it and calls the game's PLAYER_START entry (0x108DA), which
# would begin a game. While a cinema scene is running (a flag the check routine refreshes every frame, and
# the shared text routine, which the title and other screens call, clears) that entry now just forgets the
# request and sets the "abort" flag, so Start behaves like any other button.
# The arcade keeps the original behaviour everywhere.
CYCLE1 = 0x1083C       # clr.b 26624(a6) ; jsr 0x15472 (cinema) ; then tests 26624(a6) and returns
TITLE_CALL = 0x106D2   # jsr 0x10882 (title) ; bne 0x10DA0 (an rts either way)
PUSH_START_CALLS = [0x34B64, 0x35050, 0x353D6, 0x356C2]   # jsr 0x1B034, one per story scene loop
PUSH_START = 0x1B034   # jsr 0x5F050 ; beq 0x1B076 ...     (draws / blinks "PUSH START" or "INSERT COIN")
PLAYER_START = 0x108DA  # tst.b 0x10F000 ; bne 0x10C8C ...  (BIOS calls this when a Start button is pressed)
QUEUE_MUSIC = 0x152FE
TITLE_BODY = 0x1AE10
CINEMA = 0x15472
CLEAR_TEXT = 0x15696   # blanks the text layer
START_GAME = 0x10CE8   # runs a whole game; the caller tail-jumps here when a start button was pressed
SYSTEM_MODE = 0x10FD82
P1_CURRENT, P2_CURRENT = 0x10FD96, 0x10FD9C   # BIOS: buttons held (bits 4-7 = A B C D)
START_FLAGS = 0x10FDB4                        # BIOS: bit 0 / 1 = player 1 / 2 pressed Start
START_FLAG_OF_GAME = 0x106800                 # game: non-zero ends an attract screen / starts a game
IN_CINEMA = 0x10C110    # spare RAM: MAGIC while a story scene runs
ABORT = 0x10C111        # spare RAM: 1 = a button was pressed in the cinema
MAGIC = 0xA5


def apply(rom):
    cycle1 = rom.place_code(
        "    clr.b 26624(%%a6)\n"
        "    tst.b 0x%X\n"
        "    bne.s arcade\n"
        "title:\n"
        "    moveq #21,%%d0\n"             # title music, exactly what the original title call does
        "    jsr 0x%X\n"
        "    clr.b 26624(%%a6)\n"
        "    clr.b 30927(%%a6)\n"
        "    jsr 0x%X\n"                   # title screen
        "    tst.b 26624(%%a6)\n"
        "    beq.s 1f\n"
        "    jmp 0x%X\n"                   # Start pressed: play the game
        "1:  clr.b 26624(%%a6)\n"
        "    clr.b 0x%X\n"
        "    jsr 0x%X\n"                   # story cinema
        "    clr.b 0x%X\n"
        "    tst.b 0x%X\n"
        "    beq.s 2f\n"
        "    clr.b 0x%X\n"                 # a button was pressed: back to the title
        "    clr.b 26624(%%a6)\n"
        "    jsr 0x%X\n"
        "    bra.s title\n"
        "2:  move.b 26624(%%a6),%%d0\n"
        "    beq.s 3f\n"
        "    jmp 0x%X\n"
        "3:  moveq #0,%%d0\n"
        "    rts\n"
        "arcade:\n"
        "    jsr 0x%X\n"
        "    move.b 26624(%%a6),%%d0\n"
        "    beq.s 4f\n"
        "    jmp 0x%X\n"
        "4:  moveq #0,%%d0\n"
        "    rts\n" % (SYSTEM_MODE, QUEUE_MUSIC, TITLE_BODY, START_GAME, ABORT, CINEMA, IN_CINEMA,
                       ABORT, ABORT, CLEAR_TEXT, START_GAME, CINEMA, START_GAME),
        why="AES cycle 1: title, then the story cinema, back to the title on a button (arcade: unchanged)")
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

    check = rom.place_code(
        "    tst.b 0x%X\n"
        "    beq.s 1f\n"
        "    jmp 0x%X\n"                   # arcade: the original PUSH START routine
        "1:  move.b #0x%X,0x%X\n"          # a story scene is running
        "    move.b 0x%X,%%d0\n"
        "    or.b 0x%X,%%d0\n"
        "    and.b #0xF0,%%d0\n"           # A B C D of either player
        "    beq.s 2f\n"
        "    move.b #1,0x%X\n"
        "2:  tst.b 0x%X\n"
        "    beq.s 3f\n"
        "    move.b #1,0x%X\n"             # makes the scene loop (and the cinema) end
        "3:  rts\n" % (SYSTEM_MODE, PUSH_START, MAGIC, IN_CINEMA, P1_CURRENT, P2_CURRENT, ABORT, ABORT,
                       START_FLAG_OF_GAME),
        why="cinema scenes, once per frame: watch for a button instead of drawing PUSH START")
    for site in PUSH_START_CALLS:
        rom.write(site, bytes.fromhex("4EB9") + check.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB90001B034"), why="story scene loop: no PUSH START, check for a button")

    leave = rom.place_code(
        "    clr.b 0x%X\n"                 # any other screen is not the cinema
        "    jsr 0x5F050\n"                # the two original instructions' worth
        "    jmp 0x%X\n" % (IN_CINEMA, PUSH_START + 6),
        why="the PUSH START routine (title, demo, ...) marks the cinema as over")
    rom.write(PUSH_START, bytes.fromhex("4EF9") + leave.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90005F050"), why="PUSH START routine entry")

    start = rom.place_code(
        "    cmp.b #0x%X,0x%X\n"
        "    bne.s 1f\n"
        "    and.b #0xFC,0x%X\n"           # forget the Start request
        "    move.b #1,0x%X\n"
        "    rts\n"
        "1:  tst.b 0x10F000\n"             # the original first instruction
        "    jmp 0x%X\n" % (MAGIC, IN_CINEMA, START_FLAGS, ABORT, PLAYER_START + 6),
        why="BIOS PLAYER_START: in the cinema a Start press only ends the cinema")
    rom.write(PLAYER_START, bytes.fromhex("4EF9") + start.to_bytes(4, "big"),
              expect=bytes.fromhex("4A390010F000"), why="PLAYER_START entry")
