NAME = "clover-icon"
DESCRIPTION = "Item bar: the clover's icon gets the slot border the other items have (it sat a row lower)"

# The item bar's icons (sta/aes/clover_bar.sta) are fix tiles, 2 x 2 a slot (0x4E6C4 draws them; the clover's
# tiles 0x403 / 0x404 over 0x413 / 0x414), each with the slot's own border drawn in. The clover's lacks the inner
# border's bottom line (and its corner pixels differ), so its black inside ran a row lower than the others'. Its
# border rows (BORDER_ROWS) are now the acorn bomb's (0x405 / 0x406 over 0x415 / 0x416), the clover kept inside.
CLOVER, BOMB = 0x403, 0x405
BORDER_ROWS = [0, 1, 14, 15]


def tiles_of(top_left):
    return [top_left, top_left + 1, top_left + 0x10, top_left + 0x11]   # top left, top right, bottom left, right


def read(rom, index):
    at = index * 32
    return [[(rom.fix_orig[at + rom.FIX_COLUMN_BYTE[x] + y] >> (0 if x % 2 == 0 else 4)) & 15 for x in range(8)]
            for y in range(8)]


def icon(rom, top_left):
    tl, tr, bl, br = (read(rom, t) for t in tiles_of(top_left))
    return [tl[y] + tr[y] for y in range(8)] + [bl[y] + br[y] for y in range(8)]


def apply(rom):
    clover, bomb = icon(rom, CLOVER), icon(rom, BOMB)
    for r in BORDER_ROWS:
        clover[r] = list(bomb[r])
    parts = [[row[:8] for row in clover[:8]], [row[8:] for row in clover[:8]],
             [row[:8] for row in clover[8:]], [row[8:] for row in clover[8:]]]
    for index, pixels in zip(tiles_of(CLOVER), parts):
        tile = bytearray(32)
        for y in range(8):
            for x in range(8):
                tile[rom.FIX_COLUMN_BYTE[x] + y] |= (pixels[y][x] & 15) << (0 if x % 2 == 0 else 4)
        if tile != rom.fix_orig[index * 32:index * 32 + 32]:
            rom.fix[index * 32:index * 32 + 32] = tile
            rom.log.append("  fix 0x%03X  tile  item bar: the clover's border as the others'" % index)
