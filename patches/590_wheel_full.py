NAME = "wheel-full"
DESCRIPTION = "The sunken wheels start full: their gondolas already all the way round when a wheel comes into play"

# A sunken wheel's gondolas come from a spawner object (0x315C0). Its first run sets its countdown (+0x4000) to 1,
# and each time the countdown runs out (every 0x40 frames after the first) it spawns a gondola through 0xA158 (inline
# data: object area 0x5380, 31 slots, the gondola's first 0x20 bytes). It points the gondola back at itself (+0x4010)
# and gives every other one the other colour (frame 0x2464 on an odd count, +0x4003).
#
# A gondola (0x3164A) sets itself up on its first run: angle 0xB8 (the word at +0x3A), radius 0x30 at +0x38, a turn
# of 0x80 a frame at +0x3E, and +0x29 to mark it done. It's removed at angle 0x60, so six ride the wheel at once, 0x20
# apart. That meant a wheel came into view empty, with nothing to jump on until the gondolas came round.
#
# The spawner's first run now also places the five older gondolas at the angles they'd have reached (OLDER), each set
# up just as the spawner and its own first run would do.
SPAWNER_FIRST = 0x315D2            # move.w #1,0x4000(a5): spawn the first one at once
SPAWN = 0xA158
SPAWN_DATA = 0x31602               # the spawner's 30 bytes of inline data: area, slots, new object fields
CLEAR_EXTRA = 0x10098              # clears a new object's +0x4000 area (a1), as the spawner does
GONDOLA = 0x3164A
OLDER = [0xD800, 0xF800, 0x1800, 0x3800, 0x5800]   # 1-5 spawns ahead of the first (0xB800), 0x20 apart
OTHER_COLOUR = 0x2464              # every other gondola's frame


def apply(rom):
    data = bytes(rom.data[SPAWN_DATA:SPAWN_DATA + 30])
    assert int.from_bytes(data[8:12], "big") == GONDOLA, data.hex()
    assert rom.u16(GONDOLA + 0x14) == 0xB800          # move.w #0xB800,0x3A(a5): the first run's angle
    inline = "\n".join("    .word 0x%04X" % int.from_bytes(data[i:i + 2], "big") for i in range(0, 30, 2))
    angles = ",".join("0x%04X" % a for a in OLDER)
    prefill = rom.place_code("""
    move.w #1,0x4000(%%a5)             | as before: spawn the first one at once
    movem.l %%d0-%%d7/%%a0-%%a2,-(%%sp)
    lea angles(%%pc),%%a2
    moveq #0,%%d7                       | count, for alternating the colour from the second one
1:  suba.l %%a1,%%a1
    jsr 0x%(spawn)X                     | a gondola, as the spawner makes them; a1 stays 0 if no slot
%(inline)s
    cmpa.l #0,%%a1
    beq 9f
    movem.l %%d7/%%a1-%%a2,-(%%sp)        | 0x%(clear)X clears d0-d7 and uses a2
    jsr 0x%(clear)X
    movem.l (%%sp)+,%%d7/%%a1-%%a2
    move.l %%a5,0x4010(%%a1)
    move.w #-1,0x2C(%%a1)
    btst #0,%%d7
    bne 2f
    move.w #0x%(colour)X,8(%%a1)
2:  move.b #1,0x29(%%a1)               | do its first-run set-up here, at its angle
    move.w #0x3000,0x38(%%a1)
    move.w (%%a2)+,0x3A(%%a1)
    clr.w 0x3C(%%a1)
    move.w #0x80,0x3E(%%a1)
    move.b 0(%%a1),0x402E(%%a1)
    move.b 2(%%a1),0x402F(%%a1)
    addq.w #1,%%d7
    cmpi.w #%(count)d,%%d7
    bne 1b
9:  movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a2
    rts
angles:
    .word %(angles)s
""" % {"spawn": SPAWN, "inline": inline, "clear": CLEAR_EXTRA, "colour": OTHER_COLOUR, "count": len(OLDER),
       "angles": angles}, why="sunken wheel: its older gondolas placed at once")
    rom.write(SPAWNER_FIRST, bytes.fromhex("4EB9") + prefill.to_bytes(4, "big"),
              expect=bytes.fromhex("3B7C00014000"), why="sunken wheel: starts full")
