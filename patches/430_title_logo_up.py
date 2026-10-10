NAME = "title-logo-up"
DESCRIPTION = "Title screen: the ALPHA logo a row higher (more room above the copyright), the menu / PUSH START with it"

# The title's ALPHA logo is fix tiles (0xDC6-0xDDD, fix palette 8) printed by the title's set-up (0x1AF02:
# jsr 0x9FE6 with an inline record - per row a fix address word, then the tiles) at rows 23-25, right on top of
# the copyright (rows 26-27). Each row's address is one less now (a row up: rows 22-24). Above it, title-menu's
# menu and PUSH START / INSERT COIN move up a row with it (its MENU_LAST_ROW, PUSH_START_ADDR - PUSH START through
# a copy of its routine 0x1B034, which the other attract screens share: on TODAY'S BEST row 20 is a score line).
LOGO_ROWS = [0x1AF08, 0x1AF0E, 0x1AF18]           # the logo record's row addresses (0x7257, 0x7238, 0x7219)


def apply(rom):
    for at in LOGO_ROWS:
        old = rom.u16(at)
        rom.write(at, (old - 1).to_bytes(2, "big"), expect=old.to_bytes(2, "big"), why="title: ALPHA logo a row up")
