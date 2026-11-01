NAME = "exclaim-longer"
DESCRIPTION = "Enemies' exclaim as they spot Blue (the dinosaurs' red mark, the armadillo's ! bubble) held longer"

# Enemy actions are scripts of (frame, hold) word pairs ending in 0xFFFF. 0x17CF6 steps through them, writing the
# frame to the object's +8 and the hold to +0x4006; each frame shows for hold + 1 frames.
#
# When they spot Blue, the green and pink dinosaurs (0x17F1E) show the red mark 0x135C for 8 frames, pause on 0x1360
# for 10, then charge. The armadillo (0x1835E) shows its ! bubble 0x1C50 for 18 frames. Both marks now stay up for
# about half a second.
EXCLAIMS = [   # (hold address, frame, old hold, new hold)
    (0x17F24, 0x135C, 6, 18),    # dinosaurs' red mark: 20 frames, was 8
    (0x18368, 0x1C50, 6, 18),    # armadillo's ! bubble: 30 frames, was 18
]


def apply(rom):
    for at, frame, old, new in EXCLAIMS:
        assert rom.u16(at - 2) == frame, hex(at)
        rom.write(at, new.to_bytes(2, "big"), expect=old.to_bytes(2, "big"),
                  why="exclaim: frame 0x%X held %d frames (was %d)" % (frame, new + 1, old + 1))
