NAME = "exclaim-longer"
DESCRIPTION = "Enemies' exclaim as they spot Blue (the dinosaurs' red mark, the armadillo's ! bubble) held longer"

# An enemy's actions play as scripts of (frame, hold) word pairs, ended by 0xFFFF (0x17CF6 steps them: the frame goes
# to the object's +8, the hold's low byte to its +0x4006 - the frame shows hold + 1 frames). Spotting Blue:
#   the dinosaurs (green and pink; 0x17F1E): the red mark 0x135C (0, 6: 8 frames), a pause 0x1360 (6, 2: 10), the charge
#   the armadillo (0x1835E): the ! bubble 0x1C50 (0, 6, 6, 2: 18 frames) - its whole pause
# Each now waits ~1/2 s before it moves on. EXCLAIMS: (the hold's address, its frame, the hold it had, the hold now).
EXCLAIMS = [
    (0x17F24, 0x135C, 6, 18),    # dinosaurs: the red mark 20 frames (was 8), then the 10-frame pause
    (0x18368, 0x1C50, 6, 18),    # armadillo: the ! bubble 30 frames (was 18)
]


def apply(rom):
    for at, frame, old, new in EXCLAIMS:
        assert rom.u16(at - 2) == frame, hex(at)
        rom.write(at, new.to_bytes(2, "big"), expect=old.to_bytes(2, "big"),
                  why="exclaim: frame 0x%X held %d frames (was %d)" % (frame, new + 1, old + 1))
