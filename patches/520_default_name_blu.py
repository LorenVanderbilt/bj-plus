NAME = "default-name-blu"
DESCRIPTION = "High score name entry: a name left as ... (the three default characters) goes in the table as BLU"

# The high score name entry (0x4E0EA, per player, started at 0x1217C / 0x127D2) begins at ':::' in bytes 1-3 of the
# long at player block +0x160. ':' is drawn as '.'. Each character steps through 0-9, a few symbols, A-Z and space.
# The table insert (0x5413A) copies that long into the new entry (INSERTS). A name still at ':::' now goes in as
# BLU, keeping the first byte.
INSERTS = [(0x54148, 0x7160, 0x30CA), (0x5417E, 0x7560, 0x30D4)]   # site, the player's name, the entry's
DEFAULT = 0x3A3A3A


def apply(rom):
    for n, (at, name, entry) in enumerate(INSERTS):
        code = rom.place_code("""
    move.l 0x%(name)X(%%a6),%%d0
    move.l %%d0,%%d1
    andi.l #0xFFFFFF,%%d1
    cmpi.l #0x%(default)X,%%d1
    bne 1f
    andi.l #0xFF000000,%%d0
    ori.l #0x424C55,%%d0                | BLU
1:  move.l %%d0,0x%(entry)X(%%a6)
    rts
""" % {"name": name, "entry": entry, "default": DEFAULT}, why="name entry: player %d's ... as BLU" % (n + 1))
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
                  expect=bytes.fromhex("2D6E") + name.to_bytes(2, "big") + entry.to_bytes(2, "big"),
                  why="high score table: player %d's name, ... as BLU" % (n + 1))
