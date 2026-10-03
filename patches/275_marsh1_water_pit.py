NAME = "marsh1-water-pit"
DESCRIPTION = "Empire Marsh 1: the pit with water at its bottom drowns the hero (it was a bottomless-pit fall)"

# The front layer's collision type is the attribute word's bits 4-7 (0xB: a fall, 0xC: water; see
# 0x45938: falling below 0x4800 or onto type 0xB is state 35, the fall death; type 0xC is state 36, drowning).
# In Empire Marsh 1 a pit left of the hero's restart point shows water at its bottom (a back layer, behind the
# item bar), but its bottom cells - tile 0x0100, blank - are type 0xB, so he just fell out of view. The level
# map stores runs of cells as attribute / tile entries (decoded by 0xD418: the attribute's bits 2-3 mark a run);
# the two runs that make those cells are made type 0xC: the same blank tile, now water.
RUNS = [0x880D5, 0x88236]     # attribute low byte 0xBC (type 0xB, run) -> 0xCC (type 0xC, run)


def apply(rom):
    for at in RUNS:
        rom.write(at, bytes([0xCC]), expect=bytes([0xBC]), why="Marsh 1 pit: water at the bottom (type 0xC)")
