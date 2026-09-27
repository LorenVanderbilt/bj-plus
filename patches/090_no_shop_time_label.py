NAME = "no-shop-time-label"
DESCRIPTION = "Blank the leftover \"TIME\" plate above the shop's item grid (the countdown itself is removed by no-shop-timer)"

# The shop's gold frame and its "TIME" plate are part of the background tile map, drawn into the full-height
# background sprite strips by the map decoder (0xCE6A / 0xCF16). The map is run-length encoded: a byte
# 0x80|(n-1) starts a literal run of n tiles, followed by the attribute word (0x8410 here), the tile number's
# high byte (0x52) and then one low byte per tile. Row 10 of the shop map is one such run at 0xABDC7:
#   da b1 b2 [b3 b4 b5 b6] b7 dc c1   -> ... scroll, plate left end, T, I, M, E, plain plate, ...
# (tiles 0x52B3-0x52B6 spell TIME; 0x52B7 is the plain striped middle of the plate). Found by catching the
# VRAM writes of those tiles in MAME and reading the decoder's source pointer (a2, already one past the byte).
# The four letters become plain plate tiles, leaving an empty plate where the countdown used to be.
TIME_LETTERS = 0xABDCE


def apply(rom):
    rom.write(TIME_LETTERS, bytes([0xB7] * 4), expect=bytes.fromhex("B3B4B5B6"),
              why="shop plate: T I M E -> plain plate tiles")
