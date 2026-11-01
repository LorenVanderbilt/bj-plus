NAME = "shop-prices"
DESCRIPTION = "Shop: the prices charged match the prices shown (the original's data disagreed in shops 1-3)"

# Each shop (0x1078F6, 0-3) has a table of buying routines at 0x1FF90, one per cell. Each routine charges its own
# price (move.b #N,d0), doubled when the player's prices are doubled (player +0x1E). The descriptions shown come from
# separate tables at 0x20EF4, eight cells per shop, normal then doubled. In the original some of them disagree
# (sta/aes/shop_flippers.sta is in shop 1):
#   * Flippers, shops 1 and 2: shown as 15 (30), charged 25 (50). They now charge 15 (30) using 0x2038A, a
#     15-flower routine no shop used.
#   * Ice shoes, shops 1-3: shown as 75 (150), charged 70 (140). They're now shown as 70 (140); text-fixes leaves
#     the price line alone.
#   * Light safe, shop 1: shown as 25 (50), charged 20 (40). It now uses the 20 (40) description from shops 0, 2, 3.
# shop-sold-out-first also refers to the 15-flower flippers routine.
FLIPPERS_15 = 0x2038A
FLIPPERS_CELLS = [0x1FFCC + 2 * 4, 0x1FFF8 + 2 * 4]          # shops 1 and 2, cell 2 (was 0x20390, 25 flowers)
ICE_SHOE_PRICES = [(0x2118C, b"75", b"70"), (0x2138A, b"150", b"140")]   # (text, old price, new)
SAFE_DESCRIPTIONS = [(0x20F44, 0x211DA, 0x211B0), (0x20F64, 0x213D8, 0x213AE)]   # table entry, 25 / 50 text, 20 / 40 text


def apply(rom):
    for at in FLIPPERS_CELLS:
        rom.write(at, FLIPPERS_15.to_bytes(4, "big"), expect=(0x20390).to_bytes(4, "big"),
                  why="shop: flippers charged the 15 flowers shown")
    for text, old, new in ICE_SHOE_PRICES:
        at = text + rom.data[text:text + 16].index(b"\xfe") + 1
        rom.write(at, new, expect=old, why="shop: ice shoes shown at the price charged")
    for at, old, new in SAFE_DESCRIPTIONS:
        rom.write(at, new.to_bytes(4, "big"), expect=old.to_bytes(4, "big"),
                  why="shop 1: light safe shown at the price charged")
