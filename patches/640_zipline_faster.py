NAME = "zipline-faster"
DESCRIPTION = "Strange Space 3's zipline (the game's only one) carries Blue along its rope faster"

# The zipline's handle (object 0x50584) follows a fixed path. Each frame it saves its position (+0 / +2 into +0x48),
# calls the path routine (PATH_CALL, with its tables in a0 / a1), which takes one step and returns minus when the
# path is over, and then moves itself and its rider by the difference. The path now takes an extra step every
# EVERY-th frame: the same route at 1 + 1 / EVERY times the speed (2 is half as fast again, 1 is twice as fast). The
# rider and the camera follow the handle, so they keep up.
PATH_CALL = 0x50592            # jsr 0x19EEE
PATH = 0x19EEE
TABLES = (0x50726, 0x50762)    # loaded into a0 / a1 just before the call
EVERY = 2
STEPS = 0x10EA81               # spare RAM byte: frames since the last extra step


def apply(rom):
    assert rom.u16(PATH_CALL) == 0x4EB9 and rom.u32(PATH_CALL + 2) == PATH
    code = rom.place_code("""
    addq.b #1,0x%(steps)X               | every EVERY-th frame, an extra step first
    cmpi.b #%(every)d,0x%(steps)X
    bcs 1f
    clr.b 0x%(steps)X
    jsr 0x%(path)X
    bmi 9f                              | the path is over
    lea 0x%(a0)X,%%a0                   | its tables again, for the usual step
    lea 0x%(a1)X,%%a1
1:  jmp 0x%(path)X                      | the usual step; its flags go back to the handle (minus: over)
9:  rts
""" % {"path": PATH, "steps": STEPS, "every": EVERY, "a0": TABLES[0], "a1": TABLES[1]},
        why="zipline: its path stepped faster")
    rom.write(PATH_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + PATH.to_bytes(4, "big"), why="zipline: faster along its rope")
