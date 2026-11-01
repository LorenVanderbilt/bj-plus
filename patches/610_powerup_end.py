NAME = "powerup-end"
DESCRIPTION = "Pinecone powerup's end: white flashing to the last frame, then normal again at once - no shrink back"

# When the powerup timer runs out (0x42602), the hero goes into state 41, with a step each frame (0x4262A) that
# shrank him by 8 (zoom +0x26, STEP) down to 0xC0. Then it ended at 0x4264A: full size, jsr 0x151CE, the normal art
# set (+0x62 = 0), the Y and X nudges undone, and pose 0 (+8), which draws nothing until his idle animation picks a
# pose 4 frames later; the shrink hid that gap. From REST on, the player block gets form 1 and he stands. With the
# hero always big, this looked like a shrink and a pop.
#
# The step now jumps straight to the end. It's the same ending, except only the Y nudge is undone (pinecone-blink
# only applies the Y one at the start too) and he takes the normal standing pose (STANDING) instead of 0.
#
# Before that, the powerup countdown (0x3BDC8, each frame) flashed him white (+0x20 = 0x7F, every other frame) until
# 128 frames were left, then switched to a flicker (WARNING: a pose swap with the blank pose 0x0C, keeping the real
# one in player block +0x0C). It looked like he'd stopped blinking early. Now he flashes white to the end, and the
# countdown's end clears +0x20.
WARNING = 0x3BDE2              # bcs when the timer is under 0x80: the flicker instead of the white flash
STEP = 0x42634                 # move.b 0x26(a5),d0 ; subq.b #8,d0: the shrink step
REST = 0x4266A                 # movea.l 0x6804(a6),a4 ...: the rest of the ending, after its pose
STANDING = 0x3C


def apply(rom):
    assert rom.u32(WARNING - 4) == 0x0C400080, "expected cmpi.w #0x80,d0"
    rom.write(WARNING, bytes.fromhex("4E71"), expect=bytes.fromhex("6518"),
              why="pinecone powerup: the white flash to the end (no flicker in its last 128 frames)")
    end = rom.place_code("""
    move.w #-1,0x26(%%a5)               | full size
    jsr 0x151CE
    clr.w 0x62(%%a5)                    | the normal art set
    subi.w #0x800,(%%a5)                | undo the Y nudge; the powered-up hero stands 8 units higher
    move.w #0x%(standing)X,8(%%a5)       | the normal standing pose
    jmp 0x%(rest)X
""" % {"standing": STANDING, "rest": REST}, why="pinecone powerup's end: straight back to normal")
    rom.write(STEP, bytes.fromhex("4EF9") + end.to_bytes(4, "big"), expect=bytes.fromhex("102D00265100"),
              why="pinecone powerup's end: no shrink")
