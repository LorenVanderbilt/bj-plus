NAME = "eyecatcher-letters"
DESCRIPTION = "The boot logo's MAX 330 MEGA / PRO-GEAR SPEC lettering as Joy Joy Kid has it (Blue's Journey's G of MEGA had a crooked bottom)"

# The user, 2026-11-10: the bottom of the G in MEGA is crooked. The BIOS's eyecatcher draws MAX 330 MEGA / PRO-GEAR
# SPEC (fix rows 16-19) from the cartridge's own S ROM tiles 0x005-0x107, so each game carries its own copy - and
# Blue's Journey's has a few stray pixels, the G's bottom (0x040 / 0x05F, fix 24-25,17) worst. Joy Joy Kid (the same
# year, ../jjk-plus) has them clean: the 7 tiles that differ from its S ROM take its pixels (palette index per pixel,
# "." = 0), so the logo matches Joy Joy Kid's exactly. The game itself doesn't draw these tiles.
TILES = {
    0x00B: ['........', '213...31', '312...21', '.213.312', '.312.213', '..21312.', '..31113.', '..32123.'],
    0x014: ['.....331', '.......3', '..21....', '..213..3', '..312332', '...21111', '....3223', '........'],
    0x015: ['........', '.....322', '2...2111', '13.31133', '11.313..', '13......', '1......3', '3.....11'],
    0x017: ['........', '3......3', '12....21', '113..312', '311..213', '313..21.', '11...11.', '13...11.'],
    0x040: ['...11111', '...11...', '...11...', '...11...', '3..11...', '3..11111', '3..11111', '........'],
    0x05F: ['..11...1', '..11...1', '..11....', '..213...', '..3123.3', '...31111', '....3212', '........'],
    0x0DF: ['11111113', '1111113.', '11...213', '11....12', '11....12', '11....11', '11....11', '........'],
}


def apply(rom):
    for index, rows in TILES.items():
        pixels = [[0 if c == "." else int(c, 16) for c in row] for row in rows]
        rom.replace_fix_tile(index, pixels, why="eyecatcher: Joy Joy Kid's lettering")
