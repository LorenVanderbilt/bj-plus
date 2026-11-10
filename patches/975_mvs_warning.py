NAME = "mvs-warning"
DESCRIPTION = "Arcade (MVS) mode: a screen saying Plus needs home console (AES) mode, instead of the game"

# Plus is made for the home console (AES) mode: in arcade (MVS) mode the title menu, the options and more are left
# out, and the AES set's added sprite art (the grown C ROMs) isn't there in the MVS set. So, rather than a half-working
# game, MVS mode shows a message (the user, 2026-11-10, for the beta: AES only for now).
# The BIOS calls the game through its USER vector (0x122: jmp 0x9400) with a request in 0x10FDAE: 0 initialise,
# 1 the eyecatcher, 2 the attract (demo, title), 3 the title with a credit in. With the system-mode byte 0x10FD82
# non-zero (MVS) and request 2 or 3, the vector now goes to `warn`: interrupts off, every sprite hidden, the fix layer
# cleared and LINES printed in the S ROM font (tile 0x500 + the character, as the title's COPYRIGHT) in palette PAL
# (title-menu's white shades) on a black backdrop; then it stays there, kicking the watchdog. Requests 0 and 1, and the
# AES, go on to 0x9400 as before.
USER_VECTOR = 0x122             # jmp 0x9400
USER = 0x9400
SYSTEM_MODE = 0x10FD82          # BIOS: 0 = home console (AES)
REQUEST = 0x10FDAE              # BIOS: the USER request
PAL = 5
COLOURS = [0x8000, 0xFFFF, 0xFEEE, 0xFDDD, 0xFCCC, 0xFBBB, 0xFAAA, 0xF999, 0xF888, 0xF777, 0xF666, 0xF555, 0xF444,
           0xF333, 0xF222, 0xF111]   # title-menu's FONT_COLOURS
BACKDROP = 0x401FFE
FONT = 0x500
LINES = [(10, "BLUE'S JOURNEY PLUS"),
         (13, "THIS VERSION ONLY RUNS IN"),
         (15, "HOME CONSOLE (AES) MODE."),
         (18, "PLEASE SET YOUR SYSTEM OR"),
         (20, "EMULATOR TO AES.")]       # (fix row, text): each centred, inside the CRT-safe columns 3-36
WATCHDOG = 0x300001


def apply(rom):
    assert rom.data[USER_VECTOR:USER_VECTOR + 6] == bytes.fromhex("4EF9") + USER.to_bytes(4, "big")
    records = ""
    for row, text in LINES:
        assert len(text) <= 34
        col = (40 - len(text)) // 2
        records += "    .word 0x%X\n    .ascii \"%s\"\n    .byte 0\n    .even\n" % (0x7000 + col * 32 + row,
                                                                                 text.replace('"', '\\"'))
    code = rom.place_code("""
| the USER entry: in MVS mode, the attract or the title (requests 2, 3) shows the message instead
    tst.b 0x%(mode)X
    beq 9f
    cmpi.b #2,0x%(request)X
    bcs 9f
    move.w #0x2700,%%sr
    move.w #1,0x3C0004
    move.w #0x8200,0x3C0000            | every sprite's height 0: hidden
    move.w #380,%%d1
0:  move.w #0,0x3C0002
    dbf %%d1,0b
| the font's palette (written out, not a copy loop: palette-timing counts those), a black backdrop
%(palette)s    move.w #0x8000,0x%(backdrop)X
    move.w #0x7000,0x3C0000            | the fix layer: all blank
    move.w #0x4FF,%%d1
2:  move.w #0x%(blank)X,0x3C0002
    dbf %%d1,2b
    move.w #32,0x3C0004                | the lines, a column at a time
    lea lines(%%pc),%%a0
3:  move.w (%%a0)+,%%d0
    beq 6f
    move.w %%d0,0x3C0000
4:  moveq #0,%%d0
    move.b (%%a0)+,%%d0
    beq 5f
    add.w #0x%(font)X,%%d0
    move.w %%d0,0x3C0002
    bra 4b
5:  move.l %%a0,%%d0                     | to the next word
    addq.l #1,%%d0
    andi.w #0xFFFE,%%d0
    movea.l %%d0,%%a0
    bra 3b
6:  move.b %%d0,0x%(watchdog)X
    bra 6b
9:  jmp 0x%(user)X
lines:
%(records)s    .word 0
""" % {"mode": SYSTEM_MODE, "request": REQUEST, "palette": "".join("    move.w #0x%04X,0x%X\n" % (c, 0x400000 + PAL * 32 + 2 * i) for i, c in enumerate(COLOURS)),
       "backdrop": BACKDROP, "blank": PAL << 12 | (FONT + 0x20), "font": PAL << 12 | FONT, "watchdog": WATCHDOG,
       "user": USER, "records": records}, why="mvs-warning: the AES-only message")
    rom.write(USER_VECTOR + 2, code.to_bytes(4, "big"), expect=USER.to_bytes(4, "big"),
              why="USER: in MVS mode, the AES-only message")
