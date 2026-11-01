NAME = "clover-icon"
DESCRIPTION = "Item bar: the clover's icon gets the slot border the other items have (it sat a row lower)"

# The item bar's icons (see sta/aes/clover_bar.sta) are 2x2 fix tiles per slot, drawn by 0x4E6C4, with the slot
# border drawn into each icon. The clover's icon (0x403 / 0x404 over 0x413 / 0x414) is missing the bottom line of the
# inner border and its corners differ, so its black inside ran a row lower than the others. Its border rows
# (BORDER_ROWS) are now copied from the acorn bomb's icon (0x405 / 0x406 over 0x415 / 0x416), keeping the clover.
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
