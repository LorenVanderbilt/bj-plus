NAME = "item-text"
DESCRIPTION = "BLUE'S ITEM screens: new English item names and descriptions, a third screen, no PUSH START over them"

# The attract mode's item screens draw their English text (non-Japanese consoles; 0x10FD83 != 0) with
# `lea string,a0 ; move.w #position,d0 ; jsr 0x4DBB8` per line: an ASCII string ending in FF, drawn in the
# 2-row-tall text font from fix address 0x7000 + position (column * 32 + row). Each item's name is at column
# 11, the description at column 19 (one line on the item's row, or two lines a row above and below it), and
# between them the "..." leader - not text but a 2x2 block of fix tiles (0x582C) drawn at column 17 by
# `move.w #fixaddress,d0 ; move.w #0x582C,d1 ; jsr 0x2183A`. The descriptions end by column 34 (the box
# edge). (The "x" in SILVERx5 is part of the box artwork.)
#
# The first two screens' text calls are replaced by a call to new code drawing the new lines (so a line can be
# longer than the original string, or split in two), followed by a branch over the old calls, and the leaders'
# fix addresses are rewritten: on each screen the leader sits right after its longest name (the screens group
# names of similar length: the short ones on screen 1), the descriptions right after it.
NAME_COLUMN = 11
BOX_LAST_COLUMN = 34              # a description may not run past this column
LEADER_TILE = 0x582C
DRAW_TEXT, DRAW_LEADER = 0x4DBB8, 0x2183A
# (first old text call, end of the old text calls, leader position immediates, items)
# item = (name, row, [description lines]) - one line on the item's row, two a row above and below
SCREENS = [
    (0x35DCA, 0x35DFA, [0x35DFC, 0x35E0A, 0x35E18], [
        ("FERN", 10, ["SPEED UP"]),
        ("KEY", 16, ["UNLOCK BONUS ROOM"]),
        ("LEAF", 22, ["ATTACK UP"]),
    ]),
    (0x35EF0, 0x35F40, [0x35F50, 0x35F5E, 0x35F6C], [
        ("COCOON", 10, ["GOLD 1UP", "SILVER 5 1UP"]),
        ("NECTAR", 16, ["RESTORE 1 HEALTH"]),
        ("CLOVER", 22, ["REVEAL SHOP"]),
    ]),
]
# The clover (originally screen 1's top item) and the fern (screen 2's bottom one) swap places, icons too. Screen
# 1's icon objects are spawned from data at 0x35BFA (per icon: y, x, code, frame ... palette); screen 2 (0x35E62)
# gives them its frames and palettes and moves each 8px left (its icons are 4 tiles wide, screen 1's 3).
ICON_SWAP = [
    # (address, original bytes, new bytes, why)
    (0x35C00, "5000", "4C00", "screen 1 top icon: the fern (4 tiles wide) 8px further left"),
    (0x35C06, "348C", "3040", "screen 1 top icon: the fern (was the clover)"),
    (0x35C12, "D6", "C5", "screen 1 top icon: the fern's palette"),
    (0x35E76, "3040", "348C", "screen 2 bottom icon: the clover (was the fern)"),
    (0x35E88, "00C5", "00D6", "screen 2 bottom icon: the clover's palette"),
    (0x35E8E, "0400", "0000", "screen 2 top icon: already 8px left (the fern's place)"),
    (0x35E9A, "0400", "0000", "screen 2 bottom icon: the clover (3 tiles wide) stays put"),
]
PUSH_START_CALL = 0x35C9C         # jsr 0x35B00 in the item screens' loop: blinks PUSH START over the boxes

