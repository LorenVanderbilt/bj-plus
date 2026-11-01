NAME = "chimney-smoke"
DESCRIPTION = "Houses: the chimney smoke drifts one way - three puffs to the right, one after another - not two mirrored at once"

# Each house (three kinds, with the same code in three places) counts frames in +0x78. Every 64 frames it spawns two
# smoke puffs (object 0x4999A, animation 270) from its chimney: one 14 px in drifting left (x speed -32) and one 22 px
# in drifting right (+32), so the same puff appeared mirrored, both at once. Now only the right-hand puff spawns,
# three times a cycle at the frames in PUFFS.
SITES = [(0x49316, 0x493A0), (0x4969C, 0x49726), (0x4983E, 0x498C8)]   # (andi.w #63,d0 ; bne <end>), <end>
PUFFS = [0, 12, 24]       # frames into each 64-frame cycle
NEW_OBJECT = 0xFFEC       # returns a1; ne if no slot is free
SMOKE = 0x4999A
PUFF_UP = 10              # px above the house's y; the original was 8
PUFF_X = 18               # px in from the house's x; the original right-hand puff was 22


def apply(rom):
    checks = "".join("    cmp.w #%d,%%d0\n    beq 1f\n" % p for p in PUFFS)
    for at, end in SITES:
        code = rom.place_code("""
    and.w #63,%%d0
%(checks)s    bra 9f
1:  jsr 0x%(new_object)X                | a new puff object (ne if none free)
    bne 9f
    move.l #0x%(smoke)X,4(%%a1)
    move.l (%%a5),(%%a1)                | at the house's place, PUFF_UP up and PUFF_X in
    addi.w #0x%(up)X,(%%a1)
    addi.w #0x%(x)X,2(%%a1)
    move.w #0,12(%%a1)
    move.w #32,14(%%a1)                 | drifting right
    move.w #4,16(%%a1)
    move.w #0,18(%%a1)
    move.b #0x90,40(%%a1)
9:  jmp 0x%(end)X
""" % {"checks": checks, "new_object": NEW_OBJECT, "smoke": SMOKE, "up": PUFF_UP << 7, "x": PUFF_X << 7, "end": end},
            why="house chimney: puffs to the right, one after another")
        rom.write(at, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("0240003F6600"),
                  why="house chimney: the smoke's spawning")
