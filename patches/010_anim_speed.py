NAME = "anim-speed"
DESCRIPTION = "Slow the hardware tile animation (waterfalls etc.) by setting the LSPC animation clock"

# How many video frames each hardware-animated tile stays on screen before advancing.
# The game never sets this itself, so it runs at the BIOS default of 5 (12 steps/second).
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
    hook = rom.place_code(
        "    move.w #0x%04X,0x3C0006\n    jmp 0x%X\n" % ((FRAMES_PER_STEP - 1) << 8, original_vblank),
        why="sets the animation clock every frame, then continues to the original VBlank handler")
    rom.write(0x64, hook.to_bytes(4, "big"), expect=original_vblank.to_bytes(4, "big"),
              why="VBlank vector now goes through the hook")
