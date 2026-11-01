NAME = "title-logo-up"
DESCRIPTION = "Title screen: the ALPHA logo a row higher (more room above the copyright), the menu / PUSH START with it"

# The title's ALPHA logo is fix tiles 0xDC6-0xDDD (fix palette 8), printed by the title set-up at 0x1AF02 with
# jsr 0x9FE6 and an inline record (a fix address per row, then the tiles). It sat at rows 23-25, right against the
# copyright at rows 26-27. Each row's address is now one less, moving it up to rows 22-24.
#
# title-menu's menu and PUSH START / INSERT COIN move up a row with it (its MENU_LAST_ROW and PUSH_START_ADDR).
# PUSH START is drawn through a copy of 0x1B034, since the other attract screens share that routine and row 20 is
# a score line on TODAY'S BEST.
LOGO_ROWS = [0x1AF08, 0x1AF0E, 0x1AF18]           # the logo record's row addresses (0x7257, 0x7238, 0x7219)


def apply(rom):
    for at in LOGO_ROWS:
        old = rom.u16(at)
        rom.write(at, (old - 1).to_bytes(2, "big"), expect=old.to_bytes(2, "big"), why="title: ALPHA logo a row up")
