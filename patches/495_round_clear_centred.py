NAME = "round-clear-centred"
DESCRIPTION = "ROUND CLEAR and its bonus lines centred: one column (8 pixels) right"

# The two ROUND CLEAR routines (after the goal and after a boss) draw everything one column left of centre: the big
# letters span pixels 64-240, centred on 152 rather than the screen's 160, and the bonus lines are off the same way.
# Every position moves one fix column right (+0x20 in a fix address):
#   letters: move.w #<offset>,d0 ; move.w #<tile>,d1 (fix address = offset + 0x7002; 0x104 is column 8)
#   bonus line text: jsr 0x9FE6 (the inline printer) ; dc.w <fix address> ; the string
#   bonus numbers: move.w #<fix address>,d0, then moveq #4,d1 for 4 digits
# hud, which runs later, takes over each routine's first two moves and replays them from the values set here.
ROUTINES = [(0x54CD0, 0x54FD6), (0x54FD8, 0x551AC)]   # first instruction, its rts
COUNTS = {"letters": 20, "lines": 7, "numbers": 6}
COLUMN = 0x20


def apply(rom):
    found = {"letters": [], "lines": [], "numbers": []}
    for start, end in ROUTINES:
        for at in range(start, end, 2):
            op, value = rom.u16(at), rom.u16(at + 2)
            if op == 0x303C and rom.u16(at + 4) == 0x323C and value < 0x400:
                found["letters"].append(at + 2)
            elif op == 0x4EB9 and rom.u32(at + 2) == 0x9FE6 and 0x7000 <= rom.u16(at + 6) < 0x7500:
                found["lines"].append(at + 6)
            elif op == 0x303C and 0x7000 <= value < 0x7500 and rom.u16(at + 4) == 0x7204:
                found["numbers"].append(at + 2)
    assert {k: len(v) for k, v in found.items()} == COUNTS, found
    for kind, places in found.items():
        for at in places:
            old = rom.u16(at)
            rom.write(at, (old + COLUMN).to_bytes(2, "big"), expect=old.to_bytes(2, "big"),
                      why="ROUND CLEAR centred: %s" % kind[:-1])
