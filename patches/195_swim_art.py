NAME = "swim-art"
DESCRIPTION = "Big hero swimming: remove the stray leg and dash from the big-art swim poses"

# With hero-big-art the hero swims (animation 0x18) with the big art's swim poses 0x330 / 0x334 / 0x338. Two of
# their tiles carry pieces of other poses in the same 16x16 block:
#   * frame 0x334's top-right tile, 0x36A5, is also used by the caught-in-the-web pose 0x3B0, where it is a leg;
#     in the swim pose nothing of it belongs (it connects to nothing), so a leg floats over the hero - on his
#     left when he swims right (the art is flipped);
#   * frame 0x338's top-right tile, 0x36B2, has a stray dash in its top row.
# The shared tiles stay as they are; the swim frames (and player 2's copies of them, 0xB34 / 0xB38, the same poses
# in player 2's palette) get new definitions: without 0x36A5, and with a cleaned copy of 0x36B2 (a new sprite tile).
FIXES = [
    # (frames, tile, rows of it to clear - all of them: leave the tile out)
    ((0x334, 0xB34), 0x36A5, range(0, 16)),
    ((0x338, 0xB38), 0x36B2, range(0, 1)),
]


def apply(rom):
    for frames, tile, rows in FIXES:
        pixels = rom.sprite_tile(tile)
        for y in rows:
            pixels[y] = [0] * 16
        new = (rom.add_sprite_tile(pixels, why="swim pose: tile 0x%X without the stray piece" % tile)
               if any(any(r) for r in pixels) else None)
        for frame in frames:
            tiles, palette = rom.frame_tiles(frame)
            if not any(t == tile for row in tiles for t in row):
                raise SystemExit("swim-art: frame 0x%X doesn't use tile 0x%X" % (frame, tile))
            tiles = [[new if t == tile else t for t in row] for row in tiles]
            rom.replace_frame(frame, tiles, palette, why="swim pose without the stray piece")
