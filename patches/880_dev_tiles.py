NAME = "dev-tiles"
DESCRIPTION = "More free sprite tiles for new art: the developers' test font, a boxed kanji, and two unused effect frames (45)"

# Tiles the released game never shows, checked 2026-10-24 (see art/reference/free_tile_candidates.png):
#   * FONT, the developers' test font: "TestSCR!89." and symbols (0x18-0x1F, 0x38-0x3F) and hand-drawn digits and
#     hex letters (0x70-0x7F). BOOK, the kanji for "book" in a box (0x1B6F). The only screens that could show them are
#     the developers' debug menu and its tests (SCROLL TEST, SPR PRINT and so on: game state 11, 0x12BDC). The game
#     only enters it when ROM byte 0xFF is 0xDB (0x11B16), and it's 0xFF in the released ROM.
#   * EFFECTS: frames 0x33F4 (a pinwheel) and 0x331C (dark leaves), which nothing references and whose tiles no other
#     frame uses.
# None of them is in a frame the game uses. Filled with solid colour, they changed nothing in any test clip (139 runs)
# or any of 105 save states, each played 450 frames with snapshots compared every 15. A census of every save and the
# attract mode (both regions) never saw them written to the sprite tables. Tiles 0x80-0x8F (slopes, pipe edges and a
# "15") passed too, but their neighbours are in use and they may be wanted for the sound test, so they're left alone.
# The tiles go on the end of rom.tile_pool, and this patch runs last, so tiles already handed out keep their numbers.
FONT = list(range(0x18, 0x20)) + list(range(0x38, 0x40)) + list(range(0x70, 0x80))
BOOK = [0x1B6F]
EFFECTS = [0x5E49, 0x5E4A, 0x5E4B, 0x5E4C, 0x5E4D, 0x5E4E, 0x5E4F, 0x5E50,   # pinwheel (frame 0x33F4)
           0x5AD0, 0x5AD1, 0x5AD2, 0x5AD3]                                   # dark leaves (frame 0x331C)
DEBUG_FLAG = (0xFF, 0xFF)      # ROM byte and its value; anything but 0xDB keeps the debug menu shut


def apply(rom):
    tiles = FONT + BOOK + EFFECTS
    assert rom.orig[DEBUG_FLAG[0]] == DEBUG_FLAG[1], "the debug menu's ROM flag changed"
    for t in tiles:
        a, b, at = rom._sprite_at(t)
        assert any(rom.sprites_orig[a][at:at + 64]) or any(rom.sprites_orig[b][at:at + 64]), "tile 0x%X blank?" % t
        assert t not in rom.tile_pool and t not in getattr(rom, "pooled", ()), "tile 0x%X already pooled" % t
    rom.log.append("  dev-tiles: %d tiles added to the pool" % len(tiles))
    rom.pooled = set(getattr(rom, "pooled", ())) | set(tiles)
    rom.tile_pool += tiles
