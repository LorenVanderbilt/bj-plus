NAME = "wall-light-keep"
DESCRIPTION = "Daruma Empire 1's yellow wall light: its colours kept after a continue (they went missing)"

# wall-light writes its palette (LIGHT_PAL, unused in the stage) only when its tile is drawn. After a continue the
# wall is already on screen when the level's palettes load, so the light lost its colours.
#
# The colours are now copied in every frame in that stage from the vblank wait (FRAME_LOOP), chained ahead of
# tunnel-life-ball and round-clear-dim, except while the screen is blacked out or dimmed.
FRAME_LOOP = 0xE8AC             # jmp <tunnel-life-ball> in the vblank wait loop


def apply(rom):
    light, blackout, dim = (rom.other_patch("wall-light"), rom.other_patch("screen-blackout"),
                            rom.other_patch("round-clear-dim"))
    assert len(light.COLOURS) == 16
    assert rom.u16(FRAME_LOOP) == 0x4EF9, "wall-light-keep: needs round-clear-dim's hook at the vblank wait"
    next_frame = rom.u32(FRAME_LOOP + 2)
    code = rom.place_code("""
| once a frame (d1-a5 free): refresh the light's colours in its stage, then chain on
    cmpi.b #%(light_stage)d,0x%(stage)X
    bne 0f
    tst.b 0x%(black)X
    bne 0f
    tst.b 0x%(dimmed)X
    bne 0f
    lea colours(%%pc),%%a0
    lea 0x%(pal)X,%%a1
    moveq #7,%%d1
1:  move.l (%%a0)+,(%%a1)+
    dbf %%d1,1b
0:  jmp 0x%(next)X
colours:
    .word %(colours)s
""" % {"light_stage": light.LIGHT_STAGE, "stage": light.STAGE, "black": blackout.BLACK, "dimmed": dim.ACTIVE,
       "pal": 0x400000 + light.LIGHT_PAL * 32, "colours": ",".join("0x%04X" % c for c in light.COLOURS),
       "next": next_frame},
        why="wall-light: its colours kept")
    rom.write(FRAME_LOOP + 2, code.to_bytes(4, "big"), expect=next_frame.to_bytes(4, "big"),
              why="vblank wait, each frame: the wall light's colours first")
