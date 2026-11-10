NAME = "title-menu"
DESCRIPTION = "Title menu (AES): Start opens (CONTINUE /) NEW GAME / OPTIONS on the title; OPTIONS = level select, sound test, auto-save switch, memory card manager"

# ---- The title menu (home console only; the arcade keeps its original flow)
# The title screen's loop (0x1AF6A) runs the sprites and, once per frame, the PUSH START routine (`tst.w
# 31600(a6) ; bne.s ; jsr 0x1B034` at 0x1AF94); it counts a timeout down in 0x1078F0 and ends when a game has
# been started (0x106800 non-zero). Start is noticed by the BIOS itself, which calls the game's PLAYER_START
# entry (0x9478: `lea 0x100000,a6 ; jsr 0x108DA ; rts`); 0x108DA starts the game (and aes-title-first wraps it
# for the story cinema).
#   * The PUSH START call is now `menu_frame`: it notes the title was on screen this frame and, while the menu is
#     closed, calls the PUSH START routine as before. While the menu is open it holds the title's timeout, draws
#     the menu where PUSH START was (the selected line blinks), and reads Up / Down / A.
#   * PLAYER_START's call of 0x108DA now goes through `start_pressed`: on the title (it was on screen this frame or
#     the last, or it is being set up - a flag from the start of its set-up, 0x1AE10, to its end, 0x1B026 - and no
#     game is running) the first Start opens the menu instead of starting a game (the Start request is dropped,
#     the player(s) who pressed it remembered); a Start while the menu is open selects, like A.
#   * Selecting an entry stores the choice, puts the remembered Start request back and calls 0x108DA itself, so
#     the game starts exactly as it did before (the title ends, the new game runs mode 3).
# In mode 3 (a new game, 0x112C0) the card load call (`jsr 0xEEF2` at 0x11322, which offered LOAD YES / NO) now
# goes through `new_game`: NEW GAME returns "nothing loaded" (a fresh game), OPTIONS first runs the options
# screen. The how-to-play cinema (`bsr 0x1111C` at 0x11332) plays for NEW GAME as in the original, but not when a
# stage was picked in the level select; the end of mode 3 (`move.b #0,0x3004(a6)` at 0x113B4) puts a picked
# stage into the stage bytes (0x103005 and each player's +0xF0) the way the developers' own stage select did.
#
# ---- The options screen: a black screen list (Up / Down, A or Start selects, B goes back)
#   LEVEL: <stage>  - Left / Right pick a stage (the short names, SHORT_NAMES), A starts it
#   SOUND TEST      - three lines, Up / Down between them: MUSIC: nn and SOUND FX: nn NAME (Left / Right step
#                     through the music and the kept sound effects in SFX_LABELS), A plays the line,
#                     B stops all; EXIT (A) stops everything and goes back. Commands go straight into the game's
#                     sound queue (0xA27A); Z80 driver ranges: 0x04-0x23 music, 0x24-0xEF sound effects, 0xFF
#                     stop all. (sound-test-names, a later patch, shows the latest names instead.)
#   DIFFICULTY: n   - LEVEL 1-8 (the game's soft-DIP 0x10FD8C: time limit, starting hearts), Left / Right; kept
#                     like AUTO SAVE
#   AUTO SAVE       - OFF / ON, A switches it (see the memory card notes below)
#   MEMORY CARD     - the card's state and every save on it; DELETE SAVE (the hack's), FORMAT CARD
#   BACK TO TITLE   - ends the "game" the way a finished one ends (mode 8: START_GAME's mode loop at 0x10D20
#                     cleans up and returns to the attract sequence), with the attract toggle set so the title
#                     comes next
# (For the beta, beta-no-card-options leaves AUTO SAVE and MEMORY CARD out of the list.)
# Both screens take either player's controls (0x10FD96 / 0x10FD9C and both Start bits of 0x10FDAC).
#
# ---- Memory card: CONTINUE, and an optional auto-save; the hack's save never touches the original game's
# The game saves 128 bytes (RAM 0x103100: a label, then the player's stage, flowers, items ... with a checksum at
# 0x10317F) to the card, identified by the game's id (0x0022) and a sub-number (0x10FDD0; the original uses 0,
# the hack 1 - one card entry). It offers to save at game over and in the continue countdowns (taking a quarter
# of the flowers); its LOAD prompt at the start of a game is replaced by CONTINUE.
#   * Every hack save is stamped (`stamp`): label BJ PLUS (save-name adds the stage), a marker (0x10317D), the AUTO SAVE setting
#     (0x10317E), the checksum redone. The original game's own saves go through 0xEE88, hooked just before it
#     writes the card.
#   * AUTO SAVE (options; off by default): off, the game's own SAVE YES/NO prompts, as in the original; on, no
#     prompts, and the stage start's title card call (0x13A6A, and 0x11486 on the other path) also saves - in a
#     real game on the home console with a card in, past the how-to-play - showing SAVING in the bottom right
#     corner (the flowers penalty left out). A save cut off by a power cut fails its checksum: no CONTINUE, and
#     the next stage start saves again.
#   * The setting is a RAM word (AUTO) kept through the attract cycle's clear of all game RAM (0x13430), and
#     comes from the card's save when the title menu opens; switching it rewrites that save's setting.
#   * CONTINUE heads the title menu when the card holds a valid hack save; it loads it and applies it the game's
#     way (0xF0D6, which rechecks the checksum), and mode 3 then skips its fresh-game set-up.
#   * Card errors (no card, not formatted, full) just mean no save.
STAGES = [
    (2, "JUNGLE ZONE 1"), (3, "JUNGLE ZONE 2"),
    (5, "THE LOWER EARTH EMPIRE 1"), (4, "THE LOWER EARTH EMPIRE 2"),
    (6, "THE LOWER EARTH EMPIRE 3"), (7, "THE LOWER EARTH EMPIRE 4"),
    (8, "EMPIRE MARSH 1"), (10, "EMPIRE MARSH 2"), (9, "EMPIRE MARSH 3"), (11, "EMPIRE MARSH 4"),
    (16, "MECHANICAL CITY 1"), (17, "MECHANICAL CITY 2"), (18, "MECHANICAL CITY 3"), (19, "MECHANICAL CITY 4"),
    (24, "STRANGE SPACE 1"), (25, "STRANGE SPACE 2"), (26, "STRANGE SPACE 3"), (27, "STRANGE SPACE 4"),
    (28, "DARUMA EMPIRE 1"), (29, "DARUMA EMPIRE 2"), (30, "DARUMA EMPIRE 3"), (31, "DARUMA EMPIRE 4"),
]
# Stage ids (the game's English title cards, table 0x13D9E): 0/1 are the how-to-play copies of the jungle,
# 12-15 and 20-23 are unused placeholders, 32 shop, 33-40 bosses, 41 route select.
CHOICE_NEW_GAME, CHOICE_OPTIONS, CHOICE_CONTINUE = 0, 1, 2
MENU = [("NEW GAME", CHOICE_NEW_GAME), ("OPTIONS", CHOICE_OPTIONS)]       # title menu, no save on the card
MENU_SAVE = [("CONTINUE", CHOICE_CONTINUE)] + MENU                        # ... with a save to continue
LEVEL_WIDTH = 15             # the LEVEL: line's name field (SHORT_NAMES padded to it)
OPTIONS = ["LEVEL: " + " " * LEVEL_WIDTH, "SOUND TEST", "DIFFICULTY: 4", "AUTO SAVE: OFF", "MEMORY CARD",
           "BACK TO TITLE"]
# The LEVEL: and DIFFICULTY: lines are set with Left / Right (no wrapping); A on LEVEL: starts that stage. Stage
# names use the approved short forms.
SHORT_NAMES = {"JUNGLE ZONE": "JUNGLE", "THE LOWER EARTH EMPIRE": "LOW EARTH EMP", "EMPIRE MARSH": "EMP MARSH",
               "MECHANICAL CITY": "MECH CITY", "STRANGE SPACE": "STRANGE SP", "DARUMA EMPIRE": "DARUMA EMP"}
OPT_DIFFICULTY, OPT_AUTO_SAVE = 2, 3         # their values are filled in when the screen is drawn
CARD_ACTIONS = ["DELETE SAVE", "FORMAT CARD", "BACK"]
CONFIRM = ["NO", "YES"]

TITLE_PUSH_START = 0x1AF94   # tst.w 31600(a6) ; bne.s +4 ; jsr 0x1B034(pc)
PUSH_START = 0x1B034
TITLE_BODY = 0x1AE10         # the title screen: move.b #32,12293(a6) ... (set-up, ~1 s, then its loop)
TITLE_END = 0x1B026          # the end of the title: jsr 0x9FBE ; jsr 0xA136 ; rts
PLAYER_START_CALL = 0x947E   # jsr 0x108DA (inside the BIOS's PLAYER_START entry)
PLAYER_START = 0x108DA
LOAD_CALL = 0x11322          # jsr 0xEEF2 (mode 3: offer to load from the card)
LOAD = 0xEEF2
HOW_TO_PLAY_CALL = 0x1132C   # move.b 26624(a6),30878(a6) ; bsr 0x1111C
HOW_TO_PLAY = 0x1111C
MODE3_END = 0x113B4          # move.b #0,0x3004(a6)  (mode 3 -> mode 0: start the stage)
CARD_SUB_SET = 0xEFD4        # move.b #0,0x10FDD0
HACK_CARD_SUB = 1
SAVE_BUF = 0x103100          # the game's 128-byte save
MAGIC = 0x5A                 # marks a hack auto-save (0x10317D)
CARD = 0x988A                # the game's call of the BIOS card routine (command 0x10FDC4, answer 0x10FDC6)
BUILD_SAVE = 0xEFDE          # fills SAVE_BUF from the player (30878(a6) bit 0: player 1, else 2) + checksum
APPLY_SAVE = 0xF0D6          # checks SAVE_BUF's checksum and gives it to the player(s) in 30878(a6); d0 0 = ok
STAGE_TITLE_CALLS = [0x13A6A, 0x11486]   # jsr 0x13C6E - the stage start's title card (a new stage: 0x1393A, and
                                         # the other path at 0x11486)
