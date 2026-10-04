NAME = "chimney-smoke"
DESCRIPTION = "Houses: the chimney smoke drifts one way - three puffs to the right, one after another - not two mirrored at once"

# Each house (three kinds, the same code at three places) counts frames in +0x78 and every 64 spawns two smoke
# puffs (object 0x4999A, its animation 270) from its chimney: one 14 px in drifting left (x speed -32), one 22 px
# in drifting right (+32) - the same puff mirrored, both at once. Now only the right one is spawned, three times
# a cycle, PUFFS frames apart.
SITES = [(0x49316, 0x493A0), (0x4969C, 0x49726), (0x4983E, 0x498C8)]   # (andi.w #63,d0 ; bne <end>), <end>
PUFFS = [0, 12, 24]       # frames into each 64-frame cycle
NEW_OBJECT = 0xFFEC       # -> a1 (ne: none free)
SMOKE = 0x4999A
PUFF_X = 18               # px in from the house's x (the original right-hand puff's 22, nudged left)


def apply(rom):
    checks = "".join("    cmp.w #%d,%%d0\n    beq 1f\n" % p for p in PUFFS)
    for at, end in SITES:
        code = rom.place_code(
            "    and.w #63,%%d0\n"
            "%s"
            "    bra 9f\n"
            "1:  jsr 0x%X\n"
            "    bne 9f\n"
            "    move.l #0x%X,4(%%a1)\n"
            "    move.l (%%a5),(%%a1)\n"
            "    addi.w #0x400,(%%a1)             | (8 px up, as the original)\n"
            "    addi.w #0x%X,2(%%a1)\n"
            "    move.w #0,12(%%a1)\n"
            "    move.w #32,14(%%a1)\n"
            "    move.w #4,16(%%a1)\n"
            "    move.w #0,18(%%a1)\n"
            "    move.b #0x90,40(%%a1)\n"
            "9:  jmp 0x%X\n" % (checks, NEW_OBJECT, SMOKE, PUFF_X << 7, end),
            why="house chimney: puffs to the right, one after another")
        rom.write(at, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("0240003F6600"),
                  why="house chimney: the smoke's spawning")
