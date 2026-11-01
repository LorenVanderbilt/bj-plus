NAME = "beta-no-card-options"
DESCRIPTION = "Options: AUTO SAVE and MEMORY CARD left out for the beta (auto-save can't run) - LEVEL, SOUND TEST, DIFFICULTY, BACK TO TITLE"

# The memory card's auto-save and manager are left out of the beta (decided 2026-10-25); ENABLED = False brings them
# back. title-menu's options screen draws OPT_COUNT lines from a table of string offsets (the option strings, copied
# to RAM with the settings filled in) and acts on the chosen line by number: AUTO SAVE is 3, MEMORY CARD is 4, and
# anything else past DIFFICULTY is BACK TO TITLE. title-menu doesn't export its addresses, so these are found by
# their bytes:
#   * LIST_COUNT becomes 4 lines. The list expects the strings to start after that many offset words (2 x 4 bytes
#     in, not 2 x 6), so the table's first 4 offsets each grow by 4; the strings stay put, since the settings are
#     filled in at fixed places in them. The lines are LEVEL, SOUND TEST, DIFFICULTY and BACK TO TITLE.
#   * The AUTO SAVE and MEMORY CARD checks compare against a line that doesn't exist (NO_LINE), so line 4 is BACK TO
#     TITLE.
#   * The stage start's calls (STAGE_TITLE_CALLS) go straight to the title card again rather than through
#     title-menu's auto-save, so a card set to auto-save by an earlier build can't save in the beta either.
# The game's own save prompts, and CONTINUE from a save, are unchanged.
ENABLED = True
LIST_COUNT = bytes.fromhex("7E0650F9")        # moveq #OPT_COUNT,d7 ; st BIG_FLAG
AUTO_CHECK = bytes.fromhex("0C4600036600")    # cmp.w #OPT_AUTO_SAVE,d6 ; bne
CARD_CHECK = bytes.fromhex("0C4600046600")    # cmp.w #OPT_MEMORY_CARD,d6 ; bne
STRINGS = b"LEVEL: "                          # the table's first string; the offsets are the 6 words before it
BACK = b"BACK TO TITLE\x00"
SHOWN, NO_LINE = 4, 0x7F
STAGE_TITLE_CALLS = [0x13A6A, 0x11486]        # title-menu's jsr <auto-save>, originally jsr TITLE_CARD
TITLE_CARD = 0x13C6E


def find(rom, pat):
    at = bytes(rom.data).find(pat)
    assert at > 0 and bytes(rom.data).find(pat, at + 1) < 0, "beta-no-card-options: %r not found once" % pat
    return at


def apply(rom):
    if not ENABLED:
        return
    at = find(rom, LIST_COUNT)
    rom.write(at, bytes([0x7E, SHOWN]), expect=LIST_COUNT[:2], why="options: 4 lines (no AUTO SAVE, MEMORY CARD)")
    strings = find(rom, STRINGS + b" ")
    table = strings - 12
    back = bytes(rom.data).find(BACK, strings) - strings
    old = [rom.u16(table + 2 * i) for i in range(6)]
    assert old[0] == 0 and old[5] == back
    shift = 2 * (6 - SHOWN)
    new = [old[0] + shift, old[1] + shift, old[2] + shift, back + shift]
    rom.write(table, b"".join(v.to_bytes(2, "big") for v in new), expect=rom.data[table:table + 8],
              why="options: the 4 lines' offsets (the 4th BACK TO TITLE)")
    for pat, what in ((AUTO_CHECK, "AUTO SAVE"), (CARD_CHECK, "MEMORY CARD")):
        at = find(rom, pat)
        rom.write(at + 2, NO_LINE.to_bytes(2, "big"), expect=pat[2:4], why="options: no %s line" % what)
    for site in STAGE_TITLE_CALLS:
        assert rom.u16(site) == 0x4EB9
        rom.write(site + 2, TITLE_CARD.to_bytes(4, "big"), expect=rom.data[site + 2:site + 6],
                  why="stage start: the title card, no auto-save (the beta)")
