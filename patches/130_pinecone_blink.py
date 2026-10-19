NAME = "pinecone-blink"
DESCRIPTION = "Pinecone powerup: no grow animation (the hero is always big now) - the powerup flashing starts at once"

# Picking up the pinecone puts the hero in state 41: 0x3E6F4 from normal size, 0x4086E from shrunk (C button).
# After a check (jsr 0x4529E / bne), it plays sound 0x4D, nudges the position, sets the grow animation (47)
# and hands over to a per-frame handler that zooms the sprite (object +38) up from half (0x7F7F) or quarter
# (0x3F3F) size by 8 steps a frame. At full size it plays sound 13, switches to the big art set (+98 = 0x80),
# starts the 512-frame powerup timer (player +0x24), sets form 2 (player +1) and goes back to standing.
# With hero-big-art the normal hero already looks big, so the zoom just looks like a shrink-and-regrow.
# After the check, both entries now jump to code that does the finishing step straight away (same sounds
# and position nudge, no zoom or grow animation). The powered-up hero's own flashing (the powerup timer
# toggling the palette every other frame) then starts at once and is the blink. (An extra respawn-style
# blink on top, player +9, was tried first: the two per-frame toggles together looked like solid white.)
# Only the grow's Y nudge is kept (the powered-up hero's place is 8 units higher - his sprite stays level); its X
# nudge stepped him back ~9 px, and the grow's pose (0x18) drawn in the big art set stood 16 px high for a few
# frames - so the powered-up standing pose (STANDING) is set at once instead (same size, so nothing after moves).
ENTRIES = [
    # (address after the check, original bytes there, Y position nudge of the original grow)
    (0x3E6FC, "1B7C00290068", 0x0800),   # from normal size
    (0x40876, "1B7C00290068", 0x1000),   # from shrunk
]
STANDING = 0x364
# (Its end, the shrink back: `powerup-end`.)


def apply(rom):
    for addr, orig, dy in ENTRIES:
        cave = rom.place_code(
            "    moveq #0x4D,%%d0\n"
            "    jsr 0x152FE\n"                # the pickup sound
            "    addi.w #0x%X,(%%a5)\n"         # the grow's position nudge
            "    move.w #0x%X,8(%%a5)\n"       # the powered-up standing pose
            "    move.w #-1,38(%%a5)\n"         # full size (no zoom)
            "    moveq #13,%%d0\n"
            "    jsr 0x152FE\n"                # the 'powered up' sound
            "    move.w #0x80,98(%%a5)\n"       # big art set
            "    move.l 26628(%%a6),%%a4\n"     # this player's block
            "    move.w #512,36(%%a4)\n"        # powerup timer
            "    clr.w 12(%%a4)\n"
            "    clr.b 4(%%a4)\n"
            "    clr.b 100(%%a4)\n"
            "    clr.b 9(%%a4)\n"
            "    move.b #2,1(%%a4)\n"           # form 2 = powered up
            "    moveq #0,%%d0\n"
            "    jmp 0x43440\n" % (dy, STANDING),   # back to standing
            why="pinecone: become powered up at once instead of the grow")
        rom.write(addr, bytes.fromhex("4EF9") + cave.to_bytes(4, "big"), expect=bytes.fromhex(orig),
                  why="pinecone pickup: skip the grow animation")
