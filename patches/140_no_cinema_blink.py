NAME = "no-cinema-blink"
DESCRIPTION = "No invincibility blink on the hero at the start of the how-to-play cinema"

# Spawning a player sets the invincibility timer (player block +9) to 0xA0 - the blink at the start of every
# stage, so the player isn't hit straight away. The how-to-play cinema (0x1111C) plays as player 2 and sets
# up its hero with two direct calls, `jsr 0x3BA84` (spawn: resets the form, timer = 0xA0) and then
# `jsr 0x3BBB0` at 0x111C2 (creates the player 2 object, sets the timer to 0xA0 again). That second call
# now goes through a wrapper that does the same and then clears player 2's timer (0x107409). Stage starts in
# the game and the attract demo keep the blink.
CINEMA_CREATE = 0x111C2
CREATE_P2 = 0x3BBB0
P2_INVINCIBLE = 0x107409


def apply(rom):
    wrapper = rom.place_code(
        "    jsr 0x%X\n"
        "    clr.b 0x%X\n"
        "    rts\n" % (CREATE_P2, P2_INVINCIBLE),
        why="how-to-play hero: create as usual, then no invincibility blink")
    rom.write(CINEMA_CREATE, bytes.fromhex("4EB9") + wrapper.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + CREATE_P2.to_bytes(4, "big"),
              why="how-to-play cinema: set up the hero without the blink")
