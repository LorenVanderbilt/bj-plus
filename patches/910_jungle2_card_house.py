NAME = "jungle2-card-house"
DESCRIPTION = "Jungle Zone 2: a path of falling ice blocks up from the top of the icy climb leads to a second card game house"

# A level's front layer, the one the hero stands on, is a map per 256x256 px block (MAP_TABLE), each made of four
# packed 8x8 grids of 16 px cells. The format is described in tools/hackbuild.py, Rom.map_quarter. Quarters can be
# shared (all the empty ones are), so the quarters of BLOCK that get a platform are packed again into free space and
# re-pointed. The platform is a copy of the stage's own floating one (PLATFORM_FROM, PLATFORM_SIZE cells in block 7).
# It's reached by ICE_BLOCKS: kind 0xB8, an ice block that shakes when stood on and then falls (0x18FD4, shared with
# the previous stage's falling grass platforms, whose palette isn't loaded here).
#
# Objects come from per-stage lists at 0x60502, read by the spawner at 0xFC46. Each stage has 16 bytes: +0 points to
# a count of positions per block, +4 to a table with a pointer per block (block N at N-1). In a block's list, a word
# 0x8000 | kind starts a run of that kind, and each word after it is a position: x in the high byte and y in the low
# byte, in 2 px units within the block, y up from its bottom.
#
# The door (DOOR_KIND) goes on the top platform. Kinds 0x40-0x5F are house doors, with the room in the kind's low 5
# bits; a door draws itself (frame 0x2074, sign above). Its room is new: ROOM, an unused slot of the room table at
# 0x132BC, set to the card game's routine (room 9's). Each room has a visited flag that makes its door vanish, so it
# needs its own rather than sharing Empire Marsh 3's.
STAGE_TABLE = 0x60502
STAGE = 3
MAP_TABLE = 0x7C432            # Jungle Zone 2's front layer
BLOCK = 5                      # the top of the icy climb. Blocks 1-6 are the stage's top row and 7-12 the bottom,
                               # so 5 is above 11; the summit is its bottom right, Blue at about col 10, row 10
PLATFORM_FROM = (7, 8, 8)      # (block, row, col) of the stage's floating platform
PLATFORM_SIZE = (2, 5)         # rows, cols
PLATFORMS = [(3, 0)]           # (row, col) of each copy's top left in BLOCK: the house's, up and left of the summit
ICE_KIND = 0xB8
ICE_BLOCKS = [(0x5F, 0x49), (0x50, 0x60), (0x3D, 0x60), (0x29, 0x60)]   # (x, y) in 2 px units; Blue
                               # stands 32 px above y. Up and right from the summit, then a row back left to the
                               # house's platform, which is too high to reach any other way
DOOR_KIND, DOOR_AT = 0x4A, (0x01, 0x78)  # room 10 (kind 0x40 + 10) on the top platform; (x, y) in 2 px units, with
                                         # its IN arrow overlapping the platform as doors do on the ground
ROOM_TABLE, ROOM, CARD_ROOM = 0x132BC, 10, 9
EMPTY_ROOM = 0x1333C           # the bare rts the unused slots point to


def apply(rom):
    # the platforms, into the map
    src = rom.map_block(MAP_TABLE, PLATFORM_FROM[0])
    g = rom.map_block(MAP_TABLE, BLOCK)
    empty = g[0][0]
    pr, pc = PLATFORM_FROM[1:]
    rows, cols = PLATFORM_SIZE
    touched = set()
    for r0, c0 in PLATFORMS:
        for r in range(rows):
            for c in range(cols):
                assert g[r0 + r][c0 + c] == empty, "Jungle Zone 2: block %d's cell %d,%d isn't empty" % (BLOCK, r0 + r, c0 + c)
                g[r0 + r][c0 + c] = src[pr + r][pc + c]
                touched.add((1 if r0 + r >= 8 else 0) | (2 if c0 + c >= 8 else 0))
    for q in sorted(touched):
        oy, ox = (8 if q & 1 else 0), (8 if q & 2 else 0)
        cells = [g[oy + i // 8][ox + i % 8] for i in range(64)]
        rom.put_map_quarter(MAP_TABLE, BLOCK, q, cells,
                            why="Jungle Zone 2: block %d's quarter %d with floating platforms" % (BLOCK, q))

    # the door, into the objects
    sections = rom.u32(STAGE_TABLE + 16 * STAGE + 4)
    ptrs = [rom.u32(sections + 4 * k) for k in range(32)]
    end = max(ptrs)
    assert all(ptrs[k] <= ptrs[k + 1] for k in range(31))
    k0 = BLOCK - 1
    extra = (0x8000 | DOOR_KIND).to_bytes(2, "big") + bytes(DOOR_AT)
    extra += (0x8000 | ICE_KIND).to_bytes(2, "big") + b"".join(bytes(p) for p in ICE_BLOCKS)
    start = ptrs[k0]
    own = bytes(rom.data[start:ptrs[k0 + 1]])
    tail = bytes(rom.data[ptrs[k0 + 1]:end])
    blob = own + extra + tail
    at = rom.alloc(len(blob))
    rom.data[at:at + len(blob)] = blob
    rom.write(sections + 4 * k0, at.to_bytes(4, "big"), expect=start.to_bytes(4, "big"),
              why="Jungle Zone 2: the top's objects, a card game door and ice blocks added")
    for k in range(k0 + 1, 32):
        new = at + len(own) + len(extra) + (ptrs[k] - ptrs[k0 + 1])
        rom.write(sections + 4 * k, new.to_bytes(4, "big"), expect=ptrs[k].to_bytes(4, "big"),
                  why="Jungle Zone 2: block %d's objects (moved with the top's)" % (k + 1))
    counts = rom.u32(STAGE_TABLE + 16 * STAGE)
    n = rom.data[counts + k0]
    assert n == len(own) // 4, "Jungle Zone 2: block %d's count %d isn't its list's" % (BLOCK, n)
    rom.write(counts + k0, bytes([n + 1 + len(ICE_BLOCKS)]), expect=bytes([n]),
              why="Jungle Zone 2: the top's object count, with the door and ice blocks")
    card = rom.u32(ROOM_TABLE + 4 * CARD_ROOM)
    rom.write(ROOM_TABLE + 4 * ROOM, card.to_bytes(4, "big"), expect=EMPTY_ROOM.to_bytes(4, "big"),
              why="room %d: a second card game (Jungle Zone 2's house)" % ROOM)

