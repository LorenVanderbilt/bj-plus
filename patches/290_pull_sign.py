NAME = "pull-sign"
DESCRIPTION = "End-of-level hook: its sign reads PULL (was TOUCH)"

# The sign by the end-of-level hook (object 0x52520) is frame 0x2D08: 2 x 2 tiles, the word in the top two
# (0x5166, 0x5167; rows 1-10), the arrow below - its tip reaching into row 10. The word is redrawn there: U as
# the game's own, P and L drawn in the same style (outline 0xF, the strokes' shading 7 5 3 1 3 5 7 E going down,
# bars as T's and H's); letters 5 px apart sharing their outlines, as TOUCH's, only into empty pixels so the
# arrow's tip stays.
FRAME = 0x2D08
WORD_TOP = 1              # the letters' first row
WORD_X = 2                # PULL's first column (21 px wide; TOUCH was 27 from column 1)
GLYPHS = {   # rows 1-10 of each letter, 6 columns (the outer ones shared with the neighbours)
    "P": [".FFFF.", "F7777F", "F5EE5F", "F3FF3F", "F1111F", "F3EEEF", "F5FFF.", "F7F...", "FEF...", ".F...."],
    "U": [".F..F.", "F7FF7F", "F5FF5F", "F3FF3F", "F3FF1F", "F3FF3F", "F5FF5F", "FE77EF", "FFEEFF", "..FF.."],
    "L": [".F....", "F7F...", "F5F...", "F3F...", "F1F...", "F3F...", "F5FFFF", "F7777F", "FEEEEF", ".FFFF."],
}
WORD = "PULL"


def apply(rom):
    tiles, palette = rom.frame_tiles(FRAME)
    top = [rom.sprite_tile(t) for t in tiles[0]]
    canvas = [top[0][y] + top[1][y] for y in range(16)]
    # the old word out: rows 0-9 entirely, row 10 but for the arrow's tip (columns 20-23)
    for y in range(11):
        for x in range(32):
            if y < 10 or not 20 <= x <= 23:
                canvas[y][x] = 0
    for i, ch in enumerate(WORD):
        x0 = WORD_X + 5 * i
        for dy, row in enumerate(GLYPHS[ch]):
            for dx, c in enumerate(row):
                if c != "." and canvas[WORD_TOP + dy][x0 + dx] == 0:
                    canvas[WORD_TOP + dy][x0 + dx] = int(c, 16)
    new = [rom.add_sprite_tile([row[16 * k:16 * k + 16] for row in canvas], why="PULL sign") for k in range(2)]
    rom.replace_frame(FRAME, [new, tiles[1]], palette, why="the end-of-level sign: PULL")
