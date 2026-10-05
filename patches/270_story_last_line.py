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
# Scene 4 has no text box (the other scenes' boxes are part of their background maps: scene 3's is sprites 200-219,
# rows 20-23 - y 160-223 - of four tiles in palette 0x84, the right column and the bottom row mirrored). Scene 4
# keeps that palette, so its loop draws the same box with sprites BOX_SPRITE.. (free in scene 4, and drawn after
# its other sprites: in front of the leaves, behind the text), from its set-up until the beam.
#
# The leaves part lasts while Blue rises and shrinks (stage 1, 64 frames), then holds still for 32 frames (stage 2)
# before the beam. Stage 2 is held longer (STAGE2_HOLD) so there is time to read the line; his rise keeps its
# speed. (Slowing the rise doesn't work: the shrink step 0x202 packs horizontal and vertical shrink in one word,
# and any step but a whole multiple of 0x101 garbles his sprite.)
SCENE3_NEXT_LINE = 0x358FE   # lea 0x3591E,a0 (then picks the line and prints it)
AFTER_LAST_LINE = 0x359A0
SCENE4_SETUP = 0x35372       # jsr 0x9FBE
SCENE4_LOOP = 0x353D0        # jsr 0xCAF2
BEAM_START = 0x35494         # move.l #0x3551C,4(a5)
TEXT_EN, TEXT_JP = 0x3595E, 0x3591E
STAGE2_TIMER = 0x3546E       # move.w #32,16384(a5)
STAGE2_HOLD = 90                # 1.5 s
TEXT_POS = 0x7078
BOX_SPRITE = 260            # 20 sprites from here: the box's columns
BOX_ON = 0x10EFFA           # a byte (spare RAM): draw the box
BOX_TILES = (0x56E8, 0x56E9, 0x56EA, 0x56EB)   # corner, top edge, left edge, inside (palette 0x84)
BOX_Y = 160
# With the last line gone, scene 3 would sit on an empty box for 63 frames (0x359A0's countdown, like each line's)
# before Blue's leap; the leap itself is kept whole.
LEAP_WAIT_AT, LEAP_WAIT = 0x359C3, 15
# How long a line stays after it has typed out (each line's countdown, 63 frames in the original).
LINE_HOLDS = [(0x3576F, 95, "THIS IS BLUE, ... LEAF DUMP."), (0x35839, 95, "BLUE LOVES PRINCESS FA ...")]


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


def box_table():
    """Each column's four (tile, attribute) pairs, top to bottom: the corner / edge tiles, flipped for the right
    column (bit 0) and the bottom row (bit 1)."""
    corner, top, side, inside = BOX_TILES
    words = []
    for col in range(20):
        edge = col in (0, 19)
        h = 1 if col == 19 else 0
        for row in range(4):
            v = 2 if row == 3 else 0
            if row in (0, 3):
                tile = corner if edge else top
            else:
                tile = side if edge else inside
            words += [tile, 0x8400 | h | v]
    return words


