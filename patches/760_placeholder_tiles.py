NAME = "placeholder-tiles"
DESCRIPTION = "More free sprite tiles for new art: 84 copies of the developers' placeholder tile the game never shows"

# At the end of the map screen's art (its mountains, 1P / 2P markers and Japanese place names, up to 0x57AB), before
# the Japanese title art at 0x5800, RUN holds 84 copies of one tile: a box with a diagonal line through it - a "no
# art here" filler. Nothing uses them (2026-10-19):
#   * no frame definition names them;
#   * none showed on screen: every save state (600 frames each), every recorded test clip, a boot through the title,
#     story and demo (9000 frames), and every background block of every area (0-0x28) loaded one by one - each
#     frame's auto-animation group included;
#   * spare-tiles took only blank runs, tile-pool only frames' duplicates - so these were left.
# They go on the end of rom.tile_pool (after spare-tiles'), so tiles already handed out keep their numbers.
# (Its own patch, last, so the tiles before it keep theirs.)
RUN = (0x57AC, 84)             # first, count
PLACEHOLDER = ["1111111111111111"] + ["1" + "".join("1" if x == 13 - y else "." for x in range(14)) + "1"
                                     for y in range(14)] + ["1111111111111111"]


def apply(rom):
    first, n = RUN
    tiles = list(range(first, first + n))
    want = [[1 if c == "1" else 0 for c in row] for row in PLACEHOLDER]
    for t in tiles:
        if rom.sprite_tile(t) != want:
            raise SystemExit("placeholder-tiles: tile 0x%X isn't the placeholder" % t)
    rom.log.append("  placeholder-tiles: %d placeholder tiles added to the pool" % n)
    rom.pooled = set(getattr(rom, "pooled", ())) | set(tiles)
    rom.tile_pool += tiles