TITLE_CARD = 0x13C6E
SAVING_AT = (31, 28)         # fix column / row of SAVING (the bottom right corner)
SAVING_ATTR = 0x5000 + 0x500 # palette 5, the text font
# the game's own save prompts: skipped while auto-save is on (the countdown ones then answer d0 = 0, no save)
OLD_SAVES = [(0x1100C, 0xEE88, "save_over", "game over: SAVE YES/NO unless auto-save is on"),
             (0x123EE, 0xEBFE, "save_p1", "player 1 continue countdown: SAVE prompt unless auto-save is on"),
             (0x12A46, 0xED28, "save_p2", "player 2 continue countdown: SAVE prompt unless auto-save is on")]
GAME_SAVE_CARD = 0xEEB6      # jsr 0xF6B0, just before the game's own save (0xEE88) writes the card
GAME_SAVE_PREP = 0xF6B0
RAM_CLEAR = 0x13430          # the attract cycle's RAM clear: movea.l a6,a0 ; adda.l #0xF000,a0 ; then zeroes
                             # 0x100000-0x10EFFF downwards (movem loop from 0x13438)
RAM_CLEAR_REST = 0x13438
TITLE_TIMEOUT = 0x1078F0
SYSTEM_MODE = 0x10FD82       # BIOS: 0 = home console (AES)
START_FLAGS = 0x10FDB4       # BIOS: bit 0 / 1 = player 1 / 2 pressed Start
FRAME = 0x100207             # low byte of the game's frame counter
CLEAR_FIX = 0x9FBE           # fills the fix layer with the blank tile
CLEAR_SPRITES = 0xA1BC       # d0..d1 = first..last sprite to hide
WAIT_FRAME = 0xE856          # the game's wait-for-next-frame
QUEUE_SOUND = 0xA27A         # the game's sound command queue (d0 = command)
ATTRACT_TOGGLE = 0x1033CA   # bit 0: which attract cycle runs next (0x106A0: 0 = the one with the title)
FIRST_SOUND, LAST_SOUND, FIRST_EFFECT = 0x04, 0xEF, 0x24
# spare RAM: 0x10E700-0x10EFFF (see 030_pause_start.py)
CURSOR = 0x10E900            # the LEVEL: line's stage
SOUND_NO = 0x10E901          # the sound test's last number (its SOUND FX: line)
MUSIC_NO = 0x10E931          # its MUSIC: line's
# The SOUND FX: line steps through the kept sound effects (docs/sfx_labels.csv, a grid exported from the labels
# sheet: row = the code's high digit, column = its low digit; "E" = not used - blank or a synthesiser sample;
# "?" / "??" = unnamed): each shown as its code and name. SOUND_NO holds the line's place in that list.
SFX_LABELS = "docs/sfx_labels_title_menu.csv"   # (frozen: the names as of 2026-10-24, so this patch's size
                                                # doesn't follow the sheet - sound-test-names shows the live
                                                # docs/sfx_labels.csv's)


def short_name(name):
    head, num = name.rsplit(" ", 1)
    return (SHORT_NAMES[head] + " " + num).ljust(LEVEL_WIDTH)


def sfx_list():
    """[(code, label)] for the kept sounds, in code order (labels upper case, '?' for unnamed)."""
    import csv
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), SFX_LABELS)
    rows = list(csv.reader(open(path, encoding="utf-8")))
    cols = [int(c, 16) for c in rows[0][1:]]
    out = []
    for row in rows[1:]:
        hi = int(row[0], 16)
        for lo, cell in zip(cols, row[1:]):
            label = cell.strip().replace("\u2019", "'").upper()
            if label in ("", "E"):
                continue
            if set(label) <= {"?"}:
                label = "?"
            out.append((hi << 4 | lo, label))
    return sorted(out)
MENU_OPEN = 0x10E902
MENU_CURSOR = 0x10E903
MENU_PREV = 0x10E904         # (word) the menu's last frame's buttons
ON_TITLE = 0x10E906          # FRAME when the title was last on screen
START_BITS = 0x10E907        # which players pressed the Start that opened the menu
CHOICE = 0x10E908
STAGE_PICK = 0x10E909        # a stage picked on the LEVEL: line (0 = none)
COLOURS_DUE = 0x10E91F       # the framed look's colours to put in at the next frame (framed_setup / frame_wait)
SELECT_REQ = 0x10E90A        # Start pressed while the menu was open
OPT_CURSOR = 0x10E90B
TITLE_PHASE = 0x10E90C       # 1 from the start of the title screen's set-up until the title ends
PROBED = 0x10E90D            # the card has been looked at since the menu opened
BEST_SUB = 0x10E90E          # HACK_CARD_SUB if the card holds a valid hack save, 0 = none
AUTO = 0x10E910              # (word) AUTO_ON = auto-save on, anything else off (RAM is random at power-on); kept
AUTO_ON = 0xA55A             # through the attract cycle's RAM clear, and stored in the save (0x10317E = 1)
TO_MENU = 0x10E914           # (word) 0x5A00 + Start bits: open the title menu when the title is next up (kept
                             # through the attract cycle's RAM clear, like AUTO / DIFF)
FROM_ATTRACT = 0x10E90F      # Start bits of a Start pressed on an attract screen other than the title
DIFF = 0x10E912              # (word) DIFF_SET + the chosen difficulty 0-7 (LEVEL 1-8), else none chosen: the BIOS's
DIFF_SET = 0xD100            # soft-DIP (0x10FD8C, the game's default LEVEL 4); kept like AUTO, in the save 0x10317C
                             # (difficulty + 1; 0 = none)
DIFF_DIP_READ = 0x133A4      # move.b 0x10FD8C,d0 - the attract cycle's set-up copies the soft-DIPs into the game
DIFF_HEARTS = 0x134E0        # the difficulty (0x103063) -> starting hearts (0x103C02 / 0x103C03)
OPT_BUF = 0x10EB00           # the options screen's string table, with the settings filled in (128 bytes)
LINE_BUF = 0x10E980          # a line of text being put together (32 bytes)
SAVE_LABEL_NAME = "BJ PLUS "       # the start of the hack's save label (the original's: BLUE'S J.); save-name
                                  # (patches/997) writes the rest, the stage
PAL = 15                     # fix palette for the options screens' text
TITLE_PAL = 5                # the title's PUSH START palette
MENU_COL, MENU_LAST_ROW = 16, 21   # title menu: fix column, and the row of its last line (a line every other row;
                                  # was 22 - title-logo-up moved the ALPHA logo and PUSH START a row up)
PUSH_START_ADDR = 0x71D4     # where the title's PUSH START is (column 14, row 20: " PUSH START", 11 characters;
                             # row 21 in the original - title-logo-up)
TITLE_ROW, LIST_ROW, COL = 3, 6, 8
# The OPTIONS menu's framed look: the whole screen framed with the story cinema's text box (sprite tiles 0x56E8-0x56EB:
# corner, top edge, left edge, inside - the right column and bottom row mirrored; 20 x 14 tiles), its inside colour
# (15) the blue of the BLUE'S ITEMS description boxes; its text in that screen's 2-row font (0x4DBF4's table of tile
# words, fix palette 5 - loaded with that screen's shades - drawn a character at a time by 0x5F0EA, as 0x4DBB8
# does), the title centred at the top, the entries left aligned three rows apart. BIG_FONT makes list / print use it.
BIG_FONT = 0x10E930
BIG_TITLE = "OPTIONS"
BIG_TITLE_AT, BIG_LIST_AT, BIG_STEP = (None, 2), (5, 8), 3   # (column - the title is centred -, row)s; the font
                             # draws 2 rows below the row it's given (0x5F0EA adds 0x7002): the title is on rows 4-5
# The selected entry has an arrow left of it (the font's style: two new fix tiles), instead of blinking.
ARROW_ROWS = [0, 7, 6, 5, 4, 3, 2, 1, 1, 2, 3, 4, 5, 6, 7, 8]   # each pixel row's shade (as the font's letters)
SHADOW = 0xA                 # the letters' dark edge
FONT_SPACE = 0x680           # the font's space (its top tile; the bottom one 0x10 on)


def arrow_tiles():
    rows = []
    for r in range(16):
        d = abs(r - 8)
        row = [0] * 8
        if d <= 6 and r > 0:
            w = 7 - d
            for x in range(w):
                row[x] = ARROW_ROWS[r]
            if w < 8:
                row[w] = SHADOW
        rows.append(row)
    return rows[:8], rows[8:]


QUESTION = [".XXXXX.", "XXXXXXX", "XX...XX", "XX...XX", ".....XX", "....XX.", "...XX..", "..XX...", "..XX...",
            "..XX...", ".......", ".......", "..XX...", "..XX...", "..XX..."]   # pixel rows 1-15 (the font has none)


def question_tiles():
    """A question mark in the font's style: each row's shade, its dark edge right of each run."""
    rows = [[0] * 8]
    for r, line in enumerate(QUESTION, 1):
        row = [ARROW_ROWS[r] if c == "X" else 0 for c in line] + [0]
        for x in range(7):
            if line[x] == "X" and (x == 6 or line[x + 1] != "X"):
                row[x + 1] = SHADOW
        rows.append(row)
    return rows[:8], rows[8:]
FONT_TABLE, FONT_DRAW = 0x4DBF4, 0x5F0EA
FONT_PAL, FONT_COLOURS = 5, [0x8000, 0xFFFF, 0xFEEE, 0xFDDD, 0xFCCC, 0xFBBB, 0xFAAA, 0xF999, 0xF888, 0xF777, 0xF666,
                             0xF555, 0xF444, 0xF333, 0xF222, 0xF111]
FRAME_SPR, FRAME_PAL_NO = 1, 0x84
FRAME_TILES = (0x56E8, 0x56E9, 0x56EA, 0x56EB)
FRAME_COLOURS = [0x0000, 0x7FFF, 0x1029, 0x7FF8, 0xEFE3, 0x0FD1, 0x2C90, 0x2960, 0x52BF, 0x518F, 0x204C, 0xDB90,
                 0xA850, 0x0015, 0x5EC0, 0x0025]   # the story box's palette 0x84, inside (15) the items screens' blue


def frame_words():
    corner, top, left, inside = FRAME_TILES
    out = []
    for k in range(20):
        for r in range(14):
            edge_col = k in (0, 19)
            t = (corner if edge_col else top) if r in (0, 13) else (left if edge_col else inside)
            out += [t, FRAME_PAL_NO << 8 | (1 if k == 19 else 0) | (2 if r == 13 else 0)]
    return out
BLINK_ON, BLINK_OFF = 20, 10                 # frames the selected line is shown / hidden
REPEAT_DELAY, REPEAT_RATE = 20, 6            # holding a direction: first repeat after, then every, N frames


