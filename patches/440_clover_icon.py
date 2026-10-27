NAME = "clover-icon"
DESCRIPTION = "Item bar: the clover's icon gets the slot border the other items have (it sat a row lower)"

# The item bar's icons (sta/aes/clover_bar.sta) are fix tiles, 2 x 2 a slot (0x4E6C4 draws them; the clover's
# tiles 0x403 / 0x404 over 0x413 / 0x414), each with the slot's own border drawn in. The clover's lacks the inner
# border's bottom line (and its corner pixels differ), so its black inside ran a row lower than the others'. Its
# border rows (BORDER_ROWS) are now the acorn bomb's (0x405 / 0x406 over 0x415 / 0x416), the clover kept inside.
CLOVER, BOMB = 0x403, 0x405
BORDER_ROWS = [0, 1, 14, 15]


def apply(rom):
    clover, bomb = rom.fix_glyph16(CLOVER), rom.fix_glyph16(BOMB)
    for r in BORDER_ROWS:
        clover[r] = list(bomb[r])
    for dy in range(2):
        for dx in range(2):
            index = CLOVER + dy * 0x10 + dx
            pixels = [row[dx * 8:dx * 8 + 8] for row in clover[dy * 8:dy * 8 + 8]]
            if pixels != rom.fix_tile(index):
                rom.replace_fix_tile(index, pixels, why="item bar: the clover's border as the others'")
