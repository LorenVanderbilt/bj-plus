NAME = "stage-select"
DESCRIPTION = "The original game plus a stage select on every attract screen (Up / Down) - for before-and-after footage"

# Built only by `tools/hackbuild.py --original` (./run.sh --original), into build/original/: the untouched game
# with just this, so "before" shots can be taken anywhere without playing through. Everything else is the original.
#   * On every attract screen - the story cinema from power-on, the title, the demo - Up / Down step through STAGES
#     (START AT BEGINNING, then each stage - no colon: the font has none), shown in the top-left corner: the screens'
#     shared per-frame PUSH START routine (PUSH_START) does it first, then its own work.
#   * Start begins a new game as usual; at the end of its set-up (MODE3_END) a picked stage goes into the stage bytes
#     the way the developers' own stage select did (the hack's level select does the same), and the how-to-play
#     cinema (HOW_TO_PLAY_CALL) is skipped.
PUSH_START = 0x1B034           # jsr 0x5F050 ; ... (every attract screen calls it once a frame)
PUSH_START_FIRST = 0x5F050
MODE3_END = 0x113B4            # move.b #0,0x3004(a6) (mode 3 -> mode 0: the stage starts)
HOW_TO_PLAY_CALL = 0x1132C     # move.b 26624(a6),30878(a6) ; bsr 0x1111C
HOW_TO_PLAY = 0x1111C
PICK = 0x10E909                # the stage picked (0 = none; spare RAM, zeroed with the attract cycle)
BUTTONS_NEW = 0x10FD97         # BIOS: player 1's new presses (bit 0 Up, bit 1 Down)
TEXT_AT = (2, 3)               # (column, row) on the fix layer
TEXT_ATTR = 5 * 0x1000 + 0x500 # the title's PUSH START palette, the font at fix tile 0x500 + character
STAGES = [(2, "JUNGLE 1"), (3, "JUNGLE 2"), (5, "LOW EARTH 1"), (4, "LOW EARTH 2"), (6, "LOW EARTH 3"),
          (7, "LOW EARTH 4"), (8, "MARSH 1"), (10, "MARSH 2"), (9, "MARSH 3"), (11, "MARSH 4"),
          (16, "MECH CITY 1"), (17, "MECH CITY 2"), (18, "MECH CITY 3"), (19, "MECH CITY 4"),
          (24, "STRANGE SP 1"), (25, "STRANGE SP 2"), (26, "STRANGE SP 3"), (27, "STRANGE SP 4"),
          (28, "DARUMA 1"), (29, "DARUMA 2"), (30, "DARUMA 3"), (31, "DARUMA 4")]
FIRST = "BEGINNING"


def apply(rom):
    width = max(len(n) for _, n in STAGES + [(0, FIRST)])
    names = [FIRST] + [n for _, n in STAGES]
    table = "".join(("START AT " + n).ljust(9 + width) + "\0" for n in names)
    entry = 9 + width + 1
    assert rom.data[PUSH_START:PUSH_START + 6] == bytes.fromhex("4EB90005F050")
    assert rom.data[MODE3_END:MODE3_END + 6] == bytes.fromhex("1D7C00003004")
    assert rom.u16(HOW_TO_PLAY_CALL + 6) == 0x6100
    code = rom.place_code(r"""
    bra.w attract_step
    bra.w mode3_end
    bra.w how_to_play

| every attract screen, each frame: Up / Down pick a stage, shown top left - then the PUSH START routine's own work
attract_step:
    movem.l %%d0-%%d2/%%a0,-(%%sp)
    moveq #0,%%d1
    move.b 0x%(pick)X,%%d1
    move.b 0x%(buttons)X,%%d0
    btst #0,%%d0                        | Up: the next stage (round to the start)
    beq 1f
    addq.w #1,%%d1
    cmp.w #%(count)d,%%d1
    bls 1f
    moveq #0,%%d1
1:  btst #1,%%d0                        | Down: the one before
    beq 2f
    subq.w #1,%%d1
    bpl 2f
    moveq #%(count)d,%%d1
2:  move.b %%d1,0x%(pick)X
    lea names(%%pc),%%a0
    mulu #%(entry)d,%%d1
    add.w %%d1,%%a0
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #32,0x3C0004                 | (the next column)
    move.w #0x%(text_at)X,0x3C0000
3:  moveq #0,%%d0
    move.b (%%a0)+,%%d0
    beq 4f
    add.w #0x%(attr)X,%%d0
    move.w %%d0,0x3C0002
    bra 3b
4:  move.w #1,0x3C0004
    move.w (%%sp)+,%%sr
    movem.l (%%sp)+,%%d0-%%d2/%%a0
    jsr 0x%(first)X                     | (the routine's first instruction, then on with it)
    jmp 0x%(rest)X

| the end of a new game's set-up: a picked stage into the stage bytes
mode3_end:
    moveq #0,%%d0
    move.b 0x%(pick)X,%%d0
    beq 6f
    move.b ids-1(%%pc,%%d0.w),%%d0
    move.b %%d0,0x103005
    move.b %%d0,0x1070F0
    move.b %%d0,0x1074F0
6:  move.b #0,0x103004
    rts

| a new game: the how-to-play cinema unless a stage was picked
how_to_play:
    move.b 26624(%%a6),30878(%%a6)
    tst.b 0x%(pick)X
    bne 7f
    jsr 0x%(how_to_play)X
7:  rts
ids:
    .byte %(ids)s
names:
    .ascii "%(table)s"
    .even
""" % {"pick": PICK, "buttons": BUTTONS_NEW, "count": len(STAGES), "entry": entry,
       "text_at": 0x7000 + TEXT_AT[0] * 32 + TEXT_AT[1], "attr": TEXT_ATTR, "first": PUSH_START_FIRST, "rest": PUSH_START + 6,
       "how_to_play": HOW_TO_PLAY, "ids": ",".join(str(i) for i, _ in STAGES),
       "table": table.replace("\0", "\\0")},
        why="stage select on the attract screens (the original game, for before-and-after footage)")
    rom.write(PUSH_START, bytes.fromhex("4EF9") + code.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90005F050"), why="attract screens: the stage select, then PUSH START's own work")
    rom.write(MODE3_END, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"),
              expect=bytes.fromhex("1D7C00003004"), why="new game: start at the picked stage")
    rom.write(HOW_TO_PLAY_CALL, bytes.fromhex("4EB9") + (code + 8).to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=rom.data[HOW_TO_PLAY_CALL:HOW_TO_PLAY_CALL + 10], why="new game: no how-to-play with a stage picked")
