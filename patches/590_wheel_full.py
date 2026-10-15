NAME = "wheel-full"
DESCRIPTION = "The sunken wheels start full: their gondolas already all the way round when a wheel comes into play"

# A sunken wheel's gondolas come from a spawner (object code 0x315C0): its first run sets its count-down (+0x4000)
# to 1, and every time that runs out (then every 0x40 frames) it spawns a gondola (0xA158, inline data: object area
# 0x5380, 31 slots, the gondola's first 0x20 bytes ...), points it at itself (+0x4010), and gives every other one the
# other colour (frame 0x2464 for an odd count, +0x4003). A gondola (0x3164A) starts at angle 0xB8 (+0x3A, a word; its
# first run sets that, the radius 0x30 at +0x38, the turn 0x80 a frame at +0x3E - and marks itself set up, +0x29)
# and is gone at 0x60: six of them ride the wheel at once, 0x20 apart. A wheel came into play empty - rush to one,
# or go back to one, and nothing to jump to until they came round. Now the spawner's first run also places the
# five older ones (OLDER: their angles, as if it had been running), each set up as the spawner and their own first
# run would have.
SPAWNER_FIRST = 0x315D2            # move.w #1,0x4000(a5): the first spawn at once
SPAWN = 0xA158
SPAWN_DATA = 0x31602               # the spawner's inline data (30 bytes): area, slots, the new object's fields
CLEAR_EXTRA = 0x10098              # (a1: a new object's +0x4000 area cleared, as the spawner does)
GONDOLA = 0x3164A
OLDER = [0xD800, 0xF800, 0x1800, 0x3800, 0x5800]   # 1-5 spawns older than the first (0xB800), 0x20 steps each
OTHER_COLOUR = 0x2464              # (every other gondola's frame)


def apply(rom):
    data = bytes(rom.data[SPAWN_DATA:SPAWN_DATA + 30])
    assert int.from_bytes(data[8:12], "big") == GONDOLA, data.hex()
    assert rom.u16(GONDOLA + 0x14) == 0xB800          # move.w #0xB800,0x3A(a5) - its first run's angle
    inline = "\n".join("    .word 0x%04X" % int.from_bytes(data[i:i + 2], "big") for i in range(0, 30, 2))
    angles = ",".join("0x%04X" % a for a in OLDER)
    prefill = rom.place_code("""
    move.w #1,0x4000(%%a5)             | (as before: the first spawn at once)
    movem.l %%d0-%%d7/%%a0-%%a2,-(%%sp)
    lea angles(%%pc),%%a2
    moveq #0,%%d7                       | (which one: every other the other colour, from the second)
1:  suba.l %%a1,%%a1
    jsr 0x%(spawn)X                     | (a gondola, as the spawner's - no free slot: a1 stays 0)
%(inline)s
    cmpa.l #0,%%a1
    beq 9f
    movem.l %%d7/%%a1-%%a2,-(%%sp)        | (0x%(clear)X clears d0-d7 and uses a2)
    jsr 0x%(clear)X
    movem.l (%%sp)+,%%d7/%%a1-%%a2
    move.l %%a5,0x4010(%%a1)
    move.w #-1,0x2C(%%a1)
    btst #0,%%d7
    bne 2f
    move.w #0x%(colour)X,8(%%a1)
2:  move.b #1,0x29(%%a1)               | its first run, done here: at its angle
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
