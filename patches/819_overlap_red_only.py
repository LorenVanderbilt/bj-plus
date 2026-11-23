NAME = "overlap-red-only"
DESCRIPTION = "Hit tests: hero-big-art's check for Red's bigger box only runs while Red is about (it ran for every pair tested)"

# Slowdown (2026-11-22): hero-big-art gives Red, drawn big in his duels, a bigger hit box: the overlap test's lookup
# of the other object's box (PAIR_SITE) goes through a hook that checks for him. That ran for every pair the test
# looked at - about 100 a frame on a busy screen, 4-5% of the work - though Red only appears in the torch duel and
# the ending. Now the game's own instructions are back at PAIR_SITE, and the routine's two entries (ENTRIES) check
# once per call whether Red is noted (RED_OBJ): if he is, the call runs a copy of the whole routine (OVERLAP: it's
# self-contained - every branch lands inside it), which keeps the hook; if not, the game's own.
OVERLAP = (0xB604, 0xBC58)   # the overlap test, start to end (entries 0xB604 and 0xB642)
ENTRIES = [0xB604, 0xB642]   # cmpi.w #-1024,2(a5) - each entry's first instruction
ENTRY_FIRST = bytes.fromhex("0C6DFC000002")
PAIR_SITE = 0xB6A0           # hero-big-art's jsr <its box lookup> ; nop
GAME_PAIR = bytes.fromhex("3A280008 24715000".replace(" ", ""))   # move.w 8(a0),d5 ; movea.l (a1,d5.w),a2
RED_OBJ = 0x10EA50           # hero-big-art: the object noted as Red (a long; 0 = none)


def apply(rom):
    start, end = OVERLAP
    assert rom.u16(PAIR_SITE) == 0x4EB9 and rom.u16(PAIR_SITE + 6) == 0x4E71
    for at in ENTRIES:
        assert bytes(rom.data[at:at + 6]) == ENTRY_FIRST, hex(at)
    copy = rom.other_patch("hero-big-art").relocated(bytes(rom.data[start:end]), start, end)
    entries = "".join("""
e%(k)d:
    tst.l 0x%(red)X                     | Red noted: the copy, with hero-big-art's hook
    bne L%(at)X
    cmpi.w #-1024,2(%%a5)               | (as the entry's first instruction)
    jmp 0x%(on)X
""" % {"k": k, "at": at, "red": RED_OBJ, "on": at + 6} for k, at in enumerate(ENTRIES))
    code = rom.place_code("".join("    bra.w e%d\n" % k for k in range(len(ENTRIES))) + entries + copy,
                          why="overlap test: hero-big-art's Red check only while Red is noted (a copy of the test)")
    rom.write(PAIR_SITE, GAME_PAIR, expect=bytes(rom.data[PAIR_SITE:PAIR_SITE + 8]),
              why="overlap test: the game's own box lookup back")
    for k, at in enumerate(ENTRIES):
        rom.write(at, bytes.fromhex("4EF9") + (code + 4 * k).to_bytes(4, "big"), expect=ENTRY_FIRST,
                  why="overlap test: its entry checks for Red first")
