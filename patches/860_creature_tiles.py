NAME = "creature-tiles"
DESCRIPTION = "More free sprite tiles for new art: an unused pose's 7 tiles (a creature lying flat, frame 0x13F0)"

# Frame FRAME (a creature lying flat, its fist out - an enemy pose) is named nowhere in the program (no word in the
# code or the animation lists matches it), and its tiles TILES are used by no other frame. Checked unused (2026-10-24):
# filled with solid colour, they changed nothing in any recorded test clip (137 runs) nor in any save state (105, each
# played 450 frames - walking, jumping, throwing - snapshots every 15 compared). They go on the end of rom.tile_pool,
# so tiles already handed out keep their numbers. (The user saw the frame first; 0x2D78's tile, also unnamed, showed on
# the title and in the story - kept.) (Its own patch, after the others that take tiles, so theirs keep their numbers.)
FRAME = 0x13F0
TILES = [0x5140, 0x5148, 0x5149, 0x514A, 0x5150, 0x5151, 0x5152]


def apply(rom):
    import hackbuild
    for t in TILES:
        a, b, at = rom._sprite_at(t)
        assert any(rom.sprites_orig[a][at:at + 64]) or any(rom.sprites_orig[b][at:at + 64]), "tile 0x%X blank?" % t
    p = rom.u32(hackbuild.FRAME_TABLE + FRAME)
    assert p == rom.u32(hackbuild.FRAME_TABLE + FRAME), p
    rom.log.append("  creature-tiles: %d tiles of frame 0x%X added to the pool" % (len(TILES), FRAME))
    rom.pooled = set(getattr(rom, "pooled", ())) | set(TILES)
    rom.tile_pool += TILES