def fix_addr(col, row):
    return 0x7000 + col * 32 + row


def string_table(label, names):
    """A table of word offsets (label) followed by the zero-terminated strings (label_s)."""
    offs, data, off = [], "", 0
    for n in names:
        offs.append(off)
        data += "    .ascii \"%s\"\n    .byte 0\n" % n
        off += len(n) + 1
    return ("%s:\n%s%s_s:\n%s    .even\n" % (label, "".join("    .word %d\n" % o for o in offs), label, data))


PUSH_START_END = 0x1B096      # its rts at 0x1B094


def push_start_copy(rom):
    """The title's own copy of the PUSH START routine (0x1B034, shared with the other attract screens), its three
    records' fix address PUSH_START_ADDR (title-logo-up moved the title's a row up; elsewhere - TODAY'S BEST's 4th
    line is on row 20 - it stays on row 21)."""
    body = bytearray(rom.data[PUSH_START:PUSH_START_END])
    for at in (0x1B04C, 0x1B064, 0x1B084):
        if body[at - PUSH_START:at - PUSH_START + 2] != b"\x71\xd5":
            raise SystemExit("title-menu: the PUSH START routine isn't as expected")
        body[at - PUSH_START:at - PUSH_START + 2] = PUSH_START_ADDR.to_bytes(2, "big")
    addr = rom.alloc(len(body))
    rom.data[addr:addr + len(body)] = body
    return addr


