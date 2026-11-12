NAME = "ride-grid-start"
DESCRIPTION = "Travel agent's ride: no garbled colours on its first two frames (the grid's palettes start dark)"

# ride-grid paints the squares' palettes (its PALETTES, N per set) from the ride's loop (its RIDE_CALL). But the ride
# shows its layers two frames before that: the set-up waits a frame (SETUP_WAIT) and so does the top of the loop.
# Those two frames showed the back layer's tiles in whatever the palettes held (the level's colours): multicoloured
# garbage across the screen (2026-11-10, seen in the ride_grid clip).
#
# Right after the set-up's wait (in the vblank, so no streaks on real hardware - see palette-timing) every one of
# those palettes' colours is set to the floor's dark (ride-grid's DARK in its palette 0x88), the colour of a square
# nobody has lit, so the ride opens on a plain dark floor until the first step.
SETUP_WAIT = 0x2785E         # jsr 0xE856: the set-up's frame wait, before the loop
WAIT = 0xE856


def apply(rom):
    grid = rom.other_patch("ride-grid")
    palettes = grid.N * len(grid.SETS)
    code = rom.place_code("""
    jsr 0x%(wait)X                      | (the vblank: the colours are written before the picture)
    movem.l %%d0-%%d1/%%a0,-(%%sp)
    lea 0x%(pal0)X,%%a0
    move.w 0x%(dark)X,%%d0
    move.w #%(count)d,%%d1
0:  move.w %%d0,(%%a0)+
    dbra %%d1,0b
    movem.l (%%sp)+,%%d0-%%d1/%%a0
    rts
""" % {"pal0": 0x400000 + grid.PALETTES * 32, "dark": 0x400000 + grid.PAL88 * 32 + grid.DARK * 2,
       "count": palettes * 16 - 1, "wait": WAIT}, why="the ride's set-up: its grid's palettes dark")
    rom.write(SETUP_WAIT, bytes.fromhex("4EB9") + code.to_bytes(4, "big"), expect=bytes.fromhex("4EB90000E856"),
              why="the ride's set-up: the grid's palettes dark before it shows")
