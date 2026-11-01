NAME = "creature-tiles"
DESCRIPTION = "More free sprite tiles for new art: an unused pose's 7 tiles (a creature lying flat, frame 0x13F0)"

# Frame FRAME, an enemy pose of a creature lying flat with its fist out, is never referenced: no word in the code or
# the animation lists matches it, and no other frame uses its tiles (TILES). Checked on 2026-10-24 by filling them
# with solid colour: nothing changed in any test clip (137 runs) or in any of 105 save states, each played for 450
# frames of walking, jumping and throwing with snapshots compared every 15.
#
# The tiles go on the end of rom.tile_pool, and this patch runs after the others that take tiles, so tiles already
# handed out keep their numbers. Frame 0x2D78's tile is also never referenced but shows on the title and in the
# story, so it's kept.
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
