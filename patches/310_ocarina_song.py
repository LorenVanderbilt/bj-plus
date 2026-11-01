NAME = "ocarina-song"
DESCRIPTION = "Lottery: with an ocarina, the host asks for a song instead; Blue plays it and wins 1st prize (a life ball if he has the ring)"

# The ocarina (player +0x2A, item 0x0F) did nothing but play Blue's idle tune. The lottery's 1st prize comes from
# the frame counter through a table (0x29A6A), whatever he carries. Now, in the English version:
#   * The host's intro text ends at 0x2966E, which sets up the lottery and asks LET'S PLAY! / NO THANKS. (0x296C6
#     sets the time limit, then the question). With an ocarina, the host says SONG_LINES instead, SONG_DELAY frames
#     later, with the intro's last line staying up meanwhile. There's no question and no fee.
#   * That text's callback starts Blue's idle tune SONG_START frames later and starts SONG_COUNT for FIRST PRIZE!.
#     The tune comes from his idle count (hero +0x7A): when it runs out, standing still plays the ocarina animation
#     0x2B and its jingle.
#   * The lottery's timer object (0x29F70, every frame) counts SONG_COUNT down and then says FIRST PRIZE! (0x29B02).
#     From there it's the game's own 1st prize: its picture, its text and the item given.
#   * A 1st prize that would be the lucky ring (the 2nd and 4th lotteries; 0x1078BA counts them, and the prizes
#     alternate life ball and ring) is a life ball if the player already has the ring (+0x1A), whether it was won
#     by the song or drawn.
PLAY_QUESTION = 0x296C6      # move.w #0x140,0x78BC(a6) (#0xFFFF after no-lotto-prompt-timer), then the question
TIMER_TICK = 0x29F70         # subq.w #1,0x78BC(a6) ; bne.s 0x29FA4 (rts)
PRIZE_TEXT_INDEX = 0x29B32   # move.w 0x78BA(a6),d0 ; lsl.w #2,d0: the 1st prize's text
PRIZE_ART_INDEX = 0x29BA0    # move.w 0x78BA(a6),d0 ; add.w d0,d0: the 1st prize's picture
FIRST_PRIZE = 0x29B02        # FIRST PRIZE! in English
SHOW_TEXT, TEXT_BOX = 0x2152C, 0x7086
LANGUAGE = 0x10FD83          # 0 = Japanese
PLAYER = 0x106804            # long: the current player's data
HERO = 0x104000
SET_ANIM = 0x43480           # a5 = object, d0 = animation
SONG_COUNT = 0x10E822        # word
SONG_START = 60              # frames from the end of the song text to Blue's tune
SONG_FRAMES = 200            # frames from then to FIRST PRIZE!
DELAY_COUNT = 0x10E824       # word: the wait before the song text
SONG_DELAY = 90              # frames the intro's last line stays before it
SONG_LINES = ["OH! IS THAT AN", "OCARINA? PLAY", "ME A SONG AND", "I'LL GIVE YOU", "MY BEST PRIZE!"]


