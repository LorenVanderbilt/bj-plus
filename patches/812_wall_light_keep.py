NAME = "wall-light-keep"
DESCRIPTION = "Daruma Empire 1's yellow wall light: its colours kept after a continue (they went missing)"

# wall-light's palette (its LIGHT_PAL, empty in the stage) is written only as its tile is drawn, so when the level's
# palettes load after that (a continue there: the wall on screen as the level's built) the light was left without
# colours. Now they're put there each frame in its stage, at the vblank wait (FRAME_LOOP, round-clear-dim's hook
# there - tunnel-life-ball's first: ours before both) - not while the screen's black (screen-blackout) or dimmed
# (round-clear-dim).
FRAME_LOOP = 0xE8AC             # jmp <tunnel-life-ball's frame> - the vblank wait's loop, once a frame


def apply(rom):
    light, blackout, dim = (rom.other_patch("wall-light"), rom.other_patch("screen-blackout"),
                            rom.other_patch("round-clear-dim"))
    assert len(light.COLOURS) == 16
    assert rom.u16(FRAME_LOOP) == 0x4EF9, "wall-light-keep: needs round-clear-dim's hook at the vblank wait"
    next_frame = rom.u32(FRAME_LOOP + 2)
    code = rom.place_code("""
| the vblank wait's loop, a frame over (d1-a5 free): in the stage, the light's colours kept - then on
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
