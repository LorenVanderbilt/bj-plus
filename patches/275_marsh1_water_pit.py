NAME = "marsh1-water-pit"
DESCRIPTION = "Empire Marsh 1: the pit with water at its bottom is water (it was a bottomless-pit fall), drawn in the playfield"

# The front layer's collision type is in bits 4-7 of the attribute word: 0xB is a fall and 0xC is water. In 0x45938,
# falling below 0x4800 or onto type 0xB gives state 35, the fall death, and type 0xC gives state 36, drowning.
#
# In Empire Marsh 1, a pit left of the hero's restart point shows water at its bottom, but only on a back layer. Its
# front layer cells are blank (tile 0x0100), with the surface row type 0 and the bottom row type 0xB, so he just fell
# out of view. And if he drowned there, nothing in the front layer could cover him, since drown-in-front copies the
# front layer's water over a sinking hero.
#
# The level map stores runs of cells as 4-byte entries: an attribute (bits 2-3 of its low byte mark a run, masked off
# by 0xD418) and a tile. The four runs that make those cells, each one cell across two strips, now give the open
# water the other pits use: tile 0x02E0 for the surface and 0x02E8 below (0x02D0 / 0x02D8 are its edge against a
# ledge), palette 0x91, type 0xC. A run can't carry the auto-animation bit, since 0xD418 masks bits 2-3 off, so the
# decoder's end puts it back for exactly these cells (attribute 0x91C0 with tile 0x02E0 / 0x02E8, which appears
# nowhere else without its animation). They sparkle with the rest of the water.
ENABLED = False                # parked 2026-10-27 until after the beta, to revisit (see TODO)
RUNS = [
    (0x880BD, "810C0100", "91CC02E0"),   # surface row, strips 14-15 of the block
    (0x8821B, "810C0100", "91CC02E0"),   # surface row, strips 16-17
    (0x880D4, "81BC0100", "91CC02E8"),   # bottom row, strips 14-15
    (0x88235, "81BC0100", "91CC02E8"),   # bottom row, strips 16-17
]
DECODER_END = 0xD428            # andi.b #0xF3,d1 ; swap d1 ; move.b (a3)+,d1 ; rts, with d1 = attribute : tile


def apply(rom):
    if not ENABLED:
        return
    for at, old, new in RUNS:
        rom.write(at, bytes.fromhex(new), expect=bytes.fromhex(old), why="Marsh 1 pit: water tiles (type 0xC)")
    hook = rom.place_code("""
    andi.b #0xF3,%d1
    swap %d1
    move.b (%a3)+,%d1
    cmp.l #0x91C002E0,%d1
    beq.s 1f
    cmp.l #0x91C002E8,%d1
    bne.s 2f
1:  or.l #0x00040000,%d1                | 4-frame auto-animation, like the water around it
2:  rts
""", why="map runs: the Marsh 1 pit's water animates")
    rom.write(DECODER_END, bytes.fromhex("4EF9") + hook.to_bytes(4, "big"), expect=bytes.fromhex("020100F34841"),
              why="map run decoder: animate the Marsh 1 pit's water")