def apply(rom):
    stub = rom.place_code("    rts\n", why="story: the last line's callback (nothing)")
    en, jp = text_copy(rom, TEXT_EN, stub), text_copy(rom, TEXT_JP, stub)

    rom.write(SCENE3_NEXT_LINE, bytes.fromhex("4EF9") + AFTER_LAST_LINE.to_bytes(4, "big"),
              expect=bytes.fromhex("41F90003591E"), why="story scene 3: no last line, straight to the leap")

    setup = rom.place_code(
        "    jsr 0x9FBE\n"
        "    st 0x%X\n"
        "    lea 0x%X,%%a0\n"
        "    tst.b 0x10FD83\n"
        "    beq.s 1f\n"
        "    lea 0x%X,%%a0\n"
        "1:  move.w #0x%X,%%d0\n"
        "    jmp 0x2152C\n" % (BOX_ON, jp, en, TEXT_POS),
        why="story scene 4: print the last line")
    rom.write(SCENE4_SETUP, bytes.fromhex("4EB9") + setup.to_bytes(4, "big"), expect=bytes.fromhex("4EB900009FBE"),
              why="story scene 4: set-up prints the last line")

    loop = rom.place_code(
        "    jsr 0xCAF2\n"
        "    jsr 0x21562\n"
        "    tst.b 0x%X\n"
        "    beq 9f\n"
        "    movem.l %%d0-%%d3/%%a0,-(%%sp)\n"
        "    move.w %%sr,-(%%sp)\n"
        "    or.w #0x0700,%%sr\n"
        "    move.w #1,0x3C0004\n"
        "    lea box(%%pc),%%a0\n"
        "    move.w #%d,%%d1\n"
        "    moveq #19,%%d2\n"
        "1:  move.w %%d1,%%d0\n"
        "    lsl.w #6,%%d0\n"
        "    move.w %%d0,0x3C0000\n"
        "    moveq #7,%%d3\n"
        "2:  move.w (%%a0)+,0x3C0002\n"
        "    dbf %%d3,2b\n"
        "    move.w %%d1,%%d0\n"
        "    add.w #0x8000,%%d0\n"
        "    move.w %%d0,0x3C0000\n"
        "    move.w #0x0FFF,0x3C0002\n"          # SCB2: full size
        "    move.w %%d1,%%d0\n"
        "    add.w #0x8200,%%d0\n"
        "    move.w %%d0,0x3C0000\n"
        "    move.w #0x%X,0x3C0002\n"            # SCB3: y, 4 tiles high
        "    move.w %%d1,%%d0\n"
        "    add.w #0x8400,%%d0\n"
        "    move.w %%d0,0x3C0000\n"
        "    move.w %%d1,%%d0\n"
        "    sub.w #%d,%%d0\n"
        "    lsl.w #8,%%d0\n"
        "    lsl.w #3,%%d0\n"                    # x = column * 16, in the SCB4 x field
        "    move.w %%d0,0x3C0002\n"
        "    addq.w #1,%%d1\n"
        "    dbf %%d2,1b\n"
        "    move.w (%%sp)+,%%sr\n"
        "    movem.l (%%sp)+,%%d0-%%d3/%%a0\n"
        "9:  rts\n"
        "box:\n    .word %s\n" % (BOX_ON, BOX_SPRITE, ((496 - BOX_Y) << 7) | 4, BOX_SPRITE,
                                ",".join("0x%X" % w for w in box_table())),
        why="story scene 4: run the text engine, draw the text box")
    rom.write(SCENE4_LOOP, bytes.fromhex("4EB9") + loop.to_bytes(4, "big"), expect=bytes.fromhex("4EB90000CAF2"),
              why="story scene 4: the loop runs the text engine")

    beam = rom.place_code(
        "    move.l #0x3551C,4(%%a5)\n"
        "    movem.l %%d0-%%d7/%%a0-%%a6,-(%%sp)\n"
        "    clr.b 0x%X\n"                       # the box off: its sprites 0 tiles high
        "    move.w %%sr,-(%%sp)\n"
        "    or.w #0x0700,%%sr\n"
        "    move.w #1,0x3C0004\n"
        "    move.w #0x%X,0x3C0000\n"
        "    moveq #19,%%d0\n"
        "1:  move.w #0,0x3C0002\n"
        "    dbf %%d0,1b\n"
        "    move.w (%%sp)+,%%sr\n"
        "    jsr 0x34ED4\n"
        "    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a6\n"
        "    rts\n" % (BOX_ON, 0x8200 + BOX_SPRITE),
        why="story scene 4: the beam clears the last line and its box")
    rom.write(BEAM_START, bytes.fromhex("4EB9") + beam.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("2B7C0003551C0004"), why="story scene 4: clear the line as the beam starts")

    for at, frames, line in LINE_HOLDS:
        rom.write(at, bytes([frames]), expect=bytes([63]), why="story scene 3: %s stays a little longer" % line)
    rom.write(LEAP_WAIT_AT, bytes([LEAP_WAIT]), expect=bytes([63]), why="story scene 3: a short wait before the leap")
    rom.write(STAGE2_TIMER + 2, STAGE2_HOLD.to_bytes(2, "big"), expect=(32).to_bytes(2, "big"),
              why="story scene 4: Blue holds over the leaves longer before the beam")
