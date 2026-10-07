NAME = "title-logo-up"
DESCRIPTION = "Title screen: the ALPHA logo a row higher (more room above the copyright), the menu / PUSH START with it"

# The title's ALPHA logo is fix tiles (0xDC6-0xDDD, fix palette 8) printed by the title's set-up (0x1AF02:
# jsr 0x9FE6 with an inline record - per row a fix address word, then the tiles) at rows 23-25, right on top of
# the copyright (rows 26-27). Each row's address is one less now (a row up: rows 22-24). Above it, PUSH START /
# INSERT COIN (0x1B034's three records, at 0x71D5: column 14, row 21) and title-menu's menu (its last line on
# row 22 - title-menu's MENU_LAST_ROW, PUSH_START_ADDR) move up a row with it, so the logo doesn't meet them.
LOGO_ROWS = [0x1AF08, 0x1AF0E, 0x1AF18]           # the logo record's row addresses (0x7257, 0x7238, 0x7219)
PUSH_START = [0x1B04C, 0x1B064, 0x1B084]          # PUSH START / its blank / INSERT COIN: 0x71D5


def apply(rom):
    for at in LOGO_ROWS:
        old = rom.u16(at)
        rom.write(at, (old - 1).to_bytes(2, "big"), expect=old.to_bytes(2, "big"), why="title: ALPHA logo a row up")
    for at in PUSH_START:
        rom.write(at, bytes.fromhex("71D4"), expect=bytes.fromhex("71D5"), why="title: PUSH START a row up")
