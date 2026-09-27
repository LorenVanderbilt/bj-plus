NAME = "stage-select"
DESCRIPTION = "Debug stage select: after Start on the title, pick any stage from a list (Up/Down, any button starts it), plus a sound test"

# A new game runs game mode 3 (0x112C0, via the mode table at 0x10D58, mode byte 0x103004), which sets the
# stage (0x103005) to 2 = JUNGLE ZONE "1", sets each player's own stage byte (player block +0xF0, 0x1070F0
# / 0x1074F0) and finally switches to mode 0 (0x113BC), which starts the stage in 0x103005. The game also
# still contains the developers' own bare-bones stage select (mode 12, 0x12D28); it starts a stage the same
# way (stage into 0x103005 and both +0xF0 bytes, then mode 0), which is what this screen copies.
# The last instruction of mode 3, `move.b #0,0x103004`, is replaced by a call to the screen below, which
# waits for a choice, stores it the same way and then sets mode 0 itself. Mode 3 first plays the
# how-to-play cinema (`bsr 0x1111C` at 0x11332, a self-contained call); that is skipped so the screen comes
# straight after Start.
#
# The last entry opens a sound test screen instead: Left/Right step the sound command number by 1, Up/Down
# by 16, A plays it, B stops all sound, Start goes back. Commands go straight into the game's sound queue
# (0xA27A, delivered to the Z80 by the per-frame wait) rather than through 0x152FE, which filters them (it
# mutes attract-mode sound depending on the BIOS demo-sound setting). Z80 driver ranges: 0x04-0x23 music,
# 0x24-0xEF sound effects, 0xFF stop all.
#
# Both screens take either player's controls (0x10FD96 / 0x10FD9C and both Start bits of 0x10FDAC), so a game
# started with player 2's Start can pick a stage too.
#
# Stage ids (the game's English title cards, table 0x13D9E): 0/1 are the how-to-play copies of the jungle,
# 12-15 and 20-23 are unused placeholders, 32 shop, 33-40 bosses, 41 route select, 42+ none.
STAGES = [
    (2, "JUNGLE ZONE 1"), (3, "JUNGLE ZONE 2"),
    (5, "THE LOWER EARTH EMPIRE 1"), (4, "THE LOWER EARTH EMPIRE 2"),
    (6, "THE LOWER EARTH EMPIRE 3"), (7, "THE LOWER EARTH EMPIRE 4"),
    (8, "EMPIRE MARSH 1"), (10, "EMPIRE MARSH 2"), (9, "EMPIRE MARSH 3"), (11, "EMPIRE MARSH 4"),
    (16, "MECHANICAL CITY 1"), (17, "MECHANICAL CITY 2"), (18, "MECHANICAL CITY 3"), (19, "MECHANICAL CITY 4"),
    (24, "STARGE SPACE 1"), (25, "STARGE SPACE 2"), (26, "STARGE SPACE 3"), (27, "STARGE SPACE 4"),
    (28, "DARUMA EMPIRE 1"), (29, "DARUMA EMPIRE 2"), (30, "DARUMA EMPIRE 3"), (31, "DARUMA EMPIRE 4"),
    (0xFF, "SOUND TEST"),       # not a stage: opens the sound test screen
]

HOOK = 0x113B4           # move.b #0,0x3004(a6)  (mode 3 -> mode 0)
HOW_TO_PLAY_CALL = 0x11332   # bsr 0x1111C
CLEAR_FIX = 0x9FBE       # fills the fix layer with the blank tile
CLEAR_SPRITES = 0xA1BC   # d0..d1 = first..last sprite to hide
WAIT_FRAME = 0xE856      # the game's wait-for-next-frame
CURSOR = 0x10C200        # spare RAM (0x10A3B0-0x10F2FF is unused by the game): the last choice, kept for next time
SOUND_NO = 0x10C201      # spare RAM: the sound test's last number
QUEUE_SOUND = 0xA27A     # the game's sound command queue (d0 = command)
FIRST_SOUND, LAST_SOUND, FIRST_EFFECT = 0x04, 0xEF, 0x24
PAL = 15                 # fix palette used for the text
TITLE_ROW, LIST_ROW, COL = 3, 6, 8
BLINK_ON, BLINK_OFF = 20, 10                 # frames the selected line is shown / hidden
REPEAT_DELAY, REPEAT_RATE = 20, 6            # holding Up/Down: first repeat after, then every, N frames


