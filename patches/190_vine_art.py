NAME = "vine-art"
DESCRIPTION = "Hero on vines: remove the stray pair of legs from the big-art climbing pose"

# With hero-big-art the hero climbs vines with the big (powerup) art's climbing frames. The first of those
# poses (animation frame 0x324 + 0x80) has a stray tile in it: its frame definition - a small table of
# [columns-1, rows-1, attribute], the tile number's high byte (0x36), then each column's low bytes top to
# bottom, 00 = blank, FF = end - lists tile 0x3680 at the top of its first column, and that tile is a piece of
# legs from a neighbouring frame. Drawn flipped (facing right) it appears as an extra set of legs above the
# hero's head, to the right. It is blanked in both copies of the frame (the second table at 0x6E436 holds
# the same poses with another attribute).
STRAY_TILES = [0x6D923, 0x6E437]   # the 0x80 of "36 80 88 90 00" (tile 0x3680)


def apply(rom):
    for addr in STRAY_TILES:
        rom.write(addr, b"\x00", expect=bytes.fromhex("80"), why="climbing pose: stray legs tile -> blank")
        if rom.data[addr - 1] != 0x36:
            raise SystemExit("unexpected frame data at 0x%X" % addr)
