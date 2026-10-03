NAME = "no-idle-go"
DESCRIPTION = "Home console (AES): no flashing GO sign after standing idle (the hero's own idle animation is enough)"

# The idle routine at 0x11888 (see no-idle-bird) spawns a blinking hint object at 960 idle frames:
# `cmpi.w #960,d0 ; beq.s 0x118F8` (the spawn) else `bra 0x11988` (skip). The sign is "GO" with a right
# arrow (frame 0x2D30), or a bigger "GO" with no arrow (0x2D1C) on stages where the way on isn't right.
# The compare and branch now go through a check: on the AES (system-mode byte 0x10FD82 is 0; the arcade
# sets bit 7) the spawn is skipped. The arcade keeps its sign.
CHECK_AT = 0x118CA      # cmpi.w #960,d0 ; beq.s 0x118F8
SPAWN = 0x118F8
SKIP = 0x11988
SYSTEM_MODE = 0x10FD82


def apply(rom):
    code = rom.place_code(
        "    cmpi.w #960,%%d0\n"
        "    bne.s 1f\n"
        "    tst.b 0x%X\n"
        "    beq.s 1f                         | home console: no GO sign\n"
        "    jmp 0x%X\n"
        "1:  jmp 0x%X\n" % (SYSTEM_MODE, SPAWN, SKIP),
        why="idle GO sign: arcade only")
    rom.write(CHECK_AT, bytes.fromhex("4EF9") + code.to_bytes(4, "big"), expect=bytes.fromhex("0C4003C06728"),
              why="idle: the 960-frame GO sign goes through the arcade-only check")
