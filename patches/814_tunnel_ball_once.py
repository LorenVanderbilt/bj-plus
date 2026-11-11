NAME = "tunnel-ball-once"
DESCRIPTION = "The hidden tunnel's life ball can be had once: after that its spot gives the white lily (+10 flowers) again"

# The user, 2026-11-06: tunnel-life-ball's ball came back after every death in Lower Earth Empire 2 (the level's
# objects start again from the restart point), so it could be picked up again and again, a heart each time.
#
# Taking it now marks the player (TAKEN, a byte in the player block's unused tail, after weapon-switch's STASH). While
# a player in the game has the mark, the stage's lilies start as plain lilies (LILY_START), so the tunnel's end gives
# the +10 flowers as before; otherwise they go on to tunnel-life-ball's code, which turns the one at its spot into
# the ball. A new game, a player joining and a continue (JOIN, where weapon-switch clears its weapons too) clear it -
# a continue starts the hearts over, so the ball is back for it.
#
# The mark is set by the life ball's effect (0x4BD54: a4 = the player's block, a0 = the ball; one more heart, up to
# 5) at TAKE, in the ball's stage and not for the lottery's ball (its own frame, LOTTERY_BALL).
TAKEN = 0x3F4                # player block offset (weapon-switch's STASH is 0x3F0-0x3F3)
PLAYER_BLOCKS = [0x107000, 0x107400]
PLAYERS_IN = 0x106800        # bits 0 / 1: player 1 / 2 in the game
TAKE = 0x4BD58               # jsr 0x4B936, in the life ball's effect
JOIN = 0x3B958               # jsr <weapon-switch's join>: a new game / a player joining or continuing (a4 = block)


def apply(rom):
    ball = rom.other_patch("tunnel-life-ball")
    ball_start = rom.u32(ball.LILY_KINDS[0])
    assert ball_start != ball.LILY_START, "tunnel-ball-once: needs tunnel-life-ball's lily hook"
    assert rom.u16(JOIN) == 0x4EB9, "tunnel-ball-once: needs weapon-switch's hook at the join"
    join_before = rom.u32(JOIN + 2)
    code = rom.place_code("""
    bra.w lily                          | +0
    bra.w take                          | +4
    bra.w join                          | +8

| a placed white lily starting: a plain one if a player in the game has had the ball
lily:
    cmpi.b #%(stage_no)d,0x%(stage)X
    bne 9f
    btst #0,0x%(players)X
    beq 1f
    tst.b 0x%(p1)X+%(taken)d
    bne 8f
1:  btst #1,0x%(players)X
    beq 9f
    tst.b 0x%(p2)X+%(taken)d
    beq 9f
8:  jmp 0x%(lily_start)X
9:  jmp 0x%(ball_start)X

| the life ball's effect: the tunnel's ball taken
take:
    cmpi.b #%(stage_no)d,0x%(stage)X
    bne 0f
    cmpi.w #0x%(lottery_ball)X,8(%%a0)
    beq 0f
    st %(taken)d(%%a4)
0:  jmp 0x4B936

| a new game / a player joining or continuing: not had yet
join:
    jsr 0x%(join_before)X
    clr.b %(taken)d(%%a4)
    rts
""" % {"stage_no": ball.LILY_STAGE, "stage": ball.STAGE, "players": PLAYERS_IN, "p1": PLAYER_BLOCKS[0],
       "p2": PLAYER_BLOCKS[1], "taken": TAKEN, "lily_start": ball.LILY_START, "ball_start": ball_start,
       "lottery_ball": ball.LOTTERY_BALL, "join_before": join_before}, why="the hidden tunnel's life ball: once")
    for at in ball.LILY_KINDS:
        rom.write(at, code.to_bytes(4, "big"), expect=ball_start.to_bytes(4, "big"),
                  why="a placed white lily: plain once the tunnel's ball was had")
    rom.write(TAKE, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"), expect=bytes.fromhex("4EB90004B936"),
              why="the life ball taken: the tunnel's?")
    rom.write(JOIN + 2, (code + 8).to_bytes(4, "big"), expect=join_before.to_bytes(4, "big"),
              why="a new game / joining: the tunnel's ball not had yet")