def apply(rom):
    text = b"\xfe".join(l.encode() for l in SONG_LINES).replace(b"?", b"\x0a")
    if (len(text) + 1) % 2:
        text += b" "         # the callback's long on an even byte
    base = rom.place_code(r"""
    bra.w question
    bra.w tick
    bra.w index_text
    bra.w index_art

| before the lottery's question: with an ocarina, the song instead
question:
    tst.b 0x%(lang)X
    beq 1f
    movea.l 0x%(player)X,%%a0
    tst.b 0x2A(%%a0)
    bne 2f
1:  move.w #%(limit)d,0x78BC(%%a6)       | the question's time limit, as set before this patch
    rts
2:  move.w #-1,0x78BC(%%a6)
    clr.w 0x%(count)X
    move.w #%(delay)d,0x%(delay_count)X  | the intro's last line stays a while; tick shows the song text
    movem.l %%d0/%%a5,-(%%sp)             | stop Blue starting his tune by himself meanwhile: hold off his idle
    lea 0x%(hero)X,%%a5                 | count until the song text ends, and if he's already playing, stand
    move.w #0x7FFF,0x7A(%%a5)
    cmp.b #0x2B,0x66(%%a5)
    bne 8f
    moveq #0,%%d0
    jsr 0x%(set_anim)X
8:  movem.l (%%sp)+,%%d0/%%a5
    movea.l 0x78E0(%%a6),%%a0           | hide the question's box as LET'S PLAY! does (its frame object,
    clr.b 0x28(%%a0)                    | stored at 0x1078E0, isn't drawn)
    addq.l #4,%%sp                      | skip the question: back to the text's caller
    rts

| the song text has been read: Blue plays his tune, and the prize follows after SONG_FRAMES
song:
    move.w #%(start)d,0x%(hero)X+0x7A     | his idle count: the tune starts when it runs out
    move.w #%(start)d+%(frames)d,0x%(count)X
    rts

| the lottery's timer, every frame: the wait before the song text, then the song's count
tick:
    tst.w 0x%(delay_count)X
    beq 7f
    subq.w #1,0x%(delay_count)X
    bne 4f
    jsr 0x21CBA                         | clear the text box, as LET'S PLAY! does
    jsr 0x21CA2
    lea song_text(%%pc),%%a0
    move.w #0x%(box)X,%%d0
    jsr 0x%(show)X
    bra 4f
7:  tst.w 0x%(count)X
    beq 3f
    subq.w #1,0x%(count)X
    bne 4f
    jsr 0x21CBA                         | clear the text box
    lea 0x%(first)X,%%a0
    move.w #0x%(box)X,%%d0
    jsr 0x%(show)X
4:  addq.l #4,%%sp                      | as the timer's bne to its rts
    rts
3:  subq.w #1,0x78BC(%%a6)
    bne 4b
    rts

| the 1st prize's index (the lottery count, 0x1078BA): on the ring's turn, the life ball if he has the ring
index_text:
    move.w 0x78BA(%%a6),%%d0
    bsr ring_owned
    lsl.w #2,%%d0
    rts
index_art:
    move.w 0x78BA(%%a6),%%d0
    bsr ring_owned
    add.w %%d0,%%d0
    rts
ring_owned:                             | a0 holds the game's table here, so keep it
    btst #0,%%d0
    beq 6f
    move.l %%a0,-(%%sp)
    movea.l 0x%(player)X,%%a0
    tst.b 0x1A(%%a0)
    movea.l (%%sp)+,%%a0
    beq 6f
    subq.w #1,%%d0
6:  rts

    .even
song_text:
    .byte %(text)s
    .byte 0xFC
    .long song
""" % {"lang": LANGUAGE, "player": PLAYER, "count": SONG_COUNT, "box": TEXT_BOX, "show": SHOW_TEXT,
       "hero": HERO, "frames": SONG_FRAMES, "limit": rom.u16(PLAY_QUESTION + 2), "delay": SONG_DELAY, "start": SONG_START, "set_anim": SET_ANIM, "delay_count": DELAY_COUNT, "first": FIRST_PRIZE, "text": ",".join(str(b) for b in text)},
        why="lottery: the ocarina song for 1st prize; no second ring")
    for at, entry, expect, why in [
            (PLAY_QUESTION, base, "3D7C%04X78BC" % rom.u16(PLAY_QUESTION + 2), "lottery question: the ocarina song instead"),
            (TIMER_TICK, base + 4, "536E78BC662E", "lottery timer: the song's count first"),
            (PRIZE_TEXT_INDEX, base + 8, "302E78BAE548", "1st prize's text: no second ring"),
            (PRIZE_ART_INDEX, base + 12, "302E78BAD040", "1st prize's picture: no second ring")]:
        rom.write(at, bytes.fromhex("4EB9") + entry.to_bytes(4, "big"), expect=bytes.fromhex(expect), why=why)
