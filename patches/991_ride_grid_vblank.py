NAME = "ride-grid-vblank"
DESCRIPTION = "Travel agent's ride: the grid's squares' colours written in the vblank (they streaked on real hardware)"

# The user, 2026-11-11, on a BackBit: streaks during the ride. ride-grid repainted its squares' palettes (45 of
# them, every STEP frames) from the ride's loop, on picture lines ~29-123 (tools/palette_timing.py), and on the real
# Neo Geo a colour written while a line is drawn shows as a short streak (see palette-timing). Working the colours out
# takes far longer than the vblank, so ride-grid now leaves them in its BUFFER with its pending byte set, and here,
# right after the ride loop's frame wait (LOOP_WAIT: the vblank has just begun), they're block-copied into palette
# RAM: 1440 bytes, ~9 lines. (A check in the vblank interrupt instead cost every frame of the game a few cycles,
# enough to make busy frames in other places run over - the wheel_gondolas clip went out of step.)
LOOP_WAIT = 0x2787E          # jsr 0xE856: the ride loop's frame wait
WAIT = 0xE856


def apply(rom):
    grid = rom.other_patch("ride-grid")
    size = grid.N * len(grid.SETS) * 32
    assert size % 48 == 0
    code = rom.place_code("""
    jsr 0x%(wait)X
    tst.b 0x%(pending)X
    beq 9f
    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)
    lea 0x%(buffer)X,%%a0
    lea 0x%(pal0)X,%%a1
    move.w #%(blocks)d,%%d7
1:  movem.l (%%a0)+,%%d0-%%d6/%%a2-%%a6
    movem.l %%d0-%%d6/%%a2-%%a6,(%%a1)
    lea 48(%%a1),%%a1
    dbf %%d7,1b
    clr.b 0x%(pending)X
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6
9:  rts
""" % {"wait": WAIT, "pending": grid.RAM + 1, "buffer": grid.BUFFER, "pal0": 0x400000 + grid.PALETTES * 32,
       "blocks": size // 48 - 1}, why="the ride's squares' colours, in the vblank")
    rom.write(LOOP_WAIT, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("4EB90000E856"),
              why="the ride's loop, after its frame wait: the squares' colours")
