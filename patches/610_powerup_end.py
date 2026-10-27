NAME = "powerup-end"
DESCRIPTION = "Pinecone powerup's end: white flashing to the last frame, then normal again at once - no shrink back"

# The powerup timer running out (0x42602) puts the hero in state 41 with a step each frame (0x4262A) that shrank him
# by 8 (zoom +0x26, from STEP) down to 0xC0, then ended it (0x4264A): full size, jsr 0x151CE, the normal art set
# (+0x62 = 0), the Y / X nudges back, pose 0 (+8: nothing drawn until his idle animation picks one, 4 frames later -
# the shrink hid that), and from REST the player block's form 1 and standing. With the hero always big the shrink
# looked like a shrink-and-pop. Now the step jumps to END at once: the same ending, the Y nudge only (`pinecone-blink`
# keeps only the Y one at the start too) and the normal standing pose (STANDING) instead of 0.
# Before that, the powerup's countdown (0x3BDC8, each frame) flashed him white (+0x20 = 0x7F, every other frame) until
# 128 frames were left, then switched to a flicker (WARNING: bcs to a pose swap with the blank pose 0x0C, the real one
# kept in the player block's +0x0C) - he looked like he'd stopped blinking early. Now he flashes white to the end
# (the countdown's end clears +0x20).
WARNING = 0x3BDE2              # bcs (timer < 0x80: the flicker instead of the white flash)
STEP = 0x42634                 # move.b 0x26(a5),d0 ; subq.b #8,d0 - the shrink's step
REST = 0x4266A                 # movea.l 0x6804(a6),a4 ... - the ending after its pose
STANDING = 0x3C


def apply(rom):
    assert rom.u32(WARNING - 4) == 0x0C400080, "expected cmpi.w #0x80,d0"
    rom.write(WARNING, bytes.fromhex("4E71"), expect=bytes.fromhex("6518"),
              why="pinecone powerup: the white flash to the end (no flicker in its last 128 frames)")
    end = rom.place_code("""
    move.w #-1,0x26(%%a5)               | full size
    jsr 0x151CE
    clr.w 0x62(%%a5)                    | the normal art set
    subi.w #0x800,(%%a5)                | (the Y nudge back - the powered-up hero stands 8 units higher)
    move.w #0x%(standing)X,8(%%a5)       | the normal standing pose
    jmp 0x%(rest)X
""" % {"standing": STANDING, "rest": REST}, why="pinecone powerup's end: straight back to normal")
    rom.write(STEP, bytes.fromhex("4EF9") + end.to_bytes(4, "big"), expect=bytes.fromhex("102D00265100"),
              why="pinecone powerup's end: no shrink")
