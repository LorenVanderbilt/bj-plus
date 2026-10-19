NAME = "zipline-faster"
DESCRIPTION = "The zipline (the only one, in the ice world) carries Blue along its rope faster"

# The zipline's handle (object code 0x50584) follows a fixed path: each frame it keeps its place (+0 / +2 into +0x48),
# calls the path routine (PATH_CALL: jsr 0x19EEE, with its tables in a0 / a1 - a step a frame, minus when the path is
# over) and then moves itself and its rider by the difference. Now the path is stepped again on every EVERY-th frame:
# the same route, 1 + 1 / EVERY times as fast (2: half as fast again; 1: twice). The rider and the camera follow the
# handle, so they keep up. (Its own patch, last, so its code moves nothing.)
PATH_CALL = 0x50592            # jsr 0x19EEE
PATH = 0x19EEE
TABLES = (0x50726, 0x50762)    # (lea'd into a0 / a1 just before the call)
EVERY = 2
STEPS = 0x10EA81               # a byte (spare RAM): frames since the last extra step


def apply(rom):
    assert rom.u16(PATH_CALL) == 0x4EB9 and rom.u32(PATH_CALL + 2) == PATH
    code = rom.place_code("""
    addq.b #1,0x%(steps)X               | every EVERY-th frame, an extra step first
    cmpi.b #%(every)d,0x%(steps)X
    bcs 1f
    clr.b 0x%(steps)X
    jsr 0x%(path)X
    bmi 9f                              | (the path's over)
    lea 0x%(a0)X,%%a0                   | (its tables again, for the usual step)
    lea 0x%(a1)X,%%a1
1:  jmp 0x%(path)X                      | the usual step - its flags go back to the handle (minus: over)
9:  rts
""" % {"path": PATH, "steps": STEPS, "every": EVERY, "a0": TABLES[0], "a1": TABLES[1]},
        why="zipline: its path stepped faster")
    rom.write(PATH_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + PATH.to_bytes(4, "big"), why="zipline: faster along its rope")
