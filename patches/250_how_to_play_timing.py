NAME = "how-to-play-timing"
DESCRIPTION = "How-to-play cinema: more time for the longer text boxes (WHEN BLUE IS LITTLE ..., THROW DOWN ...)"

# The how-to-play cinema (0x1111C) is a 960-frame demo; its remaining frames count down in 0x103800, and on English
# consoles 0x544E2 shows each text box when that count reaches its start: JUMP 896, CHANGE SIZE 832, WHEN BLUE IS
# LITTLE... 640, BUT HE CANNOT ATTACK 576, THROW DOWN... 448, YOU CAN THROW... 320, THE FLOWERS... 192. The four-line
# WHEN BLUE IS LITTLE... got only 64 frames (about a second) and BUT HE CANNOT ATTACK 128, while CHANGE SIZE (two
# words) had 192. Now: CHANGE SIZE 96, WHEN BLUE IS LITTLE... 144, BUT HE CANNOT ATTACK 128, THROW DOWN... 160 (was 128),
# YOU CAN THROW... 112 (was 128). (The Japanese
# schedule, 0x542C8 - Japanese consoles - is unchanged.)
STARTS = [  # (address of the cmpi.w's immediate, old start, new start)
    (0x544F8, 640, 736),   # WHEN BLUE IS LITTLE ...
    (0x54500, 576, 592),   # BUT HE CANNOT ATTACK.
    (0x54508, 448, 464),   # THROW DOWN THE LEAF TO STUN YOUR ENEMIES.
    (0x54510, 320, 304),   # YOU CAN THROW A STUNNED ENEMY
]


def apply(rom):
    for addr, old, new in STARTS:
        rom.write(addr, new.to_bytes(2, "big"), expect=old.to_bytes(2, "big"),
                  why="how-to-play: text box starts at %d frames left (was %d)" % (new, old))