def fix_addr(col, row):
    return 0x7000 + col * 32 + row


def apply(rom):
    n = len(STAGES)
    # Table: one entry per stage = stage id byte, then the name, zero-terminated, padded to even length.
    table = ""
    for sid, name in STAGES:
        table += "    .byte %d\n    .ascii \"%s\"\n    .byte 0\n    .even\n" % (sid, name)
    table_offsets = []
    off = 0
    for sid, name in STAGES:
        table_offsets.append(off)
        off += (1 + len(name) + 1 + 1) & ~1

    src = r"""
    movem.l %d0-%d7/%a0-%a5,-(%sp)
menu:
    jsr CLEAR_FIX
    moveq #0,%d0
    move.w #379,%d1
    jsr CLEAR_SPRITES
    lea 0x400000+PAL*32,%a0         | text palette: letter shades white, outline black
    move.w #0x0000,(%a0)+
    moveq #3,%d0
1:  move.w #0x7FFF,(%a0)+
    dbf %d0,1b
    moveq #4,%d0
2:  move.w #0x0000,(%a0)+
    dbf %d0,2b
    move.w #0x8000,(%a0)+           | index 10: outline
    move.w #0x8000,0x401FFE         | backdrop: black

    lea title(%pc),%a0
    move.w #TITLE_ADDR,%d1
    bsr print

    moveq #0,%d6
    move.b CURSOR,%d6               | last choice (anything out of range -> first stage)
    cmp.w #COUNT,%d6
    bcs 3f
    moveq #0,%d6
3:  moveq #0,%d7                    | d7 = frame counter for the blink
    move.w #0xFFFF,%d5              | d5 = last frame's buttons: everything "held", so the Start
    moveq #0,%d4                    |      still down from the title does not count; d4 = Up/Down hold time

loop:
    | draw every line; the selected one blinks
    moveq #0,%d3
line:
    move.w %d3,%d0
    add.w %d0,%d0
    lea offsets(%pc),%a0
    move.w (%a0,%d0.w),%d0
    lea table+1(%pc),%a0
    add.w %d0,%a0
    move.w %d3,%d1
    add.w #LIST_ADDR,%d1
    moveq #0,%d2                    | d2 = 0: print the name
    cmp.w %d6,%d3
    bne 4f
    cmp.w #BLINK_ON,%d7
    bcs 4f
    moveq #1,%d2                    | selected and in the "off" part of the blink: blanks instead
4:  bsr print_or_blank
    addq.w #1,%d3
    cmp.w #COUNT,%d3
    bne line

    jsr WAIT_FRAME
    addq.w #1,%d7
    cmp.w #BLINK_ON+BLINK_OFF,%d7
    bcs 5f
    moveq #0,%d7
5:
    | buttons: bit 0 up, 1 down, 4-7 A B C D, bit 8 = Start (either player)
    moveq #0,%d0
    move.b 0x10FD96,%d0
    or.b 0x10FD9C,%d0
    move.b 0x10FDAC,%d2
    and.b #5,%d2
    beq 6f
    bset #8,%d0
6:  move.w %d5,%d1
    not.w %d1
    and.w %d0,%d1                   | d1 = newly pressed this frame
    move.w %d0,%d5
    move.w %d1,%d2
    and.w #0x1F0,%d2
    bne chosen

    move.w %d0,%d2
    and.w #3,%d2
    beq 7f
    addq.w #1,%d4                   | Up/Down held: count, and fake a new press on repeat frames
    cmp.w #REPEAT_DELAY,%d4
    bcs 8f
    move.w %d4,%d2
    sub.w #REPEAT_DELAY,%d2
    ext.l %d2
    divu #REPEAT_RATE,%d2
    swap %d2
    tst.w %d2
    bne 8f
    or.w %d0,%d1
    bra 8f
7:  moveq #0,%d4
8:
    btst #0,%d1                     | up
    beq 9f
    moveq #0,%d7                    | show the new line straight away
    subq.w #1,%d6
    bpl 9f
    move.w #COUNT-1,%d6
9:  btst #1,%d1                     | down
    beq loop
    moveq #0,%d7
    addq.w #1,%d6
    cmp.w #COUNT,%d6
    bcs loop
    moveq #0,%d6
    bra loop

chosen:
    move.b %d6,CURSOR
    add.w %d6,%d6
    lea offsets(%pc),%a0
    move.w (%a0,%d6.w),%d0
    lea table(%pc),%a0
    move.b (%a0,%d0.w),%d0          | the stage id
    cmp.b #0xFF,%d0
    bne 13f
    bsr sound_test
    bra menu
13: move.b %d0,0x103005
    move.b %d0,0x1070F0
    move.b %d0,0x1074F0
    jsr CLEAR_FIX
    movem.l (%sp)+,%d0-%d7/%a0-%a5
    move.b #0,0x103004              | the instruction this call replaced: go to mode 0 = start the stage
    rts

| ---- sound test: d6 = number, d5 = last frame's buttons, d4 = direction hold time ----
sound_test:
    jsr CLEAR_FIX
    lea st_title(%pc),%a0
    move.w #TITLE_ADDR,%d1
    bsr print
    lea st_number(%pc),%a0
    move.w #ST_NUMBER_ADDR,%d1
    bsr print
    lea st_help(%pc),%a0
    move.w #ST_HELP_ADDR,%d3
14: move.w %d3,%d1
    bsr print                       | a0 ends up just past this line's terminator
    addq.w #1,%d3
    tst.b (%a0)
    bne 14b
    moveq #0,%d6
    move.b SOUND_NO,%d6
    cmp.w #FIRST_SOUND,%d6
    bcs 15f
    cmp.w #LAST_SOUND,%d6
    bls 16f
15: move.w #FIRST_EFFECT,%d6
16: move.w #0xFFFF,%d5
    moveq #0,%d4
st_loop:
    move.w %d6,%d0
    move.w #ST_HEX_ADDR,%d1
    bsr print_hex
    lea st_music(%pc),%a0
    cmp.w #FIRST_EFFECT,%d6
    bcs 17f
    lea st_effect(%pc),%a0
17: move.w #ST_TYPE_ADDR,%d1
    bsr print
    jsr WAIT_FRAME
    bsr buttons                     | d0 = held, d1 = new (repeats included for the directions)
    btst #8,%d1                     | Start: back to the stage list
    beq 18f
    move.b %d6,SOUND_NO
    move.w #0xFF,%d0
    bra queue                       | stop everything on the way out (queue returns to our caller)
18: btst #4,%d1                     | A: play
    beq 19f
    move.w %d6,%d0
    bsr queue
19: btst #5,%d1                     | B: stop all
    beq 20f
    move.w #0xFF,%d0
    bsr queue
20: btst #3,%d1                     | right +1
    beq 21f
    addq.w #1,%d6
21: btst #2,%d1                     | left -1
    beq 22f
    subq.w #1,%d6
22: btst #0,%d1                     | up +16
    beq 23f
    add.w #16,%d6
23: btst #1,%d1                     | down -16
    beq 24f
    sub.w #16,%d6
24: cmp.w #FIRST_SOUND,%d6          | wrap around the ends
    bge 25f
    add.w #LAST_SOUND-FIRST_SOUND+1,%d6
25: cmp.w #LAST_SOUND,%d6
    ble st_loop
    sub.w #LAST_SOUND-FIRST_SOUND+1,%d6
    bra st_loop

| d0 = command -> the game's sound queue, all registers kept
queue:
    movem.l %d0-%d7/%a0-%a5,-(%sp)
    jsr QUEUE_SOUND
    movem.l (%sp)+,%d0-%d7/%a0-%a5
    rts

| buttons for the sound test (either player): d0 = held (bit 0-3 up down left right, 4-7 A B C D, 8 Start), d1 = newly
| pressed, with held directions repeating after REPEAT_DELAY frames every REPEAT_RATE frames
buttons:
    moveq #0,%d0
    move.b 0x10FD96,%d0
    or.b 0x10FD9C,%d0
    move.b 0x10FDAC,%d2
    and.b #5,%d2
    beq 26f
    bset #8,%d0
26: move.w %d5,%d1
    not.w %d1
    and.w %d0,%d1
    move.w %d0,%d5
    move.w %d0,%d2
    and.w #15,%d2
    beq 27f
    addq.w #1,%d4
    cmp.w #REPEAT_DELAY,%d4
    bcs 28f
    move.w %d4,%d2
    sub.w #REPEAT_DELAY,%d2
    ext.l %d2
    divu #REPEAT_RATE,%d2
    swap %d2
    tst.w %d2
    bne 28f
    move.w %d0,%d2
    and.w #15,%d2
    or.w %d2,%d1
    rts
27: moveq #0,%d4
28: rts

| d0 = byte, d1 = fix-layer address: two hex digits
print_hex:
    move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.w #32,0x3C0004
    move.w %d1,0x3C0000
    move.w %d0,%d2
    lsr.w #4,%d2
    bsr 29f
    move.w %d0,%d2
    bsr 29f
    move.w #1,0x3C0004
    move.w (%sp)+,%sr
    rts
29: and.w #15,%d2
    add.w #0x30,%d2
    cmp.w #0x3A,%d2
    bcs 30f
    addq.w #7,%d2                   | A-F
30: add.w #PAL*0x1000+0x500,%d2
    move.w %d2,0x3C0002
    rts

| a0 = zero-terminated text, d1 = fix-layer address; print_or_blank prints spaces instead when d2 != 0
print:
    moveq #0,%d2
print_or_blank:
    move.w %sr,-(%sp)
    or.w #0x0700,%sr
    move.w #32,0x3C0004             | next column
    move.w %d1,0x3C0000
10: moveq #0,%d0
    move.b (%a0)+,%d0
    beq 11f
    tst.w %d2
    beq 12f
    moveq #0x20,%d0
12: add.w #PAL*0x1000+0x500,%d0
    move.w %d0,0x3C0002
    bra 10b
11: move.w #1,0x3C0004
    move.w (%sp)+,%sr
    rts

title:
    .ascii "STAGE SELECT"
    .byte 0
st_title:
    .ascii "SOUND TEST"
    .byte 0
st_number:
    .ascii "NUMBER"
    .byte 0
st_music:
    .ascii "MUSIC       "
    .byte 0
st_effect:
    .ascii "SOUND EFFECT"
    .byte 0
st_help:
    .ascii "LEFT RIGHT   STEP 1"
    .byte 0
    .ascii "UP DOWN      STEP 16"
    .byte 0
    .ascii "A            PLAY"
    .byte 0
    .ascii "B            STOP ALL"
    .byte 0
    .ascii "START        BACK"
    .byte 0, 0
    .even
offsets:
OFFSETS
table:
TABLE
"""
    consts = {
        "CLEAR_FIX": "0x%X" % CLEAR_FIX, "CLEAR_SPRITES": "0x%X" % CLEAR_SPRITES,
        "WAIT_FRAME": "0x%X" % WAIT_FRAME, "CURSOR": "0x%X" % CURSOR, "PAL": str(PAL),
        "TITLE_ADDR": "0x%X" % fix_addr(COL, TITLE_ROW), "LIST_ADDR": "0x%X" % fix_addr(COL, LIST_ROW),
        "COUNT": str(n), "BLINK_ON": str(BLINK_ON), "BLINK_OFF": str(BLINK_OFF),
        "REPEAT_DELAY": str(REPEAT_DELAY), "REPEAT_RATE": str(REPEAT_RATE),
        "OFFSETS": "".join("    .word %d\n" % o for o in table_offsets), "TABLE": table,
        "SOUND_NO": "0x%X" % SOUND_NO, "QUEUE_SOUND": "0x%X" % QUEUE_SOUND,
        "FIRST_SOUND": "0x%X" % FIRST_SOUND, "LAST_SOUND": "0x%X" % LAST_SOUND, "FIRST_EFFECT": "0x%X" % FIRST_EFFECT,
        "ST_NUMBER_ADDR": "0x%X" % fix_addr(COL, 7), "ST_HEX_ADDR": "0x%X" % fix_addr(COL + 8, 7),
        "ST_TYPE_ADDR": "0x%X" % fix_addr(COL, 9), "ST_HELP_ADDR": "0x%X" % fix_addr(COL, 13),
    }
    for k in sorted(consts, key=len, reverse=True):
        src = src.replace(k, consts[k])
    screen = rom.place_code(src, why="stage select screen: list, blinking cursor, Up/Down, any button starts; sound test")
    rom.write(HOW_TO_PLAY_CALL, bytes.fromhex("4E714E71"), expect=bytes.fromhex("6100FDE8"),
              why="new game: skip the how-to-play cinema so the stage select comes straight after Start")
    rom.write(HOOK, bytes.fromhex("4EB9") + screen.to_bytes(4, "big"), expect=bytes.fromhex("1D7C00003004"),
              why="new game: show the stage select before starting the stage")
