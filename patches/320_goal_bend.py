NAME = "goal-bend"
DESCRIPTION = "Goal stalk: when touched it arcs from a little above the ground, not swung stiffly from its foot"

# The goal's stalk (sta/aes/goal_bell.sta) is a stack of segment objects, each placed every frame from the stalk's
# base (its parent, +0x4E) at its radius (+0x38, a byte: 8 per 16 px segment) and angle (+0x3A) by 0x5E4F2. Touched,
# each segment runs 0x52A0C: its angle = sin(its phase) x its amplitude (larger higher up, decaying) - all from the
# base, so the whole stalk swung stiffly from its foot. Now the segments within BEND (radius) of the base stay
# upright, and each one above is placed from the segment below it (the object before it: segments are made in
# order) one segment's length on, at its angle x (its radius - BEND) / CURVE - a chain whose angles grow up the
# stalk (the swing gives every segment the same angle): it arcs from the bend.
# (The bells hang from segments, so they follow. Anything else running 0x52A0C is placed as before.)
SWING_PLACE = 0x52A48        # jsr 0x5E4F2 (d0, d1 = the parent's position)
PLACE = 0x5E4F2
BEND = 0                     # radius units (2 px each, 8 a segment): from where it arcs (0: its foot)
CURVE = 48                   # radius units over which a segment's angle reaches the swing's: chosen so its top
                             # sways about as far as before


def apply(rom):
    code = rom.place_code(r"""
    move.b 0x38(%%a5),%%d2
    ext.w %%d2
    cmp.w #%(bend)d,%%d2
    bgt 1f
    clr.w 0x3A(%%a5)                    | (within the bend: upright)
    jmp 0x%(place)X
1:  lea -0x80(%%a5),%%a0                | the segment below: the object before this one, if it's one
    move.l 4(%%a0),%%d3
    cmp.l 4(%%a5),%%d3
    bne 2f
    move.b 0x4E(%%a0),%%d3
    cmp.b 0x4E(%%a5),%%d3
    bne 2f
    move.b 0x38(%%a0),%%d3              | (one segment's length: this radius less that one's)
    sub.b %%d3,%%d2
    ble 2f
    move.b 0x3A(%%a5),%%d3              | its angle grown up the stalk: x (radius - BEND) / CURVE (this frame's -
    ext.w %%d3                          | 0x52A0C sets it again from its swing next frame)
    move.b 0x38(%%a5),%%d0
    ext.w %%d0
    sub.w #%(bend)d,%%d0
    muls %%d0,%%d3
    divs #%(curve)d,%%d3
    move.b %%d3,0x3A(%%a5)
    move.w 0(%%a0),%%d0                 | from its position
    move.w 2(%%a0),%%d1
    move.b 0x38(%%a5),-(%%sp)
    move.b %%d2,0x38(%%a5)
    jsr 0x%(place)X
    move.b (%%sp)+,0x38(%%a5)
    rts
2:  jmp 0x%(place)X                     | (not a stalk: as before)
""" % {"bend": BEND, "place": PLACE, "curve": CURVE}, why="goal stalk: an arc from just above its foot")
    rom.write(SWING_PLACE, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + PLACE.to_bytes(4, "big"), why="goal stalk: placed from its bend")
