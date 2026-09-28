NAME = "shop-title"
DESCRIPTION = "Fairy shop: \"SHOP\" on the plate at the top (where the countdown used to be), in the BLUE'S ITEM font"

# The plate above the fairy shop's item grid used to say TIME with the countdown under it; no-shop-timer and
# no-shop-time-label left it blank. It sits at screen x 32-159, y 0-15 (fix columns 4-19, rows 2-3).
#
# The "BLUE'S ITEM" header of the attract item screens is fix-layer text in palette 5 (the grey/white text
# palette) from a 16x16 font in the S ROM: each letter is 2x2 tiles, tile n / n+1 on top and n+0x10 / n+0x11
# below, eight letters per band of 0x20 tiles starting at 0x900 (A = 0x902 ... G = 0x90E, H = 0x920 ...,
# P = 0x940 ...). "SHOP" (64 pixels) is drawn centered on the plate, columns 8-15.
#
# It is drawn during the shop's set-up, before the fade-in, at the spot where the countdown digits used to be
# drawn: `move.w #0x71C2,d0` (their position) followed by the call no-shop-timer turned into NOPs - so this
# needs no-shop-timer (the digits would land on the same spot anyway).
SITE = 0x1F7F0                    # move.w #0x71C2,d0 ; nop ; nop
LETTERS = {"S": 0x946, "H": 0x920, "O": 0x92E, "P": 0x940}
TEXT, COLUMN, ROW, PALETTE = "SHOP", 8, 2, 5


def apply(rom):
    writes = ""
    for i, ch in enumerate(TEXT):
        top = LETTERS[ch]
        for dx, dy, tile in ((0, 0, top), (1, 0, top + 1), (0, 1, top + 0x10), (1, 1, top + 0x11)):
            addr = 0x7000 + (COLUMN + 2 * i + dx) * 32 + ROW + dy
            writes += "    move.w #0x%04X,0x3C0000\n    move.w #0x%04X,0x3C0002\n" % (addr, PALETTE << 12 | tile)
    code = rom.place_code(
        "    move.w %%sr,-(%%sp)\n"
        "    or.w #0x0700,%%sr\n"
        "%s"
        "    move.w (%%sp)+,%%sr\n"
        "    rts\n" % writes,
        why="shop title SHOP on the top plate")
    if bytes(rom.data[SITE:SITE + 8]) != bytes.fromhex("303C71C24E714E71"):
        raise SystemExit("shop-title needs no-shop-timer (the countdown digit call at 0x1F7F4 must be gone)")
    rom.write(SITE, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("303C71C24E714E71"), why="shop set-up: draw SHOP where the countdown was")
