NAME = "save-name"
DESCRIPTION = "Memory card saves named BJ PLUS and the stage as world-level (3-1, BOSS 2, FINAL BOSS)"

# A save's first 20 bytes are its label, what card screens show. The game wrote a 12-character name ("BLUE'S J.   ",
# or "RAGUY STAGE " on Japanese consoles) and then 8 characters from its stage table (0xF1D6: "03 - 01 " for Empire
# Marsh 1, its last two worlds numbered 07 and 08, "BOSS 01 "). It is now "BJ PLUS " and the stage as world-level in
# play order, e.g. "BJ PLUS 3-1" (the user, 2026-11-09). The hook replaces the game's copy of the stage text
# (STAGE_TEXT_COPY, with d0 = the stage * 8 and a0 at the label's 12th byte) and writes the whole label; title-menu's
# stamp then writes the same 8-character name over its start (its SAVE_LABEL_NAME).
STAGE_TEXT_COPY = 0xF026        # lea 0xF1D6(pc),a1 ; move.l 0(a1,d0.w),(a0)+ ; move.l 4(a1,d0.w),(a0)+
SAVE_BUF = 0x103100             # the game's save, its label first
PREFIX = "BJ PLUS "
WIDTH = 12                      # the stage's part of the label
WORLDS = [[2, 3], [5, 4, 6, 7], [8, 10, 9, 11], [16, 17, 18, 19], [24, 25, 26, 27], [28, 29, 30, 31]]
                                # each world's stages in play order (title-menu's STAGES)
BOSSES = {33: "BOSS 1", 34: "BOSS 2", 35: "BOSS 3", 36: "BOSS 4", 37: "BOSS 5", 40: "FINAL BOSS"}


def stage_texts():
    texts = dict(BOSSES)
    for w, stages in enumerate(WORLDS):
        for n, stage in enumerate(stages):
            texts[stage] = "%d-%d" % (w + 1, n + 1)
    return "".join(texts.get(s, "").ljust(WIDTH) for s in range(64))     # the game masks the stage to 0-63


def apply(rom):
    assert len(PREFIX) == 8 and len(PREFIX) + WIDTH == 20
    code = rom.place_code("""
| a save being built: its label, BJ PLUS and the stage (d0 = the stage * 8); a0 left after it, as the game's copy
    movem.l %%d0/%%a1,-(%%sp)
    lea 0x%(buf)X,%%a0
    lea prefix(%%pc),%%a1
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    lea stages(%%pc),%%a1
    adda.w %%d0,%%a1
    lsr.w #1,%%d0
    adda.w %%d0,%%a1                    | + the stage * 12
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    move.l (%%a1)+,(%%a0)+
    movem.l (%%sp)+,%%d0/%%a1
    rts
prefix:
    .ascii "%(prefix)s"
stages:
    .ascii "%(stages)s"
""" % {"buf": SAVE_BUF, "prefix": PREFIX, "stages": stage_texts()}, why="save-name: the save's label")
    rom.write(STAGE_TEXT_COPY, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E714E714E71"),
              expect=bytes.fromhex("43FA01AE20F1000020F10004"),
              why="a save's label: BJ PLUS and the stage, world-level")