# A third screen, for items found in the levels that the first two don't show. The item screens run from a
# loop (0x35C60) with a countdown at 0x1078F0 set to 0x200 (0x35C6C); at 0x100 it switches to screen 2
# (0x35E62: clear the fix layer, give the three icon objects screen 2's frames / palettes / positions, draw the
# header and text). The countdown now starts at 0x300 and a hook in place of the switch shows screen 2 at 0x200
# and screen 3 at 0x100.
TIMER = 0x1078F0
TIMER_INIT = 0x35C6C              # move.w #0x200,30960(a6)
SWITCH = 0x35CA8                  # cmpi.w #0x100,30960(a6) ; bne.s +4 ; jsr 0x35E62(pc)
SCREEN2 = 0x35E62
CLEAR_FIX = 0x9FBE
HEADER_CALL = 0x35E9E             # screen 2's header call (item-header makes it a jsr to the re-spaced header)
ICON_OBJECTS = [0x104980, 0x104A00, 0x104A80]
# (name, row, [description lines], icon) - an icon is a level item's 16x16 tile, drawn 2x as big (2x2 tiles), with
# its level palette's colors (the palettes are loaded into slots the item screens don't use - only 0xD5, 0xD6,
# 0xD8, 0xF2 and 0xF3 are on screen 3; the flower got its own, 0x7D, when redrawn with both currency flowers).
SCREEN3 = [
    ("BAMBOO", 10, ["INVINCIBLE"], "bamboo"),
    ("CATFISH", 16, ["EARTHQUAKE"], "catfish"),
    ("FLOWER", 22, ["CURRENCY"], "flower"),
]
ICONS = {   # level tile, its level palette (16 colors), the palette slot it is drawn with
    "bamboo": (0x47C7, "0000 7ffb 2fd2 3eb1 4c91 5b70 2a40 a08f 003f 9e50 8e20 8b00 7ff7 fa93 6872 0000", 0x4B),
    "flower": (0x47DB, "0000 0000 0777 7ff7 fa93 6872 7f98 6f78 4e56 6ffa 5ec7 01d1 3080 0e00 4b00 7fff", 0x7D),
    "catfish": (0x502F, "0000 8000 8777 4fd0 6f90 8c60 dec7 8fa8 ef78 eff0 897f c63d c50a aa40 4720 ffff", 0x7E),
}
PALETTE_RAM = 0x400000
# Screen 1's icons (3x3 tiles) are at x 0x5000 and y 0x9000 / 0x7800 / 0x6000 (object +2 / +0, 128 per pixel,
# y up); these are 2x2, so 8px right and 8px down of that to sit centered.
ICON_X, ICON_YS = 0x5000 + 8 * 128, [0x9000 - 8 * 128, 0x7800 - 8 * 128, 0x6000 - 8 * 128]


def item_lines(items):
    """[(column, row, text)] for the names and descriptions, and the leaders' fix addresses: the leader right
    after the screen's longest name."""
    lead = NAME_COLUMN + max(len(name) for name, row, descriptions in items)
    desc_col = lead + 2
    lines, leaders = [], []
    for name, row, descriptions in items:
        lines.append((NAME_COLUMN, row, name))
        rows = [row] if len(descriptions) == 1 else [row - 1, row + 1]
        for r, text in zip(rows, descriptions):
            if desc_col + len(text) - 1 > BOX_LAST_COLUMN:
                raise SystemExit("item-text: %r runs past the box" % text)
            lines.append((desc_col, r, text))
        leaders.append(0x7000 + lead * 32 + row + 2)
    return lines, leaders


def text_source(lines, tag):
    src = "".join("    lea str%s%d(%%pc),%%a0\n    move.w #0x%X,%%d0\n    jsr 0x%X\n" % (tag, n, col * 32 + row, DRAW_TEXT)
                  for n, (col, row, text) in enumerate(lines))
    data = "".join("str%s%d:\n    .byte %s,0xFF\n" % (tag, n, ",".join("0x%02X" % ord(c) for c in text))
                   for n, (col, row, text) in enumerate(lines))
    return src, data


ART = "art/item_%s.png"       # (if there) an icon redrawn: 32x32, its own colours (up to 15 a palette slot, shared
                             # slots included; fully transparent = clear). tools/export_item_icons.py writes the
                             # starting one (the level tile drawn 2x).


