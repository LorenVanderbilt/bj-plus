NAME = "beta-mark"
DESCRIPTION = "BETA 1 in the title's top right corner, so a copy passed around shows which build it is (the pause menu has it too)"

# The user, 2026-11-10: mark the beta inside the game, in case the files get passed around and it's unclear whether
# it's the final version. The title shows LABEL in its own font (palette 5, tile 0x500 + the character, as its
# COPYRIGHT lines) at AT, the top right corner inside the CRT-safe area (columns 3-36, rows 4-28 - hud-safe-area).
# It's written on every frame of the title from its per-frame chain (FRAME_CALL), so nothing the title draws can
# leave it out. pause-menu's NOTE puts the same under its menu.
LABEL = "BETA 1"
AT = (31, 4)                    # fix column and row of its first character
FONT = 0x5500                   # palette 5, tiles 0x500 + ASCII
FRAME_CALL = 0x1AF94            # jsr (the title's per-frame chain: title-menu, title-clouds, title-banner)


def apply(rom):
    col, row = AT
    assert col + len(LABEL) - 1 <= 36 and 4 <= row <= 28, "beta-mark: LABEL outside the safe area"
    before = rom.u32(FRAME_CALL + 2)
    code = rom.place_code("""
| the title, every frame: LABEL in its corner, then the rest of the chain
    movem.l %%d0/%%a0,-(%%sp)
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #32,0x3C0004
    move.w #0x%(addr)X,0x3C0000
    lea label(%%pc),%%a0
0:  moveq #0,%%d0
    move.b (%%a0)+,%%d0
    beq 1f
    add.w #0x%(font)X,%%d0
    move.w %%d0,0x3C0002
    bra 0b
1:  move.w #1,0x3C0004
    move.w (%%sp)+,%%sr
    movem.l (%%sp)+,%%d0/%%a0
    jmp 0x%(before)X
label:
    .ascii "%(label)s"
    .byte 0
    .even
""" % {"addr": 0x7000 + col * 32 + row, "font": FONT, "before": before, "label": LABEL},
        why="beta-mark: BETA 1 on the title")
    rom.write(FRAME_CALL, bytes.fromhex("4EB9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB9") + before.to_bytes(4, "big"), why="title: BETA 1 every frame")
