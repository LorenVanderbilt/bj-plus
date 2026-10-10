NAME = "shop-prices"
DESCRIPTION = "Shop: the prices charged match the prices shown (the original's data disagreed in shops 1-3)"

# Each shop (0x1078F6: 0-3) has a table of buying routines, one a cell (0x1FF90), each routine charging its own
# price (`move.b #N,d0`, doubled when prices are doubled - player +0x1E); the descriptions shown - name / price /
# lines - come from other tables, eight of eight cells (0x20EF4: shop 0-3, each normal then doubled). In the
# original they disagree (sta/aes/shop_flippers.sta, shop 1):
#   * flippers, shops 1 and 2: shown 15 (30), charged 25 (50) - now charged 15 (30), by the 15-flower routine
#     0x2038A that no shop used;
#   * ice shoes, shops 1-3: shown 75 (150), charged 70 (140) - now shown 70 (140) (text-fixes keeps the price line);
#   * light safe, shop 1: shown 25 (50), charged 20 (40) - now shown with shops 0 / 2 / 3's 20 (40) description.
# shop-sold-out-first names the 15-flower flippers routine too.
FLIPPERS_15 = 0x2038A
FLIPPERS_CELLS = [0x1FFCC + 2 * 4, 0x1FFF8 + 2 * 4]          # shops 1, 2: cell 2 (was 0x20390, 25 flowers)
ICE_SHOE_PRICES = [(0x2118C, b"75", b"70"), (0x2138A, b"150", b"140")]   # (text, old price, new)
SAFE_DESCRIPTIONS = [(0x20F44, 0x211DA, 0x211B0), (0x20F64, 0x213D8, 0x213AE)]   # (table entry, 25 / 50, 20 / 40)


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
