NAME = "invincible-points"
DESCRIPTION = "Invincible (bamboo shoot): an enemy run through shows its points (+50 / +250) rising from it and fading away"

# While powered up (form 2 in the player block), touching an enemy kills it (0x42C72). Its points come from 0x47526
# (0x50, or 0x250 for some kinds) and are added to the score by the calls in SCORE_SITES, with the enemy pushed on
# the stack just before.
#
# Each call now also spawns a pop-up object (NEW_OBJECT) UP px above the enemy, showing +50 or +250 in a small font
# (GLYPHS) in SPEED UP's gold. Palette 6 is always loaded, so it can be used anywhere. The pop-up rises (RISE, slowing
# by SLOW) for LIFE frames, then fades by dropping half its pixels in a checkerboard (FADES), since the hardware has no
# transparency. A second, sparser fade step was dropped to save tiles for the leaf tornado.
SCORE_SITES = [(0x42C9E, 0x5E28E), (0x42CA6, 0x5E294)]   # jsr <add to player 1 / 2's score>
POINTS_AT = [(0x4752C, 0x250), (0x47536, 0x50)]           # move.l #points,d0 in 0x47526
NEW_OBJECT = 0xFFEC            # returns a1; ne if no slot is free
MOVE = 0xA258                  # moves an object: +0x0C y speed, +0x10 its change per frame
PALETTE = 6                    # SPEED UP's
PRIORITY = 0x20                # +0x28: lower draws in front; Blue is 0x80
UP, LEFT = 18, 11              # px from the enemy to the pop-up's top left
RISE, SLOW = 0x40, -1
LIFE = 48
FADES = [(12, 1)]              # frames left, fade step
ROWS = [7, 5, 3, 1, 3, 5, 8]   # palette 6 colour for each glyph row, as in SPEED UP
OUTLINE = 15
GLYPHS = {
    "+": [".....", "..1..", "..1..", "11111", "..1..", "..1..", "....."],
    "0": [".11.", "1..1", "1..1", "1..1", "1..1", "1..1", ".11."],
    "2": ["111.", "...1", "...1", ".11.", "1...", "1...", "1111"],
    "5": ["1111", "1...", "111.", "...1", "...1", "...1", "111."],
}


def picture(text, fade):
    """text centred in 32x16 pixels (two tiles), gold with an outline; fade 1 or 2 thins it out."""
    glyphs = [GLYPHS[c] for c in text]
    w = sum(len(g[0]) for g in glyphs) + len(glyphs) - 1
    gold = [[0] * 32 for _ in range(16)]
    x, top = (32 - w) // 2, (16 - len(ROWS)) // 2
    for g in glyphs:
        for r, line in enumerate(g):
            for i, ch in enumerate(line):
                if ch == "1":
                    gold[top + r][x + i] = ROWS[r]
        x += len(g[0]) + 1
    out = [[0] * 32 for _ in range(16)]
    for y in range(16):
        for x in range(32):
            if gold[y][x]:
                out[y][x] = gold[y][x]
            elif any(0 <= y + dy < 16 and 0 <= x + dx < 32 and gold[y + dy][x + dx]
                     for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                out[y][x] = OUTLINE
            if fade == 1 and (x + y) % 2 or fade == 2 and (x % 2 or y % 2):
                out[y][x] = 0
    return out


def apply(rom):
    values = []
    for at, points in POINTS_AT:
        assert rom.u16(at) == 0x203C and rom.u32(at + 2) == points, hex(at)
        values.append(points)
    frames = {}
    for points in values:
        for fade in range(len(FADES) + 1):
            pic = picture("+%X" % points, fade)
            tiles = [rom.add_sprite_tile([row[c * 16:c * 16 + 16] for row in pic], share=True,
                                         why="invincible points: +%X (fade %d)" % (points, fade)) for c in range(2)]
            n = rom.add_frame([tiles], PALETTE, why="invincible points: +%X (fade %d)" % (points, fade))
            frames.setdefault(points, []).append(n)
        assert frames[points] == [frames[points][0] + 4 * f for f in range(len(FADES) + 1)]
    fades = "".join("    cmpi.w #%d,0x50(%%a5)\n    bhi 3f\n    addq.w #4,%%d0\n" % (left, ) for left, _ in FADES)
    code = rom.place_code("""
    bra.w popup
%(wrappers)s
spawn:                                  | d0 = points; the enemy is at 24(sp), pushed by the caller
    movem.l %%d0-%%d2/%%a0-%%a1,-(%%sp)
    jsr 0x%(new)X
    bne 9f
    movea.l 24(%%sp),%%a0               | reload: NEW_OBJECT changes a0 and d0
    move.l (%%sp),%%d0
    move.l #popup,4(%%a1)
    move.l (%%a0),(%%a1)
    addi.w #%(up)d,(%%a1)
    subi.w #%(left)d,2(%%a1)
    move.w #%(frame_small)d,0x52(%%a1)
    cmpi.l #0x%(small)X,%%d0
    beq 1f
    move.w #%(frame_big)d,0x52(%%a1)
1:  clr.b 0x29(%%a1)
9:  movem.l (%%sp)+,%%d0-%%d2/%%a0-%%a1
    rts

popup:                                  | each frame: rise, fade near the end, then remove
    tst.b 0x29(%%a5)
    bne 1f
    st 0x29(%%a5)
    move.w #%(life)d,0x50(%%a5)
    move.w #%(rise)d,0x0C(%%a5)
    clr.w 0x0E(%%a5)
    move.w #%(slow)d,0x10(%%a5)
    clr.w 0x12(%%a5)
    move.b #%(palette)d,0x20(%%a5)
    move.b #0x%(priority)X,0x28(%%a5)
1:  subq.w #1,0x50(%%a5)
    bne 2f
    clr.b 0x28(%%a5)                    | done: remove it
    rts
2:  move.w 0x52(%%a5),%%d0
%(fades)s3:  move.w %%d0,8(%%a5)
    tst.w 0x0C(%%a5)                    | once it stops rising, it stays put
    bgt 4f
    clr.w 0x0C(%%a5)
    clr.w 0x10(%%a5)
4:  jmp 0x%(move)X
""" % {"wrappers": "".join("""
    move.l %%d0,-(%%sp)
    jsr 0x%X
    move.l (%%sp)+,%%d0
    bra.w spawn
""" % routine for _, routine in SCORE_SITES),
           "new": NEW_OBJECT, "up": UP * 128, "left": LEFT * 128, "small": 0x50,
           "frame_small": frames[0x50][0], "frame_big": frames[0x250][0],
           "life": LIFE, "rise": RISE, "slow": SLOW, "palette": PALETTE, "priority": PRIORITY,
           "fades": fades, "move": MOVE},
        why="invincible points: the pop-up")
    for n, (at, routine) in enumerate(SCORE_SITES):
        rom.write(at, bytes.fromhex("4EB9") + (code + 4 + 14 * n).to_bytes(4, "big"),
                  expect=bytes.fromhex("4EB9") + routine.to_bytes(4, "big"),
                  why="invincible kill: player %d's points, and a pop-up showing them" % (n + 1))
