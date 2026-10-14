NAME = "round-clear-centred"
DESCRIPTION = "ROUND CLEAR and its bonus lines centred: one column (8 pixels) right"

# ROUND CLEAR's two routines (ROUTINES: after the goal, after a boss) draw everything a column left of centre - the
# big letters span pixels 64-240 (middle 152, the screen's 160), the bonus lines likewise. Each position moves one
# fix column (+0x20 in a fix address):
#   the letters: move.w #<offset>,d0 ; move.w #<tile>,d1 (offset +0x7002 = the fix address; 0x104 = column 8)
#   the bonus lines' text: jsr 0x9FE6 (the inline printer) ; dc.w <fix address> ; the string
#   their numbers: move.w #<fix address>,d0 (then moveq #4,d1 - 4 digits)
# The HUD's (`hud`, after this) takes over each routine's first two moves and replays them, from what's here.
ROUTINES = [(0x54CD0, 0x54FD6), (0x54FD8, 0x551AC)]   # (first instruction, its rts)
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