def icon_art(rom, name):
    """The icon's 32x32 picture as colour words (None = clear): its ART if there, else its level tile drawn 2x."""
    import os
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, ART % name)
    tile, colors, slot = ICONS[name]
    if os.path.exists(path):
        sys.path.insert(0, os.path.join(root, "tools"))
        from png_tiles import neo_to_rgb, read_rgba, rgb_to_neo
        art = read_rgba(path)
        if len(art) != 32 or len(art[0]) != 32:
            raise SystemExit("item-text: %s must be 32x32" % (ART % name))
        known = {neo_to_rgb(int(c, 16)): int(c, 16) for c in colors.split()[1:]}   # (the level colours exactly,
        return [[None if a == 0 else known.get(rgb, rgb_to_neo(rgb)) for rgb, a in row] for row in art]  # dark bit too)
    cols = [int(c, 16) for c in colors.split()]
    src = rom.sprite_tile(tile)
    return [[None if src[y // 2][x // 2] == 0 else cols[src[y // 2][x // 2]] for x in range(32)] for y in range(32)]


def build_icons(rom):
    """{icon: (frame number, palette slot)} and {palette slot: 16 colors} for screen 3's icons."""
    slots, arts = {}, {}
    for name, (tile, colors, slot) in ICONS.items():    # merge each slot's colors: the icons' used ones
        arts[name] = icon_art(rom, name)
        pal = slots.setdefault(slot, [0x0000])
        for c in sorted({c for row in arts[name] for c in row if c is not None}):
            if c not in pal[1:]:
                pal.append(c)
        if len(pal) > 16:
            raise SystemExit("item-text: too many colors for palette 0x%X (%d, 15 at most)" % (slot, len(pal) - 1))
    frames = {}
    for name, (tile, colors, slot) in ICONS.items():
        big = [[0 if c is None else slots[slot].index(c, 1) for c in row] for row in arts[name]]
        tiles = [[rom.add_sprite_tile([r[tx * 16:tx * 16 + 16] for r in big[ty * 16:ty * 16 + 16]],
                                      why="item screen icon: %s" % name) for tx in range(2)] for ty in range(2)]
        frames[name] = (rom.add_frame(tiles, slot, why="item screen icon: %s" % name), slot)
    for slot in slots:
        slots[slot] += [0] * (16 - len(slots[slot]))
    return frames, slots


def apply(rom):
    rom.write(PUSH_START_CALL, bytes.fromhex("4E71") * 3, expect=bytes.fromhex("4EB900035B00"),
              why="item screens: no PUSH START blinking over the boxes")
    for addr, orig, new, why in ICON_SWAP:
        rom.write(addr, bytes.fromhex(new), expect=bytes.fromhex(orig), why=why)
    for first, end, leader_sites, items in SCREENS:
        lines, leaders = item_lines(items)
        src, data = text_source(lines, "")
        code = rom.place_code(src + "    rts\n" + data, why="item screen text")
        skip = end - (first + 6) - 2
        assert 0 < skip < 128
        rom.write(first, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes([0x60, skip]),
                  expect=bytes(rom.data[first:first + 8]), why="item screen: draw the new text instead")
        for site, addr in zip(leader_sites, leaders):
            if rom.u16(site - 2) != 0x303C or rom.u16(site + 2) != 0x323C:
                raise SystemExit("item-text: unexpected leader code at 0x%X" % site)
            rom.write(site, addr.to_bytes(2, "big"), expect=bytes(rom.data[site:site + 2]),
                      why="item screen: the ... leader's position")

    # ---- screen 3
    if rom.u16(HEADER_CALL) != 0x4EB9:
        raise SystemExit("item-text needs item-header (screen 2's header call should be a jsr)")
    header = rom.u32(HEADER_CALL + 2)
    frames, palettes = build_icons(rom)
    lines, leaders = item_lines([(n, r, d) for n, r, d, icon in SCREEN3])
    text, data = text_source(lines, "3_")
    src = "    jsr 0x%X\n" % CLEAR_FIX
    for slot, colors in palettes.items():
        src += "    lea 0x%X,%%a0\n" % (PALETTE_RAM + slot * 32)
        src += "".join("    move.w #0x%04X,(%%a0)+\n" % c for c in colors)
    for obj, y, (name, row, desc, icon) in zip(ICON_OBJECTS, ICON_YS, SCREEN3):
        frame, slot = frames[icon]
        src += """
    move.w #0x%(frame)X,0x%(obj_frame)X         | (the icon object: its frame, palette, x, y)
    move.b #0x%(slot)X,0x%(obj_palette)X
    move.w #0x%(x)X,0x%(obj_x)X
    move.w #0x%(y)X,0x%(obj)X
""" % {"frame": frame, "obj_frame": obj + 8, "slot": slot, "obj_palette": obj + 0x20, "x": ICON_X, "obj_x": obj + 2,
       "y": y, "obj": obj}
    src += "    jsr 0x%X\n" % header + text
    src += "".join("    move.w #0x%X,%%d0\n    move.w #0x%X,%%d1\n    jsr 0x%X\n" % (a, LEADER_TILE, DRAW_LEADER)
                   for a in leaders)
    screen3 = rom.place_code(src + "    rts\n" + data, why="item screen 3")
    switch = rom.place_code("""
    cmpi.w #0x200,0x%(timer)X
    bne 1f
    jmp 0x%(screen2)X
1:  cmpi.w #0x100,0x%(timer)X
    bne 2f
    jmp 0x%(screen3)X
2:  rts
""" % {"timer": TIMER, "screen2": SCREEN2, "screen3": screen3}, why="item screens: screen 2 at 0x200, screen 3 at 0x100")
    rom.write(TIMER_INIT, bytes.fromhex("3D7C030078F0"), expect=bytes.fromhex("3D7C020078F0"),
              why="item screens: a third screen's worth longer")
    rom.write(SWITCH, bytes.fromhex("4EB9") + switch.to_bytes(4, "big") + bytes.fromhex("4E71") * 3,
              expect=bytes.fromhex("0C6E010078F066044EBA01B0"), why="item screens: switch to screen 2 or 3")
