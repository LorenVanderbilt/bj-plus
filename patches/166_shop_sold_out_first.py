NAME = "shop-sold-out-first"
DESCRIPTION = "Shop: an item you can't have anyway (already have it, not cursed) gets that answer, not CAN'T AFFORD"

# Each item's buying routine checks the price first and only then whether you can have the item at all. Too few
# flowers goes to the can't-afford lines at 0x2008C, a different line each try, with the fourth sending you off.
# Already having the item goes to 0x203FC (SORRY, SOLD OUT! in text-fixes), and the magic wand without a curse goes
# to 0x2063E (YOU'RE NOT CURSED). So with too few flowers for something you already had, she said you couldn't
# afford it.
#
# The can't-afford routine now first finds the routine of the item under the cursor, from the shop's table at
# 0x1FF90 (indexed by shop, 0x1078F6, and cell, shop object +0x4040). If it's one of BLOCKED and the player data
# (a4) rules it out, that answer is given instead. Nectar already checks for full hearts before the price, and the
# gold cocoon has no limit.
CANT_AFFORD = 0x2008C        # move.w 0x4044(a5),d0 ; jsr 0x214AC (pc-relative), then 0x20094
SHOP_TABLES = 0x1FF90
SHOP = 0x78F6                # word at (a6): which shop
CELL = 0x4040                # byte at (a5): the cell under the cursor
SOLD_OUT, NOT_CURSED = 0x203FC, 0x2063E
BLOCKED = [   # (item routines, player byte, refused when "set" = nonzero / "two" = 2 / "clear" = 0, answer)
    ((0x2038A, 0x20390, 0x20396), 0x15, "set", SOLD_OUT),   # flippers
    ((0x20458, 0x2045E), 0x13, "set", SOLD_OUT),      # ice shoes (spike)
    ((0x204C8,), 0x18, "set", SOLD_OUT),              # light safe (either safe)
    ((0x20550,), 0x18, "two", SOLD_OUT),              # super safe
    ((0x205BE,), 0x19, "clear", NOT_CURSED),          # magic wand (only when cursed)
    ((0x2069E, 0x206A6), 0x14, "set", SOLD_OUT),      # fern (spring)
    ((0x2070C,), 0x2A, "set", SOLD_OUT),              # ocarina
]


def apply(rom):
    checks = "".join("    cmp.l #0x%X,%%a0\n    beq item%d\n" % (r, i)
                     for i, (routines, _, _, _) in enumerate(BLOCKED) for r in routines)
    items = ""
    for i, (routines, flag, when, answer) in enumerate(BLOCKED):
        test = {"set": "    tst.b 0x%X(%%a4)\n    bne no%d\n",
                "two": "    cmpi.b #2,0x%X(%%a4)\n    beq no%d\n",
                "clear": "    tst.b 0x%X(%%a4)\n    beq no%d\n"}[when] % (flag, i)
        items += "item%d:\n%s    bra afford\nno%d:\n    jmp 0x%X\n" % (i, test, i, answer)
    code = rom.place_code(r"""
    lea 0x%(tables)X,%%a0               | the routine of the item under the cursor
    move.w 0x%(shop)X(%%a6),%%d0
    lsl.w #2,%%d0
    movea.l (%%a0,%%d0.w),%%a0
    moveq #0,%%d0
    move.b 0x%(cell)X(%%a5),%%d0
    lsl.w #2,%%d0
    movea.l (%%a0,%%d0.w),%%a0
%(checks)s    bra afford
%(items)s
afford:                                 | as before: the can't-afford lines
    move.w 0x4044(%%a5),%%d0
    jsr 0x214AC
    jmp 0x%(back)X
""" % {"tables": SHOP_TABLES, "shop": SHOP, "cell": CELL, "checks": checks, "items": items, "back": CANT_AFFORD + 8},
        why="shop: SOLD OUT (or NOT CURSED) before CAN'T AFFORD")
    rom.write(CANT_AFFORD, bytes.fromhex("4EF9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("302D40444EBA141A"), why="shop: can't afford -> first, may he have it at all?")
