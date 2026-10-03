NAME = "marsh1-water-pit"
DESCRIPTION = "Empire Marsh 1: the pit with water at its bottom drowns the hero (it was a bottomless-pit fall)"

# The front layer's collision type is the attribute word's bits 4-7 (0xB: a fall, 0xC: water; see
# 0x45938: falling below 0x4800 or onto type 0xB is state 35, the fall death; type 0xC is state 36, drowning).
# In Empire Marsh 1 a pit left of the hero's restart point shows water at its bottom (a back layer, behind the
# item bar), but its bottom cells - tile 0x0100, blank - are type 0xB, so he just fell out of view. The level
# map stores runs of cells as attribute / tile entries (decoded by 0xD418: the attribute's bits 2-3 mark a run);
# the two runs that make those cells are made type 0xC: the same blank tile, now water.
# The row above them (where the water's surface shows, as in the other pits) was type 0: the hero and enemies
# only met the water a row (16 px) too low, behind the item bar. Its two runs (each just that one cell of two
# strips) are made type 0xC too.
RUNS = [(0x880D5, 0xBC), (0x88236, 0xBC),     # the bottom row: 0xBC (type 0xB, run) -> 0xCC
        (0x880BE, 0x0C), (0x8821C, 0x0C)]     # the surface row: 0x0C (type 0, run) -> 0xCC


def apply(rom):
    for at, old in RUNS:
        rom.write(at, bytes([0xCC]), expect=bytes([old]), why="Marsh 1 pit: water (type 0xC)")
