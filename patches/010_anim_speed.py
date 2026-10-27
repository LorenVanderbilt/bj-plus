NAME = "anim-speed"
DESCRIPTION = "Slow the hardware tile animation (waterfalls etc.) by setting the LSPC animation clock"

# How many video frames each hardware-animated tile stays on screen before advancing.
# The game sets it per stage (a table at 0x1516E: 5 frames - 12 steps/second - nearly everywhere; Jungle Zone 2's
# has the animation off, a mode bit kept below).
# Bigger = slower: 8 = 7.5 steps/sec, 10 = 6 steps/sec, 12 = 5 steps/sec. (Max 256.)
FRAMES_PER_STEP = 9


def apply(rom):
    # Setting this once at startup (hooking the cartridge's USER entry at 0x122) does NOT stick:
    # the animation stays at the default 5 frames, so something re-sets the register after the
    # game starts (not tracked down). Setting it every frame does work, so instead:
    # the game's vertical-blank interrupt handler (vector at 0x64) runs once per frame. Point
    # the vector at a small routine that sets the animation clock (LSPC mode register 0x3C0006,
    # high byte = frames per step - 1) and then carries on to the original handler.
    original_vblank = rom.u32(0x64)
    # The game keeps its own copy of the register at 0x1002C2 and sets bit 3 in it (auto-animation
    # off) while paused, so keep everything except the speed byte from that copy.
    hook = rom.place_code("""
    move.l %%d0,-(%%sp)
    move.w 0x1002C2,%%d0                | (the game's copy of the LSPC mode: its other bits kept)
    and.w #0x00FF,%%d0
    or.w #0x%(timer)04X,%%d0            | the animation clock: FRAMES_PER_STEP
    move.w %%d0,0x3C0006
    move.l (%%sp)+,%%d0
    jmp 0x%(vblank)X
""" % {"timer": (FRAMES_PER_STEP - 1) << 8, "vblank": original_vblank},
        why="sets the animation clock every frame (keeping the game's other mode bits), then continues to the original VBlank handler")
    rom.write(0x64, hook.to_bytes(4, "big"), expect=original_vblank.to_bytes(4, "big"),
              why="VBlank vector now goes through the hook")