def apply(rom):
    # the big font's colon: its full stop's lower tile (the dot at its foot) twice, one above the other
    stop = rom.u16(FONT_TABLE + (ord(".") - 0x20) * 2)
    colon = rom.add_fix_tile(rom.fix_tile(((stop >> 8) & 0xF) << 8 | ((stop + 0x10) & 0xFF)),
                             why="options font: a colon's dot")
    arrow = [rom.add_fix_tile(t, why="options font: the selection arrow") for t in arrow_tiles()]
    question = [rom.add_fix_tile(t, why="options font: a question mark") for t in question_tiles()]
    sfx = sfx_list()
    sfx_width = max(len(label) for code, label in sfx)
    for code, label in sfx:
        bad = [c for c in label if not ("A" <= c <= "Z" or "0" <= c <= "9" or c in " !'(),-.?/")]
        if bad:
            raise SystemExit("title-menu: %s's label %r has characters the font lacks: %r" % (hex(code), label, bad))
    n = len(OPTIONS)
    strings = "".join(o + "\0" for o in OPTIONS)
    opt_len = 2 * n + len(strings) + (len(strings) & 1)
    assert opt_len <= 128
    opt_digit = 2 * n + strings.index("DIFFICULTY: 4") + 12
    opt_level = 2 * n + strings.index("LEVEL: ") + 7
    opt_onoff = 2 * n + strings.index("OFF")
    width = max(len(m) for m, c in MENU_SAVE)
    src = r"""
    bra.w menu_frame                 | +0
    bra.w start_pressed              | +4
    bra.w new_game                   | +8
    bra.w how_to_play                | +12
    bra.w mode3_end                  | +16
    bra.w title_enter                | +20
    bra.w title_leave                | +24
    bra.w autosave                   | +28
    bra.w save_over                  | +32
    bra.w save_p1                    | +36
    bra.w save_p2                    | +40
    bra.w game_save_prep             | +44
    bra.w ram_keep                   | +48
    bra.w diff_dip                   | +52

| ================= auto-save off (the default): the game's own save prompts, as in the original
save_over:
    cmp.w #AUTO_ON,AUTO_WORD
    beq 1f
    jmp 0xEE88
1:  rts
save_p1:
    cmp.w #AUTO_ON,AUTO_WORD
    beq 1f
    jmp 0xEBFE
1:  moveq #0,%d0
    rts
save_p2:
    cmp.w #AUTO_ON,AUTO_WORD
    beq 1f
    jmp 0xED28
1:  moveq #0,%d0
    rts
| the game's own save (0xEE88), just before it writes the card: the hack's label, marker and setting
game_save_prep:
    jsr GAME_SAVE_PREP
    bra stamp

| the attract cycle's RAM clear (all of 0x100000-0x10EFFF), keeping the auto-save setting
ram_keep:
    move.l AUTO_WORD,-(%sp)          | and DIFF_WORD, the word after it
    move.w TO_MENU_WORD,-(%sp)
    move.l %a6,%a0
    add.l #0xF000,%a0
    jsr RAM_CLEAR_REST
    move.w (%sp)+,TO_MENU_WORD
    move.l (%sp)+,AUTO_WORD
    rts

| the attract cycle's set-up, in place of its read of the difficulty soft-DIP: the chosen difficulty if any
diff_dip:
    bra diff_level

| d0.l = the difficulty, 0-7: the one chosen in the options, else the BIOS's soft-DIP
diff_level:
    moveq #0,%d0
    tst.b SYSTEM_MODE                | the arcade: always the soft-DIP
    bne 1f
    move.w DIFF_WORD,%d0
    and.w #0xFFF8,%d0
    cmp.w #DIFF_SET,%d0
    bne 1f
    move.w DIFF_WORD,%d0
    and.l #7,%d0
    rts
1:  move.b 0x10FD8C,%d0
    and.l #7,%d0
    rts

| d0 = a difficulty 0-7: chosen, and the game given it now (0x103063, and the starting hearts that follow from it)
diff_set:
    movem.l %d0-%d2/%a0-%a1/%a6,-(%sp)
    and.w #7,%d0
    move.b %d0,0x103063
    or.w #DIFF_SET,%d0
    move.w %d0,DIFF_WORD
    lea 0x100000,%a6
    jsr DIFF_HEARTS
    movem.l (%sp)+,%d0-%d2/%a0-%a1/%a6
    rts

| ================= title: once per frame, in place of the PUSH START call
menu_frame:
    move.b FRAME,ON_TITLE
    move.w %d0,-(%sp)                | Start was pressed on another attract screen: open the menu now
    move.w TO_MENU_WORD,%d0
    and.w #0xFF00,%d0
    cmp.w #0x5A00,%d0
    bne 0f
    tst.b MENU_OPEN
    bne 0f
    move.b #1,MENU_OPEN
    clr.b PROBED
    clr.b BEST_SUB
    clr.b MENU_CURSOR
    clr.b SELECT_REQ
    move.w #0xFFFF,MENU_PREV
    move.b TO_MENU_WORD+1,START_BITS
    clr.w TO_MENU_WORD
0:  move.w (%sp)+,%d0
    tst.b MENU_OPEN
    bne 1f
    tst.w 31600(%a6)
    bne 0f
    jsr PUSH_START
0:  rts
1:  movem.l %d0-%d7/%a0-%a1,-(%sp)
    addq.l #1,TITLE_TIMEOUT          | hold the title's timeout
    lea push_blank(%pc),%a0          | PUSH START, still on screen from before the menu opened
    move.w #PUSH_START_ADDR,%d1
    moveq #0,%d2
    move.w #TITLE_ATTR,%d7
    bsr print_attr
    tst.b PROBED                     | the first frame: is there a save to continue?
    bne 10f
    move.b #1,PROBED
    lea push_blank(%pc),%a0          | (and the game's own PUSH START a row lower, where it draws it - left on
    move.w #PUSH_START_ADDR+1,%d1    | screen by some ways to the title: its P and T showed round OPTIONS)
    moveq #0,%d2
    move.w #TITLE_ATTR,%d7
    bsr print_attr
    bsr probe
10: bsr menu_entries                 | a1 = the entries' strings, d5 = how many, d4 = the first line's address
    moveq #0,%d0
    move.b 0x10FD96,%d0
    or.b 0x10FD9C,%d0
    move.w MENU_PREV,%d1
    not.w %d1
    and.w %d0,%d1                    | d1 = newly pressed
    move.w %d0,MENU_PREV
    moveq #0,%d6
    move.b MENU_CURSOR,%d6
    btst #0,%d1
    beq 2f
    subq.w #1,%d6
    bpl 2f
    move.w %d5,%d6
    subq.w #1,%d6
2:  btst #1,%d1
    beq 3f
    addq.w #1,%d6
    cmp.w %d5,%d6
    bcs 3f
    moveq #0,%d6
3:  move.b %d6,MENU_CURSOR
    btst #4,%d1                      | A
    bne select
    tst.b SELECT_REQ                 | or Start
    bne select
    | draw the entries; the selected one blinks (frame counter bit 4)
    moveq #0,%d3
4:  move.w %d3,%d0
    add.w %d0,%d0
    move.w (%a1,%d0.w),%d0
    move.w %d5,%d2                   | the strings follow the offsets
    add.w %d2,%d2
    lea (%a1,%d2.w),%a0
    add.w %d0,%a0
    move.w %d3,%d1
    add.w %d1,%d1
    add.w %d4,%d1
    moveq #0,%d2
    cmp.b %d6,%d3
    bne 5f
    btst #4,FRAME
    beq 5f
    moveq #1,%d2
5:  move.w #TITLE_ATTR,%d7
    bsr print_attr
    addq.w #1,%d3
    cmp.w %d5,%d3
    bne 4b
    movem.l (%sp)+,%d0-%d7/%a0-%a1
    rts
select:
    lea menu_ids(%pc),%a0            | the entry -> the choice
    tst.b BEST_SUB
    beq 7f
    lea menu_save_ids(%pc),%a0
7:  move.b (%a0,%d6.w),CHOICE
    clr.b MENU_OPEN
    clr.b SELECT_REQ
    moveq #0,%d3                     | clear the menu lines
6:  lea blank(%pc),%a0
    move.w %d3,%d1
    add.w %d1,%d1
    add.w %d4,%d1
    moveq #0,%d2
    move.w #TITLE_ATTR,%d7
    bsr print_attr
    addq.w #1,%d3
    cmp.w %d5,%d3
    bne 6b
    move.b START_BITS,%d0            | put the Start request back and start the game the usual way
    or.b %d0,START_FLAGS
    movem.l (%sp)+,%d0-%d7/%a0-%a1
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    lea 0x100000,%a6
    jsr PLAYER_START
    movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

| the menu's entries: a1 = the string table, d5 = how many, d4 = the fix address of the first line
menu_entries:
    lea menu_t(%pc),%a1
    moveq #MENU_COUNT,%d5
    tst.b BEST_SUB
    beq 1f
    lea menu_save_t(%pc),%a1
    moveq #MENU_SAVE_COUNT,%d5
1:  move.w %d5,%d4
    subq.w #1,%d4
    add.w %d4,%d4
    neg.w %d4
    add.w #MENU_LAST_ADDR,%d4
    rts

| ================= the title screen's set-up and end: the title phase
title_enter:
    clr.b FROM_ATTRACT_BYTE
    move.b #1,TITLE_PHASE
    move.b #32,0x103005              | the instruction this call replaced
    rts
title_leave:
    clr.b TITLE_PHASE
    jmp CLEAR_FIX                    | the call this replaced

| ================= BIOS PLAYER_START, in place of its jsr 0x108DA
start_pressed:
    tst.b SYSTEM_MODE
    bne 9f
    cmp.b #2,0x10FDAF                | a game is running (BIOS USER_MODE 2; player 2 joining): as before (the attract
    beq 9f                           | demo has players in 0x106800 too, but USER_MODE 1)
    tst.b TITLE_PHASE                | the title is being set up (or is up): the menu
    bne 7f
    move.b FRAME,%d0
    sub.b ON_TITLE,%d0
    cmp.b #2,%d0
    bcc 10f                          | not on the title (the demo, high scores ...): see new_game
7:
    tst.b MENU_OPEN
    bne 8f
    move.b #1,MENU_OPEN              | open the menu
    clr.b PROBED
    clr.b BEST_SUB
    clr.b MENU_CURSOR
    clr.b SELECT_REQ
    move.w #0xFFFF,MENU_PREV         | buttons already held don't count
    move.b START_FLAGS,%d0
    and.b #3,%d0
    move.b %d0,START_BITS
    and.b #0xFC,START_FLAGS          | forget the Start request for now
    rts
8:  move.b #1,SELECT_REQ
    and.b #0xFC,START_FLAGS
    rts
9:  jmp PLAYER_START
10: move.b START_FLAGS,%d0           | the game starts as before, but mode 3 (new_game) sends it back to the
    and.b #3,%d0                     | title with the menu open
    move.b %d0,FROM_ATTRACT_BYTE
    jmp PLAYER_START

| ================= mode 3 (new game), in place of the card load call
new_game:
    tst.b SYSTEM_MODE
    beq 1f
    jmp LOAD                         | arcade: as before
1:  tst.b FROM_ATTRACT_BYTE          | started from an attract screen: back to the title, the menu open there
    beq 11f
    moveq #0,%d0
    move.b FROM_ATTRACT_BYTE,%d0
    or.w #0x5A00,%d0
    move.w %d0,TO_MENU_WORD
    clr.b FROM_ATTRACT_BYTE
    bclr #0,ATTRACT_TOGGLE           | as BACK TO TITLE
    move.b #8,0x103004
    addq.l #4,%sp
    rts
11: clr.b STAGE_PICK
    move.b CHOICE,%d0
    clr.b CHOICE
    cmp.b #CHOICE_CONTINUE,%d0
    bne 3f
    bsr continue                     | d0 = 0 if a save was loaded (then mode 3 skips its fresh-game set-up)
    beq 4f
    bra 2f
3:  cmp.b #CHOICE_OPTIONS,%d0
    bne 2f
    movem.l %d1-%d7/%a0-%a5,-(%sp)
    bsr options
    movem.l (%sp)+,%d1-%d7/%a0-%a5
    tst.w %d0
    beq 2f
    bclr #0,ATTRACT_TOGGLE           | BACK TO TITLE: the next attract cycle is the title one
    move.b #8,0x103004               | mode 8 ends the game (START_GAME's mode loop cleans up and returns)
    addq.l #4,%sp                    | and leave mode 3 now, straight back to that loop
    rts
2:  moveq #-1,%d0                    | nothing loaded: a fresh game
4:  rts

| ================= the memory card: the hack's save is the game's 128-byte save (0x103100: a label, the player's
| stage, flowers, items ... and a checksum at 0x10317F over 0x103114-0x10317E) in slot (sub-number) 1; unused
| bytes of it hold a marker (0x10317D) and the AUTO SAVE setting (0x10317E).
| d0 = command (2 load, 3 save), d1 = slot -> d0 = the BIOS's answer (0 = done), Z set if done
card_io:
    movem.l %d1-%d7/%a0-%a6,-(%sp)
    move.l #SAVE_BUF,0x10FDC8
    move.w #0x80,0x10FDCC
    move.w 0x108,0x10FDCE            | the game's id
    move.b %d1,0x10FDD0
    move.b %d0,0x10FDC4
    lea 0x100000,%a6
    jsr BIOS_CARD_CALL
    moveq #0,%d0
    move.b 0x10FDC6,%d0
    movem.l (%sp)+,%d1-%d7/%a0-%a6
    tst.b %d0
    rts

| Z set if the buffer holds a hack save: its marker, and a matching checksum
buf_valid:
    movem.l %d0-%d1/%a0,-(%sp)
    cmp.b #MAGIC,0x10317D
    bne 9f
    bsr checksum
    cmp.b 0x10317F,%d1
9:  movem.l (%sp)+,%d0-%d1/%a0
    rts

| d1 = the save's checksum (the byte sum of 0x103114-0x10317E)
checksum:
    move.l %a0,-(%sp)
    move.w %d0,-(%sp)
    lea 0x103114,%a0
    move.w #106,%d0
    moveq #0,%d1
1:  add.b (%a0)+,%d1
    dbf %d0,1b
    move.w (%sp)+,%d0
    move.l (%sp)+,%a0
    rts

| a built save becomes the hack's: the label (what card screens show) BJ PLUS (save-name: and the stage), the marker, the
| auto-save setting (0x10317E), and the checksum again
stamp:
    movem.l %d0-%d1/%a0-%a1,-(%sp)
    lea save_label(%pc),%a0
    lea SAVE_BUF,%a1
    moveq #LABEL_NAME-1,%d0
5:  move.b (%a0)+,(%a1)+
    dbf %d0,5b
    move.b #MAGIC,0x10317D
    bsr stamp_setting
    movem.l (%sp)+,%d0-%d1/%a0-%a1
    rts
stamp_setting:
    clr.b 0x10317E
    cmp.w #AUTO_ON,AUTO_WORD
    bne 1f
    move.b #1,0x10317E
1:  move.l %d0,-(%sp)                | the difficulty + 1
    bsr diff_level
    addq.b #1,%d0
    move.b %d0,0x10317C
    move.l (%sp)+,%d0
    bsr checksum
    move.b %d1,0x10317F
    rts

| the AUTO SAVE option changed: the save on the card (if any) takes the new setting
store_setting:
    movem.l %d0-%d1,-(%sp)
    move.b 0x380000,%d0
    and.b #0x30,%d0
    bne 9f
    moveq #2,%d0
    moveq #HACK_SLOT,%d1
    bsr card_io
    bne 9f
    bsr buf_valid
    bne 9f
    bsr stamp_setting
    moveq #3,%d0
    moveq #HACK_SLOT,%d1
    bsr card_io
9:  movem.l (%sp)+,%d0-%d1
    rts

| BEST_SUB = HACK_SLOT if the card holds a valid hack save, else 0
probe:
    movem.l %d0-%d1,-(%sp)
    clr.b BEST_SUB
    move.b 0x380000,%d0              | no card: nothing
    and.b #0x30,%d0
    bne 9f
    moveq #2,%d0
    moveq #HACK_SLOT,%d1
    bsr card_io
    bne 9f
    bsr buf_valid
    bne 9f
    move.b #HACK_SLOT,BEST_SUB
    clr.w AUTO_WORD                  | the save's settings: auto-save
    tst.b 0x10317E
    beq 8f
    move.w #AUTO_ON,AUTO_WORD
8:  moveq #0,%d0                     | and the difficulty, if it has one
    move.b 0x10317C,%d0
    subq.b #1,%d0
    cmp.b #8,%d0
    bcc 9f
    bsr diff_set
9:  movem.l (%sp)+,%d0-%d1
    rts

| CONTINUE (in mode 3): load the save and apply it the game's way (0xF0D6); d0 = 0 / Z set if loaded
continue:
    moveq #2,%d0
    moveq #HACK_SLOT,%d1
    move.b 0x380000,%d2
    and.b #0x30,%d2
    bne 8f
    bsr card_io
    bne 8f
    bsr buf_valid
    bne 8f
    jsr APPLY_SAVE
    tst.w %d0
    rts
8:  moveq #-1,%d0
    rts

| ================= the stage start, in place of its jsr to the title card: the title card, then an auto-save
| (a real game on the home console, past the how-to-play, with a card in) and SAVING in the corner meanwhile
autosave:
    jsr TITLE_CARD
    cmp.w #AUTO_ON,AUTO_WORD
    bne 9f
    tst.b SYSTEM_MODE
    bne 9f
    tst.b 0x106800                   | the attract demo: no
    beq 9f
    cmp.b #2,0x103005                | the how-to-play's stages 0 / 1: no
    bcs 9f
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    move.b 0x380000,%d0
    and.b #0x30,%d0
    bne 8f
    lea saving(%pc),%a0
    move.w #SAVING_ADDR,%d1
    moveq #0,%d2
    move.w #SAVING_ATTR,%d7
    bsr print_attr
    lea 0x100000,%a6                 | the game's save builder (0xEFDE) - minus the quarter of the flowers it
    lea 0x107000,%a4                 | takes away (a game-over penalty): put them back
    btst #0,30878(%a6)
    bne 3f
    lea 0x107400,%a4
3:  move.b 16(%a4),%d6
    jsr BUILD_SAVE
    move.b %d6,16(%a4)
    move.b %d6,0x103115
    bsr stamp
    moveq #3,%d0
    moveq #HACK_SLOT,%d1
    bsr card_io
8:  movem.l (%sp)+,%d0-%d7/%a0-%a6
9:  rts

| in place of `move.b 26624(a6),30878(a6) ; bsr 0x1111C`: the how-to-play, unless a stage was picked
how_to_play:
    move.b 26624(%a6),30878(%a6)
    tst.b STAGE_PICK
    bne 1f
    jsr HOW_TO_PLAY
1:  rts

| in place of `move.b #0,0x3004(a6)` at the end of mode 3: a picked stage
mode3_end:
    move.b STAGE_PICK,%d0
    beq 1f
    move.b %d0,0x103005
    move.b %d0,0x1070F0
    move.b %d0,0x1074F0
    clr.b STAGE_PICK
1:  move.b #0,0x103004
    rts

| ================= the options screen: returns d0 = 0 to start the game (a stage picked), 1 = back to the title
options:
    bsr framed_setup
options_list:
    lea opt_title(%pc),%a0
    bsr opt_build
    moveq #0,%d6
    move.b OPT_CURSOR,%d6
    moveq #OPT_COUNT,%d7
    st BIG_FLAG
    bsr list
    move.b %d6,OPT_CURSOR
    cmp.w #2,%d0
    bcs 20f
    bsr opt_left_right               | Left / Right: a setting changed, the list again
    bra options_list
20: tst.w %d6
    bne 21f
    tst.w %d0
    bne options_list                 | B: stay here
    lea stage_ids(%pc),%a0           | LEVEL: start the chosen stage
    moveq #0,%d0
    move.b CURSOR,%d0
    move.b (%a0,%d0.w),STAGE_PICK
    clr.b BIG_FLAG
    bsr frame_hide
    jsr CLEAR_FIX
    moveq #0,%d0
    rts
21: cmp.w #OPT_DIFFICULTY,%d6
    beq options_list                 | DIFFICULTY: set with Left / Right
    clr.b BIG_FLAG
    bsr frame_hide
    tst.w %d0
    bne options                      | B: stay here
    cmp.w #1,%d6
    bne 2f
    bsr sound_test                   | SOUND TEST
    bra options
2:  cmp.w #OPT_AUTO_SAVE,%d6
    bne 5f
    cmp.w #AUTO_ON,AUTO_WORD         | AUTO SAVE: switch it
    seq %d0
    move.w #AUTO_ON,AUTO_WORD
    tst.b %d0
    beq 4f
    clr.w AUTO_WORD
4:  bsr store_setting
    bra options
5:  cmp.w #OPT_MEMORY_CARD,%d6
    bne 3f
    bsr card_screen                  | MEMORY CARD
    bra options
3:  moveq #1,%d0                     | BACK TO TITLE
    rts

| Left (d0 = 2) / Right (3) on line d6: LEVEL: the stage, DIFFICULTY: the level - a step, no wrapping
opt_left_right:
    move.w %d0,%d1
    tst.w %d6
    bne 2f
    moveq #0,%d0
    move.b CURSOR,%d0
    cmp.w #2,%d1
    bne 1f
    tst.w %d0
    beq 9f
    subq.b #1,CURSOR
    rts
1:  cmp.w #STAGE_COUNT-1,%d0
    bcc 9f
    addq.b #1,CURSOR
    rts
2:  cmp.w #OPT_DIFFICULTY,%d6
    bne 9f
    move.w %d1,-(%sp)
    bsr diff_level
    move.w (%sp)+,%d1
    cmp.w #2,%d1
    bne 3f
    tst.w %d0
    beq 9f
    subq.w #1,%d0
    bra 4f
3:  cmp.w #7,%d0
    bcc 9f
    addq.w #1,%d0
4:  bsr diff_set
    bsr store_setting
9:  rts

short_names:
    .byte SHORT_STAGE_NAMES
    .even

| a1 = the options' string table, copied to RAM with the settings filled in (the difficulty's digit, ON / OFF)
opt_build:
    move.l %a0,-(%sp)
    lea opt_t(%pc),%a0
    lea OPT_BUF,%a1
    move.w #OPT_T_LEN-1,%d0
1:  move.b (%a0)+,(%a1)+
    dbf %d0,1b
    lea OPT_BUF,%a1
    moveq #0,%d0                     | LEVEL: the chosen stage's name
    move.b CURSOR,%d0
    cmp.w #STAGE_COUNT,%d0           | RAM is random at power-on: the first stage
    bcs 4f
    moveq #0,%d0
    move.b %d0,CURSOR
4:  mulu #LEVEL_WIDTH,%d0
    lea short_names(%pc),%a0
    add.w %d0,%a0
    moveq #LEVEL_WIDTH-1,%d0
3:  move.b (%a0)+,OPT_LEVEL_AT(%a1)
    addq.l #1,%a1
    dbf %d0,3b
    lea OPT_BUF,%a1
    bsr diff_level
    add.b #0x31,%d0
    move.b %d0,OPT_DIGIT(%a1)
    cmp.w #AUTO_ON,AUTO_WORD
    bne 2f
    move.b #0x4F,OPT_ONOFF(%a1)      | ON
    move.b #0x4E,OPT_ONOFF+1(%a1)
    move.b #0x20,OPT_ONOFF+2(%a1)
2:  move.l (%sp)+,%a0
    rts

| ================= the memory card screen: the actions (DELETE SAVE - the hack's -, FORMAT CARD, BACK), the card's
| state and every save on it. The card is read directly (as the BIOS does: 0x3A0019 / 0x380011 cleared, then card
| byte n = the low byte of the word at 0x800000 + 2n; word reads only - MAME answers byte reads with 0xFF): the
| "formatted" signature at 0x20, the directory at 0x40 (32 entries: slot or 0xFF = free, the game's id, first
| 64-byte block), the block chain at 0xC0 (0 = free block); a save's first bytes are its label. Deleting and formatting are the BIOS's card commands 4 and 0.
card_screen:
    bsr screen_setup
    moveq #0,%d4                     | d4 = 0 no card, 1 not formatted, 2 formatted
    move.b 0x380000,%d0
    and.b #0x30,%d0
    bne 1f
    move.b #0,0x3A0019
    move.b #0,0x380011
    lea 0x800000,%a3                 | card byte n = low byte of the word at 0x800000 + 2n
    lea card_sig(%pc),%a0            | word reads only: MAME answers byte reads with 0xFF
    lea 0x40(%a3),%a2
    moveq #CARD_SIG_LEN-1,%d1
    moveq #1,%d4
2:  move.w (%a2)+,%d0
    cmp.b (%a0)+,%d0
    bne 1f
    dbf %d1,2b
    moveq #2,%d4
1:  lea st_nocard(%pc),%a0
    cmp.w #1,%d4
    bcs 3f
    lea st_unformatted(%pc),%a0
    beq 3f
    lea st_free(%pc),%a0
3:  move.w #CARD_STATUS_ADDR,%d1
    bsr print
    cmp.w #2,%d4
    bne 20f
    moveq #0,%d5                     | free blocks: the block chain's zeros (blocks 5-31)
    lea 0x180+5*2(%a3),%a2
    moveq #26,%d1
4:  move.w (%a2)+,%d0
    tst.b %d0
    bne 5f
    addq.w #1,%d5
5:
    dbf %d1,4b
    move.w %d5,%d0
    move.w #CARD_FREE_ADDR,%d1
    bsr print_dec2
    move.w #CARD_LIST_ADDR,%d3       | the saves, one line each
    moveq #0,%d2                     | d2 = directory entry
6:  cmp.w #CARD_LIST_END,%d3       | room for 14 lines
    beq 20f
    move.w %d2,%d0
    lsl.w #3,%d0
    lea 0x80(%a3),%a2                | entry at card 0x40 + 4 * n
    add.w %d0,%a2
    move.w (%a2),%d0
    cmp.b #0xFF,%d0
    beq 9f
    lea LINE_BUF,%a1                 | the label (20 characters, anything unprintable as a space)
    moveq #0,%d0
    move.w 6(%a2),%d0                | first block
    and.w #0xFF,%d0
    mulu #128,%d0
    lea (%a3,%d0.l),%a0
    moveq #LABEL_LEN-1,%d1
7:  move.w (%a0)+,%d0
    cmp.b #0x20,%d0
    bcs 8f
    cmp.b #0x5F,%d0
    bls 10f
8:  moveq #0x20,%d0
10: move.b %d0,(%a1)+
    dbf %d1,7b
    move.b #0x20,(%a1)+              | then the game's id and slot, e.g. 0022-1
    move.w 2(%a2),%d0
    bsr hex_to_buf
    move.w 4(%a2),%d0
    bsr hex_to_buf
    move.b #0x2D,(%a1)+
    move.w (%a2),%d0
    and.b #15,%d0
    add.b #0x30,%d0
    move.b %d0,(%a1)+
    clr.b (%a1)
    lea LINE_BUF,%a0
    move.w %d3,%d1
    movem.l %d2-%d4/%a3,-(%sp)
    bsr print
    movem.l (%sp)+,%d2-%d4/%a3
    addq.w #1,%d3
9:  addq.w #1,%d2
    cmp.w #32,%d2
    bne 6b
20: move.w %d4,-(%sp)                | kept over the list
    lea card_title(%pc),%a0
    lea card_t(%pc),%a1
    moveq #0,%d6
    moveq #CARD_ACTION_COUNT,%d7
    bsr list
    move.w (%sp)+,%d4
    tst.w %d0
    bne 29f                          | B: back
    cmp.w #2,%d6
    beq 29f                          | BACK
    cmp.w #1,%d6
    beq 25f
    cmp.w #2,%d4                     | DELETE SAVE
    bne card_screen
    lea confirm_delete(%pc),%a0
    bsr confirm
    beq card_screen
    moveq #4,%d0
    moveq #HACK_SLOT,%d1
    bsr card_io
    bra card_screen
25: tst.w %d4                        | FORMAT CARD
    beq card_screen
    lea confirm_format(%pc),%a0
    bsr confirm
    beq card_screen
    moveq #0,%d0
    moveq #0,%d1
    bsr card_io
    bra card_screen
29: rts

| a0 = the question: NO / YES (NO first); Z clear if YES
confirm:
    move.l %a0,-(%sp)
    bsr screen_setup
    move.l (%sp)+,%a0
    lea confirm_t(%pc),%a1
    moveq #0,%d6
    moveq #2,%d7
    bsr list
    tst.w %d0
    bne 1f
    tst.w %d6
    rts
1:  moveq #0,%d0
    rts

| d0 = byte -> two hex digits at (a1)+
hex_to_buf:
    move.w %d0,-(%sp)
    lsr.b #4,%d0
    bsr 1f
    move.w (%sp)+,%d0
1:  and.b #15,%d0
    add.b #0x30,%d0
    cmp.b #0x3A,%d0
    bcs 2f
    addq.b #7,%d0
2:  move.b %d0,(%a1)+
    rts

| d0 = 0-99, d1 = fix address: two decimal digits
print_dec2:
    and.l #0xFF,%d0
    divu #10,%d0
    lea LINE_BUF,%a0
    add.b #0x30,%d0
    move.b %d0,(%a0)
    swap %d0
    add.b #0x30,%d0
    move.b %d0,1(%a0)
    clr.b 2(%a0)
    bra print

| black screen, white text in palette PAL - its colours from a vblank, after the clearing (which takes most of a
| frame): the screen changes in one frame, not torn partway down
screen_setup:
    jsr CLEAR_FIX
    moveq #0,%d0
    move.w #379,%d1
    jsr CLEAR_SPRITES
    jsr 0xE856
    lea 0x400000+PAL*32,%a0
    move.w #0x0000,(%a0)+
    moveq #3,%d0
1:  move.w #0x7FFF,(%a0)+
    dbf %d0,1b
    moveq #4,%d0
2:  move.w #0x0000,(%a0)+
    dbf %d0,2b
    move.w #0x8000,(%a0)+
    move.w #0x8000,0x401FFE          | backdrop: black
    rts

| a list screen: a0 = title, a1 = string table, d7 = count, d6 = first cursor
| returns d6 = the entry chosen, d0 = 0 (A / Start) or 1 (B)
list:
    move.w %d7,-(%sp)
    move.l %a1,-(%sp)
    move.w #TITLE_ADDR,%d1
    tst.b BIG_FLAG
    beq 0f
    move.w #BIG_TITLE_POS,%d1
0:  bsr print
    moveq #0,%d7                     | blink counter
    move.w #0xFFFF,%d5
    moveq #0,%d4
l_loop:
    move.l (%sp),%a1
    moveq #0,%d3
l_line:
    move.w %d3,%d0
    add.w %d0,%d0
    move.w (%a1,%d0.w),%d0
    move.w 4(%sp),%d2                | the strings follow the offsets
    add.w %d2,%d2
    lea (%a1,%d2.w),%a0
    add.w %d0,%a0
    move.w %d3,%d1
    add.w #LIST_ADDR,%d1
    tst.b BIG_FLAG
    beq 0f
    move.w %d3,%d1                   | (the big font: BIG_STEP rows a line; the last line - BACK TO TITLE - a row
    mulu #BIG_STEP_ROWS,%d1          | lower, set apart)
    add.w #BIG_LIST_POS,%d1
    move.w 4(%sp),%d0
    subq.w #1,%d0
    cmp.w %d0,%d3
    bne 0f
    addq.w #1,%d1
0:  moveq #0,%d2
    cmp.w %d6,%d3
    bne 1f
    cmp.w #BLINK_ON,%d7
    bcs 1f
    moveq #1,%d2
1:  tst.b BIG_FLAG                   | the big font: no blinking - an arrow at the selected entry
    beq 16f
    moveq #0,%d2
16: bsr print_or_blank
    tst.b BIG_FLAG
    beq 17f
    bsr big_arrow
17:
    addq.w #1,%d3
    cmp.w 4(%sp),%d3
    bne l_line
    bsr frame_wait
    addq.w #1,%d7
    cmp.w #BLINK_ON+BLINK_OFF,%d7
    bcs 2f
    moveq #0,%d7
2:  bsr buttons
    move.w %d1,%d2
    and.w #0x110,%d2                 | A or Start
    beq 3f
    moveq #0,%d0
    bra 9f
3:  btst #5,%d1                      | B
    beq 4f
    moveq #1,%d0
    bra 9f
4:  tst.b BIG_FLAG                   | OPTIONS: Left / Right return 2 / 3
    beq 41f
    moveq #2,%d0
    btst #2,%d1
    bne 9f
    moveq #3,%d0
    btst #3,%d1
    bne 9f
41: btst #0,%d1
    beq 5f
    moveq #0,%d7
    subq.w #1,%d6
    bpl 5f
    move.w 4(%sp),%d6
    subq.w #1,%d6
5:  btst #1,%d1
    beq l_loop
    moveq #0,%d7
    addq.w #1,%d6
    cmp.w 4(%sp),%d6
    bcs l_loop
    moveq #0,%d6
    bra l_loop
9:  addq.l #6,%sp
    rts

| ---- sound test: d6 = number, d5 = last frame's buttons, d4 = direction hold time
| ---- sound test (the framed look): MUSIC: and SOUND FX: lines (Left / Right step their number, round their
| range), EXIT; Up / Down pick the line (the arrow), A plays (or, on EXIT, goes back), B stops everything, Start
| does nothing. d6 = the line, d5 / d4 = buttons' state.
sound_test:
    bsr framed_setup
    move.b #1,BIG_FLAG
    lea st2_title(%pc),%a0
    move.w #ST2_TITLE_POS,%d1
    moveq #0,%d2
    bsr big_print
    moveq #0,%d0                     | RAM is random at power-on: each number into its range
    move.b MUSIC_NO_RAM,%d0
    cmp.w #FIRST_SOUND,%d0
    bcs 1f
    cmp.w #FIRST_EFFECT,%d0
    bcs 2f
1:  move.b #FIRST_SOUND,MUSIC_NO_RAM
2:  move.b SOUND_NO,%d0
    cmp.w #SFX_COUNT,%d0
    bcs 4f
    clr.b SOUND_NO
4:  moveq #0,%d6
    move.w #0xFFFF,%d5
    moveq #0,%d4
st2_loop:
    lea st2_music(%pc),%a0           | MUSIC: nn
    move.b MUSIC_NO_RAM,%d0
    move.w #ST2_LINE0,%d1
    moveq #0,%d3
    sub.l %a2,%a2
    bsr st2_line
    bsr st2_sfx                      | SOUND FX: nn NAME (d0 = its code, a2 = its name)
    lea st2_effect(%pc),%a0
    move.w #ST2_LINE1,%d1
    moveq #1,%d3
    bsr st2_line
    lea st2_exit(%pc),%a0            | EXIT
    move.w #ST2_LINE2,%d1
    moveq #0,%d2
    bsr big_print
    moveq #2,%d3
    bsr big_arrow
    bsr frame_wait
    bsr buttons                      | d0 = held, d1 = new (repeats included for the directions)
    btst #0,%d1                      | Up / Down: the line
    beq 5f
    subq.w #1,%d6
    bpl 5f
    moveq #2,%d6
5:  btst #1,%d1
    beq 6f
    addq.w #1,%d6
    cmp.w #3,%d6
    bcs 6f
    moveq #0,%d6
6:  moveq #0,%d2                     | Left / Right: d2 = the step
    btst #2,%d1
    beq 7f
    moveq #-1,%d2
7:  btst #3,%d1
    beq 8f
    moveq #1,%d2
8:  tst.w %d2
    beq 12f
    tst.w %d6
    bne 10f
    moveq #0,%d0                     | MUSIC: round FIRST_SOUND .. FIRST_EFFECT-1
    move.b MUSIC_NO_RAM,%d0
    add.w %d2,%d0
    cmp.w #FIRST_SOUND,%d0
    bge 9f
    move.w #FIRST_EFFECT-1,%d0
9:  cmp.w #FIRST_EFFECT,%d0
    blt 91f
    move.w #FIRST_SOUND,%d0
91: move.b %d0,MUSIC_NO_RAM
    bra 12f
10: cmp.w #1,%d6
    bne 12f
    moveq #0,%d0                     | SOUND FX: the next / last in the list, round
    move.b SOUND_NO,%d0
    add.w %d2,%d0
    bpl 11f
    move.w #SFX_COUNT-1,%d0
11: cmp.w #SFX_COUNT,%d0
    blt 111f
    moveq #0,%d0
111: move.b %d0,SOUND_NO
12: btst #4,%d1                      | A: play / EXIT
    beq 14f
    moveq #0,%d0
    move.b MUSIC_NO_RAM,%d0
    tst.w %d6
    beq 13f
    bsr st2_sfx
    cmp.w #1,%d6
    beq 13f
    clr.b BIG_FLAG                   | EXIT: stop everything, back to the options
    bsr frame_hide
    move.w #0xFF,%d0
    bra queue                        | queue returns to our caller
13: bsr queue
14: btst #5,%d1                      | B: stop all
    beq st2_loop
    move.w #0xFF,%d0
    bsr queue
    bra st2_loop

| a sound test line: a0 = its label, d0 = its number (shown in hex after it), d1 = fix address, d3 = its line
st2_line:
    movem.l %d0-%d2/%a0-%a1,-(%sp)
    lea LINE_BUF,%a1
1:  move.b (%a0)+,(%a1)+
    bne 1b
    subq.l #1,%a1
    and.w #0xFF,%d0
    move.w %d0,%d2
    lsr.w #4,%d2
    bsr st2_digit
    move.w %d0,%d2
    and.w #15,%d2
    bsr st2_digit
    cmpa.l #0,%a2                    | a2: a name after it (0: none)
    beq 2f
    move.b #0x20,(%a1)+
3:  move.b (%a2)+,(%a1)+
    bne 3b
    subq.l #1,%a1
2:  clr.b (%a1)
    lea LINE_BUF,%a0
    moveq #0,%d2
    bsr big_print
    bsr big_arrow
    movem.l (%sp)+,%d0-%d2/%a0-%a1
    rts
st2_digit:
    add.b #0x30,%d2
    cmp.b #0x3A,%d2
    bcs 1f
    addq.b #7,%d2
1:  move.b %d2,(%a1)+
    rts

| the SOUND FX: line's sound (SOUND_NO = its place): d0 = its code, a2 = its name (padded)
st2_sfx:
    moveq #0,%d0
    move.b SOUND_NO,%d0
    mulu #SFX_ENTRY,%d0
    lea sfx_table(%pc),%a2
    add.w %d0,%a2
    moveq #0,%d0
    move.b (%a2)+,%d0
    rts
sfx_table:
    .byte SFX_TABLE_BYTES
    .even

st2_title:
    .ascii "SOUND TEST"
    .byte 0
st2_music:
    .ascii "MUSIC: "
    .byte 0
st2_effect:
    .ascii "SOUND FX: "
    .byte 0
st2_exit:
    .ascii "EXIT"
    .byte 0
    .even

| d0 = command -> the game's sound queue, all registers kept
queue:
    movem.l %d0-%d7/%a0-%a5,-(%sp)
    jsr QUEUE_SOUND
    movem.l (%sp)+,%d0-%d7/%a0-%a5
    rts

| buttons (either player): d0 = held (bit 0-3 up down left right, 4-7 A B C D, 8 Start), d1 = newly pressed, with
| held directions repeating after REPEAT_DELAY frames every REPEAT_RATE frames; d5 = last held, d4 = hold time
buttons:
    moveq #0,%d0
    move.b 0x10FD96,%d0
    or.b 0x10FD9C,%d0
    move.b 0x10FDAC,%d2
    and.b #5,%d2
    beq 26f
    bset #8,%d0
26: move.w %d5,%d1
    not.w %d1
    and.w %d0,%d1
    move.w %d0,%d5
    move.w %d0,%d2
    and.w #15,%d2
    beq 27f
    addq.w #1,%d4
    cmp.w #REPEAT_DELAY,%d4
    bcs 28f
    move.w %d4,%d2
    sub.w #REPEAT_DELAY,%d2
    ext.l %d2
    divu #REPEAT_RATE,%d2
    swap %d2
    tst.w %d2
    bne 28f
    move.w %d0,%d2
    and.w #15,%d2
    or.w %d2,%d1
    rts
27: moveq #0,%d4
28: rts

| a0 = zero-terminated text, d1 = fix-layer address; print_or_blank prints spaces instead when d2 != 0;
| print_attr uses the attribute (palette | tile base) in d7 instead of PAL's
print:
    moveq #0,%d2
print_or_blank:
    move.w %d7,-(%sp)
    move.w #PAL*0x1000+0x500,%d7
    bsr print_attr
    move.w (%sp)+,%d7
    rts
print_attr:
    tst.b BIG_FLAG
    bne big_print
    move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.w #32,0x3C0004              | next column
    move.w %d1,0x3C0000
10: moveq #0,%d0
    move.b (%a0)+,%d0
    beq 11f
    tst.w %d2
    beq 12f
    moveq #0x20,%d0
12: add.w %d7,%d0
    move.w %d0,0x3C0002
    bra 10b
11: move.w #1,0x3C0004
    move.w (%sp)+,%sr
    rts

| print_attr in the big font (BIG_FLAG): a0 = string (0-ended), d1 = fix address, d2 = 1: blanks instead
big_print:
    movem.l %d0-%d7/%a0-%a6,-(%sp)
    move.w %d1,%d0
    sub.w #0x7000,%d0
    move.w %d2,%d3
1:  moveq #0,%d1
    move.b (%a0)+,%d1
    beq 9f
    tst.w %d3
    beq 2f
    moveq #0x20,%d1
2:  cmp.b #0x3F,%d1                  | '?' (the font has none: two tiles made here)
    bne 21f
    move.w #QUESTION_TOP_WORD,%d2
    move.w #QUESTION_BOTTOM_WORD,%d4
    bra 22f
21: cmp.b #0x3A,%d1                  | ':' (the font has none: two of its full stop's dot tile, made here)
    bne 3f
    move.w #COLON_TOP_WORD,%d2
    move.w #COLON_BOTTOM_WORD,%d4
22:
    move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.w #1,0x3C0004
    move.w %d0,%d1
    add.w #0x7002,%d1
    move.w %d1,0x3C0000
    move.w %d2,0x3C0002
    move.w %d4,0x3C0002
    move.w (%sp)+,%sr
    add.w #0x20,%d0
    bra 1b
3:  sub.w #0x20,%d1
    add.w %d1,%d1
    lea FONT_TABLE_ADDR,%a1
    move.w (%a1,%d1.w),%d1
    movem.l %d0/%d3/%a0,-(%sp)
    jsr FONT_DRAW_ADDR
    movem.l (%sp)+,%d0/%d3/%a0
    add.w #0x20,%d0
    bra 1b
9:  movem.l (%sp)+,%d0-%d7/%a0-%a6
    rts

| list's line d3 (at fix address d1) in the big font: the arrow left of it if it's the selected one (d6), else blank
big_arrow:
    movem.l %d0-%d1,-(%sp)
    move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.w #1,0x3C0004
    add.w #2-64,%d1                  | the font draws 2 rows down; two columns to the left: a gap
    move.w %d1,0x3C0000
    cmp.w %d6,%d3
    bne 1f
    move.w #ARROW_TOP_WORD,0x3C0002
    move.w #ARROW_BOTTOM_WORD,0x3C0002
    bra 2f
1:  move.w #SPACE_TOP_WORD,0x3C0002
    move.w #SPACE_BOTTOM_WORD,0x3C0002
2:  move.w (%sp)+,%sr
    movem.l (%sp)+,%d0-%d1
    rts

| the framed look (OPTIONS): screen_setup, then the frame; the font's shades and the frame's palette black for now -
| they're put in at the screen loop's next frame (frame_wait), once its text is all printed: it appears whole
framed_setup:
    bsr screen_setup
    movem.l %d0-%d2/%a0-%a1,-(%sp)
    lea 0x400000+FONT_PAL_NO*32,%a1
    moveq #15,%d0
1:  clr.w (%a1)+
    dbf %d0,1b
    lea FRAME_PAL_ADDR,%a1
    moveq #15,%d0
2:  clr.w (%a1)+
    dbf %d0,2b
    st COLOURS_DUE
    move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.w #1,0x3C0004
    lea frame_words(%pc),%a0
    move.w #FRAME_SPR_NO*64,%d1
    moveq #19,%d2
3:  move.w %d1,0x3C0000
    moveq #27,%d0
4:  move.w (%a0)+,0x3C0002
    dbf %d0,4b
    add.w #64,%d1
    dbf %d2,3b
    move.w #0x8000+FRAME_SPR_NO,0x3C0000
    moveq #19,%d0
5:  move.w #0x0FFF,0x3C0002
    dbf %d0,5b
    move.w #0x8200+FRAME_SPR_NO,0x3C0000
    move.w #0xF80E,0x3C0002          | (y 0, 14 tiles tall)
    moveq #18,%d0
6:  move.w #0x40,0x3C0002
    dbf %d0,6b
    move.w #0x8400+FRAME_SPR_NO,0x3C0000
    move.w #0,0x3C0002
    move.w (%sp)+,%sr
    movem.l (%sp)+,%d0-%d2/%a0-%a1
    rts

| the screens' wait for the next frame: then (at the vblank) the framed look's colours, if they're due
frame_wait:
    jsr WAIT_FRAME
    tst.b COLOURS_DUE
    beq 9f
    movem.l %d0/%a0-%a1,-(%sp)
    lea font_colours(%pc),%a0
    lea 0x400000+FONT_PAL_NO*32,%a1
    moveq #15,%d0
1:  move.w (%a0)+,(%a1)+
    dbf %d0,1b
    lea frame_colours(%pc),%a0
    lea FRAME_PAL_ADDR,%a1
    moveq #15,%d0
2:  move.w (%a0)+,(%a1)+
    dbf %d0,2b
    clr.b COLOURS_DUE
    movem.l (%sp)+,%d0/%a0-%a1
9:  rts

frame_hide:
    move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.w #0x8200+FRAME_SPR_NO,0x3C0000
    move.w #0,0x3C0002
    move.w (%sp)+,%sr
    rts

font_colours:
    .word FONT_COLOUR_WORDS
frame_colours:
    .word FRAME_COLOUR_WORDS
frame_words:
    .word FRAME_WORD_LIST

blank:
    .ascii "BLANK_TEXT"
    .byte 0
saving:
    .ascii "SAVING"
    .byte 0
save_label:
    .ascii "SAVE_LABEL_NAME"
card_sig:
    .ascii "N@EDOH-LGPETOX"
card_title:
    .ascii "MEMORY CARD"
    .byte 0
st_nocard:
    .ascii "NO MEMORY CARD"
    .byte 0
st_unformatted:
    .ascii "CARD NOT FORMATTED"
    .byte 0
st_free:
    .ascii "FREE BLOCKS"
    .byte 0
confirm_delete:
    .ascii "DELETE THE SAVE"
    .byte 0
confirm_format:
    .ascii "FORMAT - ERASES ALL SAVES"
    .byte 0
push_blank:
    .ascii "           "
    .byte 0
opt_title:
    .ascii "OPTIONS"
    .byte 0
    .even
stage_ids:
    .byte STAGE_IDS
    .even
TABLES
"""
    tables = (string_table("menu_t", [m.ljust(width) for m, c in MENU])
              + string_table("menu_save_t", [m.ljust(width) for m, c in MENU_SAVE])
              + "menu_ids:\n    .byte %s\nmenu_save_ids:\n    .byte %s\n    .even\n" % (
                  ",".join(str(c) for m, c in MENU), ",".join(str(c) for m, c in MENU_SAVE))
              + string_table("opt_t", OPTIONS)
              + string_table("card_t", CARD_ACTIONS) + string_table("confirm_t", CONFIRM))
    consts = {
        "MENU_SAVE_COUNT": str(len(MENU_SAVE)), "MENU_COUNT": str(len(MENU)), "OPT_COUNT": str(len(OPTIONS)), "STAGE_COUNT": str(len(STAGES)),
        "CHOICE_OPTIONS": str(CHOICE_OPTIONS), "CHOICE_CONTINUE": str(CHOICE_CONTINUE),
        "PROBED": "0x%X" % PROBED, "TO_MENU_WORD": "0x%X" % TO_MENU, "FROM_ATTRACT_BYTE": "0x%X" % FROM_ATTRACT, "DIFF_WORD": "0x%X" % DIFF, "DIFF_SET": "0x%X" % DIFF_SET,
        "DIFF_HEARTS": "0x%X" % DIFF_HEARTS, "OPT_BUF": "0x%X" % OPT_BUF, "OPT_T_LEN": str(opt_len),
        "OPT_DIGIT": str(opt_digit), "OPT_LEVEL_AT": str(opt_level), "LEVEL_WIDTH": str(LEVEL_WIDTH),
        "SHORT_STAGE_NAMES": ",".join("0x%02X" % ord(c) for i, nm in STAGES for c in short_name(nm)), "OPT_ONOFF": str(opt_onoff), "OPT_DIFFICULTY": str(OPT_DIFFICULTY),
        "OPT_AUTO_SAVE": str(OPT_AUTO_SAVE), "OPT_MEMORY_CARD": str(OPTIONS.index("MEMORY CARD")), "AUTO_ON": "0x%X" % AUTO_ON, "AUTO_WORD": "0x%X" % AUTO,
        "GAME_SAVE_PREP": "0x%X" % GAME_SAVE_PREP, "RAM_CLEAR_REST": "0x%X" % RAM_CLEAR_REST, "BEST_SUB": "0x%X" % BEST_SUB,
        "SAVE_BUF": "0x%X" % SAVE_BUF, "HACK_SLOT": str(HACK_CARD_SUB), "LINE_BUF": "0x%X" % LINE_BUF,
        "SAVE_LABEL_NAME": SAVE_LABEL_NAME.ljust(12), "LABEL_NAME": str(len(SAVE_LABEL_NAME)), "LABEL_LEN": "20",
        "CARD_SIG_LEN": "14", "CARD_ACTION_COUNT": str(len(CARD_ACTIONS)),
        "CARD_STATUS_ADDR": "0x%X" % fix_addr(COL, 11), "CARD_FREE_ADDR": "0x%X" % fix_addr(COL + 12, 11),
        "CARD_LIST_ADDR": "0x%X" % fix_addr(COL, 13), "CARD_LIST_END": "0x%X" % fix_addr(COL, 27),
        "MAGIC": "0x%X" % MAGIC, "BIOS_CARD_CALL": "0x%X" % CARD, "APPLY_SAVE": "0x%X" % APPLY_SAVE,
        "BUILD_SAVE": "0x%X" % BUILD_SAVE, "TITLE_CARD": "0x%X" % TITLE_CARD,
        "SAVING_ADDR": "0x%X" % fix_addr(*SAVING_AT), "SAVING_ATTR": "0x%X" % SAVING_ATTR, "BLANK_TEXT": " " * width,
        "MENU_LAST_ADDR": "0x%X" % fix_addr(MENU_COL, MENU_LAST_ROW), "PUSH_START_ADDR": "0x%X" % PUSH_START_ADDR, "TITLE_ATTR": "0x%X" % (TITLE_PAL * 0x1000 + 0x500),
        "TITLE_ADDR": "0x%X" % fix_addr(COL, TITLE_ROW), "LIST_ADDR": "0x%X" % fix_addr(COL, LIST_ROW),
        "ST_NUMBER_ADDR": "0x%X" % fix_addr(COL, 7), "ST_HEX_ADDR": "0x%X" % fix_addr(COL + 8, 7),
        "ST_TYPE_ADDR": "0x%X" % fix_addr(COL, 9), "ST_HELP_ADDR": "0x%X" % fix_addr(COL, 13),
        "STAGE_IDS": ",".join(str(i) for i, n in STAGES), "TABLES": tables,
        "TITLE_TIMEOUT": "0x%X" % TITLE_TIMEOUT, "SYSTEM_MODE": "0x%X" % SYSTEM_MODE,
        "START_FLAGS": "0x%X" % START_FLAGS, "FRAME": "0x%X" % FRAME, "PUSH_START": "0x%X" % push_start_copy(rom),
        "PLAYER_START": "0x%X" % PLAYER_START, "LOAD": "0x%X" % LOAD, "HOW_TO_PLAY": "0x%X" % HOW_TO_PLAY,
        "ATTRACT_TOGGLE": "0x%X" % ATTRACT_TOGGLE, "CLEAR_FIX": "0x%X" % CLEAR_FIX,
        "CLEAR_SPRITES": "0x%X" % CLEAR_SPRITES, "WAIT_FRAME": "0x%X" % WAIT_FRAME,
        "QUEUE_SOUND": "0x%X" % QUEUE_SOUND, "FIRST_SOUND": "0x%X" % FIRST_SOUND,
        "LAST_SOUND": "0x%X" % LAST_SOUND, "FIRST_EFFECT": "0x%X" % FIRST_EFFECT,
        "CURSOR": "0x%X" % CURSOR, "SOUND_NO": "0x%X" % SOUND_NO, "MENU_OPEN": "0x%X" % MENU_OPEN,
        "MENU_CURSOR": "0x%X" % MENU_CURSOR, "MENU_PREV": "0x%X" % MENU_PREV, "ON_TITLE": "0x%X" % ON_TITLE,
        "START_BITS": "0x%X" % START_BITS, "CHOICE": "0x%X" % CHOICE, "STAGE_PICK": "0x%X" % STAGE_PICK, "COLOURS_DUE": "0x%X" % COLOURS_DUE,
        "SELECT_REQ": "0x%X" % SELECT_REQ, "TITLE_PHASE": "0x%X" % TITLE_PHASE, "OPT_CURSOR": "0x%X" % OPT_CURSOR, "PAL": str(PAL),
        "BLINK_ON": str(BLINK_ON), "BLINK_OFF": str(BLINK_OFF), "BIG_FLAG": "0x%X" % BIG_FONT,
        "ARROW_TOP_WORD": "0x%X" % (FONT_PAL << 12 | arrow[0]), "ARROW_BOTTOM_WORD": "0x%X" % (FONT_PAL << 12 | arrow[1]),
        "SPACE_TOP_WORD": "0x%X" % (FONT_PAL << 12 | FONT_SPACE),
        "SPACE_BOTTOM_WORD": "0x%X" % (FONT_PAL << 12 | FONT_SPACE + 0x10),
        "ST2_TITLE_POS": "0x%X" % fix_addr((40 - len("SOUND TEST")) // 2, BIG_TITLE_AT[1]),
        "ST2_LINE0": "0x%X" % fix_addr(BIG_LIST_AT[0], BIG_LIST_AT[1]),
        "ST2_LINE1": "0x%X" % fix_addr(BIG_LIST_AT[0], BIG_LIST_AT[1] + BIG_STEP),
        "ST2_LINE2": "0x%X" % fix_addr(BIG_LIST_AT[0], BIG_LIST_AT[1] + BIG_STEP * (len(OPTIONS) - 1) + 1),
        "MUSIC_NO_RAM": "0x%X" % MUSIC_NO, "SFX_COUNT": str(len(sfx)), "SFX_ENTRY": str(sfx_width + 2),
        "SFX_TABLE_BYTES": ",".join("0x%02X" % b for code, label in sfx
                                    for b in [code] + [ord(c) for c in label.ljust(sfx_width)] + [0]),
        "QUESTION_TOP_WORD": "0x%X" % (FONT_PAL << 12 | question[0]),
        "QUESTION_BOTTOM_WORD": "0x%X" % (FONT_PAL << 12 | question[1]),
        "COLON_TOP_WORD": "0x%X" % (FONT_PAL << 12 | colon), "COLON_BOTTOM_WORD": "0x%X" % (FONT_PAL << 12 | colon),
        "BIG_TITLE_POS": "0x%X" % fix_addr((40 - len(BIG_TITLE)) // 2, BIG_TITLE_AT[1]),
        "BIG_LIST_POS": "0x%X" % fix_addr(*BIG_LIST_AT), "BIG_STEP_ROWS": str(BIG_STEP),
        "FONT_TABLE_ADDR": "0x%X" % FONT_TABLE, "FONT_DRAW_ADDR": "0x%X" % FONT_DRAW, "FONT_PAL_NO": str(FONT_PAL),
        "FONT_COLOUR_WORDS": ",".join("0x%04X" % c for c in FONT_COLOURS),
        "FRAME_COLOUR_WORDS": ",".join("0x%04X" % c for c in FRAME_COLOURS),
        "FRAME_WORD_LIST": ",".join("0x%04X" % w for w in frame_words()),
        "FRAME_PAL_ADDR": "0x%X" % (0x400000 + FRAME_PAL_NO * 32), "FRAME_SPR_NO": str(FRAME_SPR),
        "REPEAT_DELAY": str(REPEAT_DELAY), "REPEAT_RATE": str(REPEAT_RATE),
    }
    for k in sorted(consts, key=len, reverse=True):
        src = src.replace(k, consts[k])
    base = rom.place_code(src, why="title menu, options screen (level select, sound test)")
    labels = {name: base + 4 * i for i, name in
              enumerate(("menu_frame", "start_pressed", "new_game", "how_to_play", "mode3_end",
                         "title_enter", "title_leave", "autosave", "save_over", "save_p1", "save_p2",
                         "game_save_prep", "ram_keep", "diff_dip"))}
    nops = bytes.fromhex("4E714E71")
    rom.write(TITLE_PUSH_START, bytes.fromhex("4EB9") + labels["menu_frame"].to_bytes(4, "big") + nops,
              expect=bytes.fromhex("4A6E7B7066044EBA0098"),
              why="title: the menu instead of PUSH START once Start is pressed")
    rom.write(PLAYER_START_CALL, bytes.fromhex("4EB9") + labels["start_pressed"].to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9000108DA"), why="PLAYER_START: on the title, Start opens the menu")
    rom.write(LOAD_CALL, bytes.fromhex("4EB9") + labels["new_game"].to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90000EEF2"), why="new game: the menu's choice instead of the card's LOAD prompt")
    rom.write(HOW_TO_PLAY_CALL, bytes.fromhex("4EB9") + labels["how_to_play"].to_bytes(4, "big") + nops,
              expect=bytes.fromhex("1D6E6800789E6100FDE8"), why="new game: the how-to-play unless a stage was picked")
    rom.write(MODE3_END, bytes.fromhex("4EB9") + labels["mode3_end"].to_bytes(4, "big"),
              expect=bytes.fromhex("1D7C00003004"), why="new game: start a stage picked in the level select")
    rom.write(TITLE_BODY, bytes.fromhex("4EB9") + labels["title_enter"].to_bytes(4, "big"),
              expect=bytes.fromhex("1D7C00203005"), why="title set-up: note the title phase")
    rom.write(TITLE_END, bytes.fromhex("4EB9") + labels["title_leave"].to_bytes(4, "big"),
              expect=bytes.fromhex("4EB900009FBE"), why="title end: the title phase is over")
    for site in STAGE_TITLE_CALLS:
        rom.write(site, bytes.fromhex("4EB9") + labels["autosave"].to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB900013C6E"), why="stage start: the title card, then an auto-save")
    for addr, target, stub, why in OLD_SAVES:
        rom.write(addr, bytes.fromhex("4EB9") + labels[stub].to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + target.to_bytes(4, "big"), why=why)
    rom.write(GAME_SAVE_CARD, bytes.fromhex("4EB9") + labels["game_save_prep"].to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90000F6B0"), why="the game's own save: the hack's label, marker and setting")
    rom.write(DIFF_DIP_READ, bytes.fromhex("4EB9") + labels["diff_dip"].to_bytes(4, "big"),
              expect=bytes.fromhex("10390010FD8C"), why="attract set-up: the difficulty chosen in the options")
    rom.write(RAM_CLEAR, bytes.fromhex("4EF9") + labels["ram_keep"].to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("204ED1FC0000F000"), why="attract RAM clear: keep the auto-save setting")
    rom.write(CARD_SUB_SET + 3, bytes([HACK_CARD_SUB]), expect=bytes.fromhex("00"),
              why="memory card: the hack's saves use sub-number 1 (the original game's use 0)")
