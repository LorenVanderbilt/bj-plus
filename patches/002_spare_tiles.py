NAME = "spare-tiles"
DESCRIPTION = "More free sprite tiles for new art: runs of blank tiles the game never uses (padding between graphics sets)"

# The C ROMs hold 1257 blank tiles; most are single blanks the art uses on purpose (empty spots in frames and
# maps), but some are long runs - padding at the end of a graphics set. RUNS are those that nothing uses:
#   * no frame definition names them (as tile-pool's decode reads them);
#   * none showed on screen in any of the 81 save states (a census of every visible sprite's tile, each frame's
#     auto-animation group included, over 150 frames each, 2026-10-06);
#   * the program names none of them: the words in the code that match are frame numbers (object +8, animation
#     lists - 0x2BB0..., 0x2CE0...) or other bytes, not tiles.
# Runs below 0x100 (0x26, 0x5B) are left alone: the BIOS's boot logo draws tiles from there. They're added to the
# end of rom.tile_pool (add_sprite_tile's tiles after its own range), so tiles already handed out keep their numbers.
RUNS = [(0x9D3, 13), (0x2BAD, 19), (0x2CD3, 45), (0x2F6C, 20), (0x333B, 9), (0x4FF0, 16)]   # (first, count): 122


def apply(rom):
    blank = bytes(64)
    tiles = [t for first, n in RUNS for t in range(first, first + n)]
    for t in tiles:
        a, b, at = rom._sprite_at(t)
        if rom.sprites_orig[a][at:at + 64] != blank or rom.sprites_orig[b][at:at + 64] != blank:
            raise SystemExit("spare-tiles: tile 0x%X isn't blank" % t)
    rom.log.append("  spare-tiles: %d blank tiles added to the pool" % len(tiles))
    rom.tile_pool += tiles
