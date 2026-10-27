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
PUSH_START_FIRST = 0x5F050
TITLE = 0x10882        # the arcade cycle's title call
QUEUE_MUSIC = 0x152FE
TITLE_BODY = 0x1AE10
CINEMA = 0x15472
CLEAR_TEXT = 0x15696   # blanks the text layer
START_GAME = 0x10CE8   # runs a whole game; the caller tail-jumps here when a start button was pressed
SYSTEM_MODE = 0x10FD82
P1_CURRENT, P2_CURRENT = 0x10FD96, 0x10FD9C   # BIOS: buttons held (bits 4-7 = A B C D)
START_FLAGS = 0x10FDB4                        # BIOS: bit 0 / 1 = player 1 / 2 pressed Start
START_FLAG_OF_GAME = 0x106800                 # game: non-zero ends an attract screen / starts a game
IN_CINEMA = 0x10E810    # spare RAM: MAGIC while a story scene runs
ABORT = 0x10E811        # spare RAM: 1 = a button was pressed in the cinema
MAGIC = 0xA5


def apply(rom):
    names = {"system_mode": SYSTEM_MODE, "queue_music": QUEUE_MUSIC, "title_body": TITLE_BODY, "title": TITLE,
             "start_game": START_GAME, "abort": ABORT, "cinema": CINEMA, "in_cinema": IN_CINEMA,
             "clear_text": CLEAR_TEXT, "push_start": PUSH_START, "push_start_first": PUSH_START_FIRST,
             "push_start_rest": PUSH_START + 6, "magic": MAGIC, "p1": P1_CURRENT, "p2": P2_CURRENT,
             "start_of_game": START_FLAG_OF_GAME, "start_flags": START_FLAGS, "player_start_rest": PLAYER_START + 6}
    cycle1 = rom.place_code(r"""
    clr.b 26624(%%a6)
    tst.b 0x%(system_mode)X
    bne.s arcade
title:
    moveq #21,%%d0                      | title music, exactly what the original title call does
    jsr 0x%(queue_music)X
    clr.b 26624(%%a6)
    clr.b 30927(%%a6)
    jsr 0x%(title_body)X                | title screen
    tst.b 26624(%%a6)
    beq.s 1f
    jmp 0x%(start_game)X                | Start pressed: play the game
1:  clr.b 26624(%%a6)
    clr.b 0x%(abort)X
    jsr 0x%(cinema)X                    | story cinema
    clr.b 0x%(in_cinema)X
    tst.b 0x%(abort)X
    beq.s 2f
    clr.b 0x%(abort)X                   | a button was pressed: back to the title
    clr.b 26624(%%a6)
    jsr 0x%(clear_text)X
    bra.s title
2:  move.b 26624(%%a6),%%d0
    beq.s 3f
    jmp 0x%(start_game)X
3:  moveq #0,%%d0
    rts
arcade:
    jsr 0x%(cinema)X
    move.b 26624(%%a6),%%d0
    beq.s 4f
    jmp 0x%(start_game)X
4:  moveq #0,%%d0
    rts
""" % names, why="AES cycle 1: title, then the story cinema, back to the title on a button (arcade: unchanged)")
    rom.write(CYCLE1, bytes.fromhex("4EF9") + cycle1.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("422E68004EB900015472"), why="start of the first attract cycle")

    skip = rom.place_code(r"""
    tst.b 0x%(system_mode)X
    beq.s 1f                            | AES: no title here
    jsr 0x%(title)X
1:  rts
""" % names, why="AES: skip the title at the end of the demo cycle (arcade: unchanged)")
    rom.write(TITLE_CALL, bytes.fromhex("4EF9") + skip.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("4EB9000108826600" "06C6"), why="end of the second attract cycle")

    check = rom.place_code(r"""
    tst.b 0x%(system_mode)X
    beq.s 1f
    jmp 0x%(push_start)X                | arcade: the original PUSH START routine
1:  move.b #0x%(magic)X,0x%(in_cinema)X | a story scene is running
    move.b 0x%(p1)X,%%d0
    or.b 0x%(p2)X,%%d0
    and.b #0xF0,%%d0                    | A B C D of either player
    beq.s 2f
    move.b #1,0x%(abort)X
2:  tst.b 0x%(abort)X
    beq.s 3f
    move.b #1,0x%(start_of_game)X       | makes the scene loop (and the cinema) end
3:  rts
""" % names, why="cinema scenes, once per frame: watch for a button instead of drawing PUSH START")
    for site in PUSH_START_CALLS:
        rom.write(site, bytes.fromhex("4EB9") + check.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB90001B034"), why="story scene loop: no PUSH START, check for a button")

    leave = rom.place_code(r"""
    clr.b 0x%(in_cinema)X               | any other screen is not the cinema
    jsr 0x%(push_start_first)X          | the two original instructions' worth
    jmp 0x%(push_start_rest)X
""" % names, why="the PUSH START routine (title, demo, ...) marks the cinema as over")
    rom.write(PUSH_START, bytes.fromhex("4EF9") + leave.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90005F050"), why="PUSH START routine entry")

    start = rom.place_code(r"""
    cmp.b #0x%(magic)X,0x%(in_cinema)X
    bne.s 1f
    and.b #0xFC,0x%(start_flags)X       | forget the Start request
    move.b #1,0x%(abort)X
    rts
1:  tst.b 0x10F000                      | the original first instruction
    jmp 0x%(player_start_rest)X
""" % names, why="BIOS PLAYER_START: in the cinema a Start press only ends the cinema")
    rom.write(PLAYER_START, bytes.fromhex("4EF9") + start.to_bytes(4, "big"),
              expect=bytes.fromhex("4A390010F000"), why="PLAYER_START entry")
