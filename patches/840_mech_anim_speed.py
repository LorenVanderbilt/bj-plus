NAME = "mech-anim-speed"
DESCRIPTION = "Mechanical City: the hardware tile animation (conveyor belts, wheels) runs faster there - smoother belts"

# anim-speed sets the hardware tile animation clock each vblank (its FRAMES_PER_STEP: 9 - calmer waterfalls), which
# made Mechanical City's conveyor belts and their wheels (about 40 auto-animated tiles, 4 frames each) step jerkily.
# More frames would need ~160-320 free sprite tiles; instead the clock runs at FAST frames a step in STAGES. The
# clock is one for the whole screen, so the stages' other animated tiles (lights, machinery) run faster too.
# anim-speed's `or.w #<speed>,d0 ; move.w d0,0x3C0006` (CLOCK_WRITE, found by its bytes) calls ours instead -
# the same size, so its code doesn't move.
STAGES = (16, 17, 18, 19)      # Mechanical City 1-4
FAST = 5                       # frames a step there (anim-speed's elsewhere)
STAGE = 0x103005


def apply(rom):
    anim_speed = rom.other_patch("anim-speed")
    normal = (anim_speed.FRAMES_PER_STEP - 1) << 8
    clock_write = bytes.fromhex("0040%04X33C0003C0006" % normal)
    at = bytes(rom.data).find(bytes.fromhex("3039001002C2024000FF") + clock_write)
    assert at > 0, "anim-speed's clock write not found"
    at += 10
    code = rom.place_code("""
    move.b 0x%(stage)X,-(%%sp)
    cmpi.b #%(first)d,(%%sp)
    bcs 1f
    cmpi.b #%(last)d,(%%sp)
    bhi 1f
    or.w #0x%(fast)04X,%%d0
    bra 2f
1:  or.w #0x%(normal)04X,%%d0
2:  addq.l #2,%%sp
    move.w %%d0,0x3C0006
    rts
""" % {"stage": STAGE, "first": STAGES[0], "last": STAGES[-1], "fast": (FAST - 1) << 8, "normal": normal},
        why="the animation clock: faster in Mechanical City")
    rom.write(at, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E714E71"), expect=clock_write,
              why="anim-speed's clock write: by stage")
