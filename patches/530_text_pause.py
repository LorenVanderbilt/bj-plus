NAME = "text-pause"
DESCRIPTION = "Text engine: a pause code (0xFD); the opening's BUT... types its dots one at a time"

# The text engine (0x21768, each frame: the state at 0x107840 - +2 the index into the text, +8 all at once, +9 frames
# per character, +10 the countdown to the next) acts on 0xFF / 0xFE / 0xFC / 0xFB and draws anything else as a
# character. CONTROL (cmpi.b #0xFB,d1 ; beq 0x2181A) now goes through new code: 0xFD waits PAUSE_FRAMES (the
# countdown), then goes on. The story cinema's BUT...... (English; typed a character every 2 frames, so its dots
# came in a blur) is now BUT, then each dot after a pause - the same 9 bytes.
CONTROL = 0x217AC
CHAIN = 0x2181A               # 0xFB's handling
BUT = 0x34C38                 # BUT...... then 0xFC and its callback
PAUSE = 0xFD
PAUSE_FRAMES = 18             # before each dot


def apply(rom):
    code = rom.place_code("""
    cmpi.b #0xFB,%%d1
    bne 1f
    addq.l #4,%%sp
    jmp 0x%(chain)X
1:  cmpi.b #0x%(pause)X,%%d1
    bne 2f
    move.b #%(frames)d,10(%%a3)            | the countdown
    addq.w #1,2(%%a3)                   | past 0xFD
    addq.l #4,%%sp                      | this frame: done
2:  rts
""" % {"chain": CHAIN, "pause": PAUSE, "frames": PAUSE_FRAMES}, why="text engine: 0xFD pauses")
    rom.write(CONTROL, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("0C01FFFB67000068"), why="text engine: its control bytes, with a pause")
    rom.write(BUT, b"BUT" + bytes([PAUSE]) + b"." + bytes([PAUSE]) + b"." + bytes([PAUSE]) + b".",
              expect=b"BUT......", why="story cinema: BUT... a dot at a time")
