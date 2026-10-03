NAME = "marsh1-water-pit"
DESCRIPTION = "Empire Marsh 1: the pit with water at its bottom is water (it was a bottomless-pit fall), drawn in the playfield"

# The front layer's collision type is the attribute word's bits 4-7 (0xB: a fall, 0xC: water; see
# 0x45938: falling below 0x4800 or onto type 0xB is state 35, the fall death; type 0xC is state 36, drowning).
# In Empire Marsh 1 a pit left of the hero's restart point shows water at its bottom, but only on a back layer:
# its front-layer cells are blank (tile 0x0100), the surface row type 0 and the bottom row type 0xB - he just fell
# out of view, and once drowning there, nothing in the front layer could cover him (drown-in-front copies the
# front layer's water over a sinking hero).
# The level map stores runs of cells as 4-byte entries: attribute (its low byte's bits 2-3 mark a run, masked off
# by 0xD418), tile. The four runs that make those cells (each one cell of two strips) now give the other pits'
# open water: tile 0x02E0 (surface) / 0x02E8 (below; 0x02D0 / 0x02D8 are its edge against a ledge), palette 0x91,
# type 0xC. A run can't carry the auto-animation bit (0xD418 masks bits 2-3 off: the map uses them to mark the
# run), so the decoder's end now puts it back for exactly these cells (attribute 0x91C0 with tile 0x02E0 / 0x02E8:
# open water without its animation appears nowhere else) - they sparkle with the rest of the water.
RUNS = [
    (0x880BD, "810C0100", "91CC02E0"),   # surface row, strips 14-15 of the block
    (0x8821B, "810C0100", "91CC02E0"),   # surface row, strips 16-17
    (0x880D4, "81BC0100", "91CC02E8"),   # bottom row, strips 14-15
    (0x88235, "81BC0100", "91CC02E8"),   # bottom row, strips 16-17
]


DECODER_END = 0xD428            # andi.b #0xF3,d1 ; swap d1 ; move.b (a3)+,d1 ; rts  (d1 = attribute : tile)


def apply(rom):
    for at, old, new in RUNS:
        rom.write(at, bytes.fromhex(new), expect=bytes.fromhex(old), why="Marsh 1 pit: water tiles (type 0xC)")
    hook = rom.place_code(
        "    andi.b #0xF3,%d1\n"
        "    swap %d1\n"
        "    move.b (%a3)+,%d1\n"
        "    cmp.l #0x91C002E0,%d1\n"
        "    beq.s 1f\n"
        "    cmp.l #0x91C002E8,%d1\n"
        "    bne.s 2f\n"
        "1:  or.l #0x00040000,%d1             | auto-animation (4 frames), as the water around it\n"
        "2:  rts\n",
        why="map runs: the Marsh 1 pit's water animates")
    rom.write(DECODER_END, bytes.fromhex("4EF9") + hook.to_bytes(4, "big"), expect=bytes.fromhex("020100F34841"),
              why="map run decoder: animate the Marsh 1 pit's water")
