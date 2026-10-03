NAME = "story-last-line"
DESCRIPTION = "Story cinema: the last line (BLUE, DRIVE OUT THE DARUMA ...) moves to the final scene, over the leaves"

# The story cinema runs four scenes (0x15472): the planet (0x34ACC), the Daruma laugh (0x34F9A), Blue
# (0x355B6) and the leaves / light beam (0x3533E). Scene 3 prints its lines as a chain: each line's callback
# starts a countdown object, which clears the box (0x34ED4) and prints the next line. After the last line
# (BLUE, DRIVE OUT ...) its callback 0x359A0 waits 63 frames, then Blue leaps and the scene ends.
#
# Now scene 3 stops after FA FELL ILL ...: its countdown (0x358FE) goes straight to 0x359A0 (wait, leap, end).
# Scene 4 prints the last line as it starts (a copy of the string, ending in a callback that does nothing - the
# original's would end the scene), runs the text engine (0x21562) every frame, which scene 4 never did, and
# clears the line when the light beam starts (Blue's second stage ending, 0x35494, loads the beam's layers).
# Scene 4 has no text box (the other scenes' boxes are part of their background maps), so for now the line
# sits on the leaves.
#
# The leaves part lasts while Blue rises and shrinks: STAGE1 frames (originally 64; shrink 0x202 a frame), then
# 32 more. RISE_SLOWDOWN stretches the first stage (slowing his flight and shrink to match) so there is time
# to read.
SCENE3_NEXT_LINE = 0x358FE   # lea 0x3591E,a0 (then picks the line and prints it)
AFTER_LAST_LINE = 0x359A0
SCENE4_SETUP = 0x35372       # jsr 0x9FBE
SCENE4_LOOP = 0x353D0        # jsr 0xCAF2
STAGE1_TIMER = 0x3539C       # move.w #64,16384(a1)
STAGE1_SHRINK = 0x3545A      # subi.w #0x202,38(a5)
BLUE_VELOCITY = 0x3538E      # in Blue's spawn data: +12 / +14 velocity 0x00A0, 0xFF80 (stage 1 ends by clearing it)
BEAM_START = 0x35494         # move.l #0x3551C,4(a5)
TEXT_EN, TEXT_JP = 0x3595E, 0x3591E
RISE_SLOWDOWN = 3
TEXT_POS = 0x7078
# With the last line gone, scene 3 would sit on an empty box for 63 frames (0x359A0's countdown, like each line's)
# before Blue's leap; the leap itself is kept whole.
LEAP_WAIT_AT, LEAP_WAIT = 0x359C3, 15


def text_copy(rom, at, stub):
    end = at
    while rom.data[end] != 0xFC:
        end += 1
    body = bytes(rom.data[at:end]) + b"\xfc" + stub.to_bytes(4, "big")
    addr = rom.alloc(len(body) + 1, align=2)
    if (end - at) % 2 == 0:          # keep the callback's address on an even byte, as in the original
        addr += 1
    rom.data[addr:addr + len(body)] = body
    return addr


def apply(rom):
    stub = rom.place_code("    rts\n", why="story: the last line's callback (nothing)")
    en, jp = text_copy(rom, TEXT_EN, stub), text_copy(rom, TEXT_JP, stub)

    rom.write(SCENE3_NEXT_LINE, bytes.fromhex("4EF9") + AFTER_LAST_LINE.to_bytes(4, "big"),
              expect=bytes.fromhex("41F90003591E"), why="story scene 3: no last line, straight to the leap")

    setup = rom.place_code(
        "    jsr 0x9FBE\n"
        "    lea 0x%X,%%a0\n"
        "    tst.b 0x10FD83\n"
        "    beq.s 1f\n"
        "    lea 0x%X,%%a0\n"
        "1:  move.w #0x%X,%%d0\n"
        "    jmp 0x2152C\n" % (jp, en, TEXT_POS),
        why="story scene 4: print the last line")
    rom.write(SCENE4_SETUP, bytes.fromhex("4EB9") + setup.to_bytes(4, "big"), expect=bytes.fromhex("4EB900009FBE"),
              why="story scene 4: set-up prints the last line")

    loop = rom.place_code(
        "    jsr 0xCAF2\n"
        "    jmp 0x21562\n",
        why="story scene 4: run the text engine")
    rom.write(SCENE4_LOOP, bytes.fromhex("4EB9") + loop.to_bytes(4, "big"), expect=bytes.fromhex("4EB90000CAF2"),
              why="story scene 4: the loop runs the text engine")

    beam = rom.place_code(
        "    move.l #0x3551C,4(%a5)\n"
        "    movem.l %d0-%d7/%a0-%a6,-(%sp)\n"
        "    jsr 0x34ED4\n"
        "    movem.l (%sp)+,%d0-%d7/%a0-%a6\n"
        "    rts\n",
        why="story scene 4: the beam clears the last line")
    rom.write(BEAM_START, bytes.fromhex("4EB9") + beam.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("2B7C0003551C0004"), why="story scene 4: clear the line as the beam starts")

    rom.write(STAGE1_TIMER + 2, (64 * RISE_SLOWDOWN).to_bytes(2, "big"), expect=(64).to_bytes(2, "big"),
              why="story scene 4: Blue rises over the leaves for longer")
    rom.write(STAGE1_SHRINK + 2, (0x202 // RISE_SLOWDOWN).to_bytes(2, "big"), expect=(0x202).to_bytes(2, "big"),
              why="story scene 4: ... and shrinks more slowly to match")
    rom.write(LEAP_WAIT_AT, bytes([LEAP_WAIT]), expect=bytes([63]), why="story scene 3: a short wait before the leap")
    vx, vy = 0x00A0, -0x80
    rom.write(BLUE_VELOCITY, (vx // RISE_SLOWDOWN).to_bytes(2, "big") + (vy // RISE_SLOWDOWN & 0xFFFF).to_bytes(2, "big"),
              expect=bytes.fromhex("00A0FF80"), why="story scene 4: ... and flies more slowly to match")
