NAME = "marsh2-step"
DESCRIPTION = "Empire Marsh 2: the step up beside the waterfall reaches further left, over the still water that didn't match the waves"

# Block BLOCK of Empire Marsh 2's front layer (map table MAP_TABLE; the map format is in tools/hackbuild.py,
# Rom.map_quarter) has a grassy ledge in columns 9-14 with a step two tiles higher to its right, starting at column 15.
# Above the ledge, the lake's surface row (tile 0x3C1) and the foot of the waterfall (columns 13-14) are a still strip
# that doesn't match the waves behind.
#
# The step now starts two tiles further left, at column EDGE, which covers the strip. COLUMNS holds the new cells:
# the waterfall with grass tufts on top, the ledge's ragged corner piece over the water, and solid dirt below. The
# ledge's grass band runs on into the step's face. The front layer is what Blue stands on, so the new step is solid.
#
# A flower on the ledge where the step now is (FLOWER, in the block's object list; see jungle2-card-house) moves up
# onto it.
ENABLED = False                       # parked 2026-10-25 until after the beta: not looking right yet (see TODO)
MAP_TABLE = 0x8F732
BLOCK = 12
EDGE = 13
COLUMNS = {                           # rows 1-4 of each column from EDGE on; row 0 (the waterfall's top) is kept
    "edge": [(0xEC00, 0x110A),         # waterfall with the left end of the grass tufts
             (0xED20, 0x114C),         # the band's left corner, ragged over the water
             (0xED50, 0x22A),          # dirt with a ragged left edge
             (0xA970, 0x132)],         # dirt, with the ledge's band running into it
    "inside": [[(0xEC00, 0x10C7), (0xED10, 0x1148), (0xA970, 0x132), (0xA970, 0x132)],   # tufts, band, dirt;
               [(0xEC00, 0x110B), (0xED10, 0x1149), (0xA970, 0x132), (0xA970, 0x128)]],  # the two alternate
}
LEDGE_BAND = (4, (0x9010, 0x1148))    # (row, cell): the ledge's band continuing into the step, no end piece
STAGE_TABLE, STAGE = 0x60502, 10      # object lists; Empire Marsh 2
FLOWER = (0x200, (0x70, 0x68), (0x70, 0x70))   # (kind, old x/y, new x/y) in 2 px units, y up


def apply(rom):
    if not ENABLED:
        return
    g = rom.map_block(MAP_TABLE, BLOCK)
    assert g[2][15] == (0xC320, 0x1104), "marsh2-step: the step's edge isn't where it was"
    for c in range(EDGE, 16):
        rows = COLUMNS["edge"] if c == EDGE else COLUMNS["inside"][(c - EDGE - 1) % 2]
        for r, cell in enumerate(rows, start=1):
            g[r][c] = cell
    r, cell = LEDGE_BAND
    g[r][EDGE - 1] = cell
    for q in range(4):
        oy, ox = (8 if q & 1 else 0), (8 if q & 2 else 0)
        cells = [g[oy + i // 8][ox + i % 8] for i in range(64)]
        if rom.map_quarter(rom.u32(MAP_TABLE + 16 * BLOCK + 4 * q)) == cells:
            continue
        rom.put_map_quarter(MAP_TABLE, BLOCK, q, cells,
                            why="Empire Marsh 2: block %d quarter %d - the step reaching left" % (BLOCK, q))

    # the flower, up onto the step
    kind, was, now = FLOWER
    counts, lists = rom.u32(STAGE_TABLE + 16 * STAGE), rom.u32(STAGE_TABLE + 16 * STAGE + 4)
    a, n, k, found = rom.u32(lists + 4 * (BLOCK - 1)), rom.data[rom.u32(STAGE_TABLE + 16 * STAGE) + BLOCK - 1], None, None
    seen = 0
    while seen < n:
        w = rom.u16(a)
        if w & 0x8000:
            k = w & 0x7FFF
        else:
            if k == kind and (w >> 8, w & 0xFF) == was:
                found = a
            seen += 1
        a += 2
    assert found, "marsh2-step: the flower isn't in the list"
    rom.write(found, bytes(now), expect=bytes(was), why="Empire Marsh 2: a flower up onto the step")
