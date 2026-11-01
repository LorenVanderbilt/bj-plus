NAME = "default-name-blu-table"
DESCRIPTION = "High score name entry typed into the table (after the ending): a name left as ... goes in as BLU too"

# default-name-blu turns a name left as ':::' (drawn as ...) into BLU when the entry is copied into TODAY'S BEST.
# The name entry after the ending (0x5491E, ENTRIES) works differently: it inserts the row first, then has the name
# typed straight into it at TABLE + 16 * rank. So after each of those, a row still holding ':::' gets ' BLU', a
# space and three letters like the table's other names.
ENTRIES = [(0x54934, 0x4E248, 0x1030DC), (0x5494A, 0x4E2D4, 0x1030DD)]   # jsr, its routine, the player's rank
TABLE = 0x103384               # the first row's name; rows are 16 bytes apart
DEFAULT = 0x3A3A3A


def apply(rom):
    for n, (at, routine, rank) in enumerate(ENTRIES):
        assert rom.u16(at) == 0x4EB9 and rom.u32(at + 2) == routine
        code = rom.place_code("""
    jsr 0x%(routine)X
    movem.l %%d0-%%d1/%%a0,-(%%sp)
    moveq #0,%%d0
    move.b 0x%(rank)X,%%d0
    lsl.w #4,%%d0
    lea 0x%(table)X,%%a0
    adda.w %%d0,%%a0
    move.l (%%a0),%%d0
    move.l %%d0,%%d1
    andi.l #0xFFFFFF,%%d1
    cmpi.l #0x%(default)X,%%d1
    bne 1f
    move.l #0x20424C55,(%%a0)           | ' BLU'
1:  movem.l (%%sp)+,%%d0-%%d1/%%a0
    rts
""" % {"routine": routine, "rank": rank, "table": TABLE, "default": DEFAULT},
            why="name entry in the table: player %d's ... as BLU" % (n + 1))
        rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + routine.to_bytes(4, "big"),
                  why="high score name typed into the table: player %d's ... as BLU" % (n + 1))
