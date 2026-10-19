NAME = "title-journey-up"
DESCRIPTION = "Title screen: the logo's JOURNEY (and its TM) sits a few pixels higher, closer under BLUE'S"

# The title logo is two sprite objects: BLUE'S (code 0x1BB8E) and JOURNEY (code 0x1BC08, frame 0x3488), which each
# frame takes BLUE'S y, zoom and priority - its y GAP lower (subi.w #GAP,(a5); y counts up, 128 a pixel: 0x1800 =
# 48 px). The gap is UP pixels smaller now: JOURNEY that much higher, BLUE'S where it was.
# Its TM is fix text, printed once as the logo settles (TM_PRINT: jsr 0x9FE6 with the record "TM" at fix TM_ADDR,
# fix palette 5 - the font's T and M, tiles TM_TILES). The fix layer moves in 8-px rows, so it's redrawn UP px higher
# across two rows (the glyphs' tops in the row above): 4 new fix tiles, written in place of the print.
GAP_AT = 0x1BC14               # (the subi.w's operand)
GAP = 0x1800
UP = 3                         # pixels
TM_PRINT = 0x1BBF8             # jsr 0x9FE6 ; dc 0x744F, 0xFC55, "TM", 0xFF, 0
TM_AFTER = 0x1BC06             # (past the record)
TM_ADDR = 0x744F               # fix: column 34, row 15
TM_TILES = (0x554, 0x54D)
TM_PALETTE = 5


def fix_pixels(rom, tile):
    at, b = tile * 32, rom.FIX_COLUMN_BYTE
    d = rom.fix_orig[at:at + 32]
    return [[(d[b[x] + y] >> (0 if x % 2 == 0 else 4)) & 15 for x in range(8)] for y in range(8)]


def apply(rom):
    rom.write(GAP_AT, (GAP - UP * 0x80).to_bytes(2, "big"), expect=GAP.to_bytes(2, "big"),
              why="title: JOURNEY %d px higher" % UP)
    assert 0 < UP < 8
    assert bytes(rom.data[TM_PRINT:TM_AFTER]) == bytes.fromhex("4EB900009FE6744FFC55544DFF00")
    words = []                 # (fix address, word) - each glyph's top UP rows in the row above, the rest below
    for n, tile in enumerate(TM_TILES):
        px = fix_pixels(rom, tile)
        above = [[0] * 8 for _ in range(8 - UP)] + px[:UP]
        below = px[UP:] + [[0] * 8 for _ in range(UP)]
        for dy, part in ((-1, above), (0, below)):
            t = rom.add_fix_tile(part, why="title: TM %d px higher (%s, %s)" % (UP, "TM"[n], "top" if dy else "bottom"))
            words.append((TM_ADDR + n * 32 + dy, TM_PALETTE << 12 | t))
    code = rom.place_code("".join("    move.w #0x%X,0x3C0000\n    move.w #0x%X,0x3C0002\n" % w for w in words) +
                          "    move.l #0x%X,(%%sp)\n    rts\n" % TM_AFTER, why="title: its TM, a little higher")
    rom.write(TM_PRINT, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("4EB900009FE6"),
              why="title: its TM printed higher")
