NAME = "marsh2-step"
DESCRIPTION = "Empire Marsh 2: the step up beside the waterfall reaches further left, over the still water that didn't match the waves"

# Empire Marsh 2's front layer (map table MAP_TABLE; the map format: tools/hackbuild.py, Rom.map_quarter), block BLOCK: a grassy
# ledge (columns 9-14, its grass at rows 3-4) and to its right a step two tiles higher (its left edge column 15:
# grass tufts rows 0-1, the band's corner row 2, the edge row 3; on into block 19). Above the ledge the lake's
# surface row (tile 0x3C1) runs on as a still strip, with the waterfall's light foot in columns 13-14 - neither
# matching the waves behind. The step now starts at column EDGE (the user's pick: 2 tiles further left) - COLUMNS:
# the waterfall-with-tufts and the band from block 19 on to column 15, the tufts' left end at EDGE, the band's corner
# there the ledge's own (ragged over the water - the step's old edge pieces had the waterfall's water painted in),
# solid dirt below where the ledge's grass is in front; the ledge's band runs on into the step's face. The front layer is what the
# hero stands on: the new step is solid like the old. A flower that grew on the ledge where the step now is (FLOWER, in
# the stage's object list for the block: see jungle2-card-house) moves up onto it.
ENABLED = False                       # (parked 2026-10-25, after the beta - the user: not looking right yet; see TODO)
MAP_TABLE = 0x8F732
BLOCK = 12
EDGE = 13
COLUMNS = {                           # rows 1-4 of each column from EDGE on (row 0, the waterfall's top, as it is)
    "edge": [(0xEC00, 0x110A),         # 1: the waterfall with the step's grass tufts, their left end (the old edge's)
             (0xED20, 0x114C),         # 2: the band's left corner - a ragged border over the water (the ledge's own)
             (0xED50, 0x22A),          # 3: dirt, ragged on the left (the ledge's own edge) - above the ledge's grass
             (0xA970, 0x132)],         # 4: dirt, the ledge's band running into it
    "inside": [[(0xEC00, 0x10C7), (0xED10, 0x1148), (0xA970, 0x132), (0xA970, 0x132)],   # the tufts' middle, the band,
               [(0xEC00, 0x110B), (0xED10, 0x1149), (0xA970, 0x132), (0xA970, 0x128)]],  # dirt - alternating
}
LEDGE_BAND = (4, (0x9010, 0x1148))    # (row, cell): the ledge's band, on into the step's face (no end piece)
STAGE_TABLE, STAGE = 0x60502, 10      # the object lists; Empire Marsh 2
FLOWER = (0x200, (0x70, 0x68), (0x70, 0x70))   # (kind, where it was, where it goes): x, y (up) in 2 px units


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
