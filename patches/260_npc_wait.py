NAME = "npc-wait"
DESCRIPTION = "NPC rooms: after the last line, wait for a button press (up to 10 s) instead of fading out after half a second"

# Each NPC room loops until its text engine's "done" flag (0x107861, set by the last line's end-of-text callback)
# and then waits a fixed time - `move.w #N,d0 ; jsr 0xE858` (N frames; 30 in most rooms, 100 / 120 in a few) -
# before fading out, so a long last line was gone before it could be read. That wait now goes through `npc_wait`:
# the room's own wait, then until a fresh press of A / B / C / D (either player; a button still held from the
# answer to a question doesn't count), or MAX_WAIT frames.
SITES = [0x21B72, 0x22948, 0x22F14, 0x2346A, 0x2374A, 0x2394E, 0x25AAE, 0x26838, 0x270CE, 0x27B62, 0x28670,
         0x2C560, 0x2D3DE, 0x2DE70, 0x2F0F8]   # each `move.w #N,d0`'s immediate; the `jsr 0xE858` follows it
WAIT = 0xE858          # d0 = frames to wait
WAIT_FRAME = 0xE856    # one frame
MAX_WAIT = 600


def apply(rom):
    at = rom.place_code(r"""
npc_wait:
    jsr 0x%X                         | the room's own wait
    movem.l %%d0-%%d2,-(%%sp)
    move.w #%d,%%d2
    move.b 0x10FD96,%%d1             | buttons held now (A B C D = bits 4-7, either player): not a new press
    or.b 0x10FD9C,%%d1
1:  jsr 0x%X
    move.b 0x10FD96,%%d0
    or.b 0x10FD9C,%%d0
    and.b #0xF0,%%d0
    not.b %%d1
    and.b %%d0,%%d1                  | pressed since last frame?
    bne 2f
    move.b %%d0,%%d1
    dbf %%d2,1b
2:  movem.l (%%sp)+,%%d0-%%d2
    rts
""" % (WAIT, MAX_WAIT, WAIT_FRAME), why="NPC rooms: wait for a button after the last line")
    for site in SITES:
        rom.write(site + 2, bytes.fromhex("4EB9") + at.to_bytes(4, "big"), expect=bytes.fromhex("4EB90000E858"),
                  why="NPC room: after the last line, wait for a button (up to 10 s)")
