NAME = "gameover-smog"
DESCRIPTION = "Game over: smog clouds drift right to left over the polluted scene, each layer rippling up and down"

# The GAME OVER scene (the smokestacks: 0x236xx - set up, faded in at FADE_IN_CALL, a frame loop while its text types,
# a hold, faded out at FADE_OUT_CALL) gets LAYERS of smog clouds in front of its picture: each a strip of cloud art
# (art/gameover_smog/layerN.png, 256 px wide - it repeats - and a whole number of tiles tall) in sprites of its own,
# COLUMNS of them side by side from FIRST_SLOT on (above the scene's: it uses 1-143). Each frame (at the end of the
# game's vblank wait, VBLANK_END - before screen-blackout's - so they move through the fades and the hold too) a
# layer slides DRIFT/256 px to the left (its sprites a pixel further each time, then back 16 px with the next column of
# art: the strip runs on endlessly, no jump) and each column bobs on the layer's wave: a sine across the screen
# (WAVES of it), AMP px either way, rolling ROLL/256 steps of 64 a frame - anchored to the screen, the clouds
# drifting through it. The palette (PALETTE: empty in this scene; the art's colours, transparent 0) goes in once the
# screen isn't held black (screen-blackout's flag); the sprites are hidden as the scene fades out.
# At most two layers overlap on a line (the scene uses up to 51 sprites a line; two layers 42 - under the 96).
# (Its own patch, last, so its code moves nothing.)
import math

FADE_IN_CALL = 0x236EE         # jsr <the scene's fade-in>
FADE_OUT_CALL = 0x23752        # jsr 0x15724 - the scene's fade-out
VBLANK_END = 0xE8B2            # jmp <screen-blackout's vblank end>
BLACKOUT = 0x10E600            # (screen-blackout's flag: the screen held black)
PALETTE = 0x7E
FIRST_SLOT = 296               # 4 layers x COLUMNS sprites: 296-379
COLUMNS = 21                   # (20 cover the screen, one more coming in)
ART = "art/gameover_smog/layer%d.png"
# (art, top y px, drift 1/256 px a frame, wave: amp px, waves across the screen, roll 1/256 of a step of 64 a frame -
#  minus: rolling the other way)
LAYERS = [(1, 6, 64, (3, 1.0, 64)), (2, 30, 102, (4, 1.5, -128)), (3, 52, 154, (3, 2.0, 192)), (4, 74, 205, (2, 1.25, -64))]
RAM = 0x10D400                 # spare RAM (the game only clears 0x10D000-0x10E6FF at the attract cycle's start): ON
ON, PAL_DUE, STATE = RAM, RAM + 1, RAM + 4   # (bytes), then 8 bytes a layer: offset (long, 1/256 px), roll (word),
                                             # the column of art its first sprite last showed (byte; 0xFF: none yet)


def apply(rom):
    assert rom.u16(FADE_IN_CALL) == 0x4EB9 and rom.u16(FADE_OUT_CALL) == 0x4EB9 and rom.u16(VBLANK_END) == 0x4EF9
    fade_in, fade_out, after = rom.u32(FADE_IN_CALL + 2), rom.u32(FADE_OUT_CALL + 2), rom.u32(VBLANK_END + 2)
    assert fade_out == 0x15724
    from png_tiles import read_rgba, rgb_to_neo
    strips = [read_rgba(ART % n) for n, _, _, _ in LAYERS]       # (rows of ((r, g, b), alpha))
    colours = []
    for rows in strips:
        assert len(rows[0]) == 256 and len(rows) % 16 == 0, "gameover-smog: a strip is 256 px wide, whole tiles tall"
        for row in rows:
            for rgb, a in row:
                if a >= 128 and rgb not in colours:
                    colours.append(rgb)
    assert len(colours) <= 15, "gameover-smog: %d colours (15 at most)" % len(colours)
    words = [0x8000] + [rgb_to_neo(c) for c in colours] + [0] * (15 - len(colours))
    layer_src = []
    for i, ((n, top, drift, (amp, waves, roll)), im) in enumerate(zip(LAYERS, strips)):
        rows = len(im) // 16
        tiles = []
        for col in range(16):
            for row in range(rows):
                cells = [im[row * 16 + y][col * 16:col * 16 + 16] for y in range(16)]
                pixels = [[colours.index(rgb) + 1 if a >= 128 else 0 for rgb, a in r] for r in cells]
                tiles.append(rom.add_sprite_tile(pixels, why="game over smog: layer %d" % n, share=True))
        wave = [int(round(amp * math.sin(2 * math.pi * k / 64))) for k in range(64)]
        kx = int(round(waves * 64 * 256 / 320))          # (8.8 steps of 64 a pixel)
        layer_src.append("""
layer%(i)d:
    .word %(top)d, %(drift)d, %(kx)d, %(roll)d, %(rows)d, %(slot)d
    .long tiles%(i)d, wave%(i)d
tiles%(i)d:
    .word %(tiles)s
wave%(i)d:
    .byte %(wave)s
    .even""" % {"i": i, "top": top, "drift": drift, "kx": kx, "roll": roll & 0xFFFF, "rows": rows,
                "slot": FIRST_SLOT + i * COLUMNS, "tiles": ",".join("0x%X" % t for t in tiles),
                "wave": ",".join(str(w & 0xFF) for w in wave)})
    code = rom.place_code("""
    bra.w setup                         | (+0)
    bra.w tick                          | (+4)
    bra.w finish                        | (+8)

| before the scene's fade-in: the layers set up and drawn
setup:
    movem.l %%d0-%%d7/%%a0-%%a5,-(%%sp)
    lea 0x%(state)X,%%a0
    moveq #%(n)d-1,%%d0
1:  clr.l (%%a0)+
    clr.w (%%a0)+
    move.w #0xFF00,(%%a0)+
    dbf %%d0,1b
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
    move.w #0x8000+%(first)d,0x3C0000    | (full size)
    move.w #%(sprites)d-1,%%d0
2:  move.w #0x0FFF,0x3C0002
    dbf %%d0,2b
    move.w (%%sp)+,%%sr
    st 0x%(pal_due)X
    st 0x%(on)X
    bsr update
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a5
    jmp 0x%(fade_in)X

| the scene faded out: the layers hidden, off
finish:
    jsr 0x%(fade_out)X
    move.l %%d0,-(%%sp)
    clr.b 0x%(on)X
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    move.w #1,0x3C0004
    move.w #0x8200+%(first)d,0x3C0000
    move.w #%(sprites)d-1,%%d0
1:  move.w #0,0x3C0002
    dbf %%d0,1b
    move.w (%%sp)+,%%sr
    move.l (%%sp)+,%%d0
    rts

| the end of the vblank wait (d1-a5 free; d0 kept): the layers on a frame
tick:
    tst.b 0x%(on)X
    beq 9f
    tst.b 0x%(pal_due)X                 | (the colours, once the screen isn't held black)
    beq 1f
    tst.b 0x%(blackout)X
    bne 1f
    clr.b 0x%(pal_due)X
    lea colours(%%pc),%%a0
    lea 0x400000+%(palette)d*32,%%a1
    moveq #15,%%d1
0:  move.w (%%a0)+,(%%a1)+
    dbf %%d1,0b
1:  move.l %%d0,-(%%sp)
    bsr update
    move.l (%%sp)+,%%d0
9:  jmp 0x%(after)X

| each layer: on by a frame, its sprites placed
update:
    lea layers(%%pc),%%a5
    lea 0x%(state)X,%%a4
    moveq #%(n)d-1,%%d7
0:  movea.l (%%a5)+,%%a3                | a3 = the layer's data
    move.w 2(%%a3),%%d0                 | drift
    ext.l %%d0
    add.l %%d0,(%%a4)                   | offset (1/256 px)
    move.w 6(%%a3),%%d0                 | roll
    add.w %%d0,4(%%a4)
    move.l (%%a4),%%d6
    lsr.l #8,%%d6                       | px
    move.w %%d6,%%d5
    andi.w #15,%%d5                     | d5 = fine
    lsr.w #4,%%d6
    andi.w #15,%%d6                     | d6 = the first sprite's column of art
    move.w %%sr,-(%%sp)
    or.w #0x0700,%%sr
    cmp.b 6(%%a4),%%d6
    beq 3f
    move.b %%d6,6(%%a4)                 | (a new column: every sprite's tiles)
    move.w #1,0x3C0004
    move.w 10(%%a3),%%d4                | first slot
    lsl.w #6,%%d4
    movea.l 12(%%a3),%%a2               | tiles
    move.w 8(%%a3),%%d3                 | rows
    moveq #%(columns)d-1,%%d2
    move.w %%d6,%%d1                    | the column of art
1:  move.w %%d4,0x3C0000
    move.w %%d1,%%d0
    mulu %%d3,%%d0
    add.w %%d0,%%d0
    lea (%%a2,%%d0.w),%%a1
    move.w %%d3,%%d0
    subq.w #1,%%d0
2:  move.w (%%a1)+,0x3C0002
    move.w #%(palette)d<<8,0x3C0002
    dbf %%d0,2b
    addi.w #64,%%d4
    addq.w #1,%%d1
    andi.w #15,%%d1
    dbf %%d2,1b
3:  move.w #0x200,0x3C0004              | (SCB3 then SCB4, a sprite at a time)
    move.w 10(%%a3),%%d4
    addi.w #0x8200,%%d4                 | d4 = SCB3 address
    movea.l 16(%%a3),%%a2               | the wave
    moveq #0,%%d1
    sub.w %%d5,%%d1                     | d1 = x
    moveq #%(columns)d-1,%%d2
4:  move.w %%d1,%%d0                    | the wave here: (x * kx) / 256 + roll / 256, of 64
    muls 4(%%a3),%%d0
    asr.l #8,%%d0
    move.w 4(%%a4),%%d3
    lsr.w #8,%%d3
    add.w %%d3,%%d0
    andi.w #63,%%d0
    move.b (%%a2,%%d0.w),%%d0
    ext.w %%d0
    add.w (%%a3),%%d0                   | y = top + the wave
    move.w #496,%%d3
    sub.w %%d0,%%d3
    andi.w #0x1FF,%%d3
    lsl.w #7,%%d3
    or.w 8(%%a3),%%d3                   | its height
    move.w %%d4,0x3C0000
    move.w %%d3,0x3C0002                | SCB3
    move.w %%d1,%%d3
    andi.w #0x1FF,%%d3
    lsl.w #7,%%d3
    move.w %%d3,0x3C0002                | SCB4
    addq.w #1,%%d4
    addi.w #16,%%d1
    dbf %%d2,4b
    move.w (%%sp)+,%%sr
    addq.l #8,%%a4
    dbf %%d7,0b
    rts

colours:
    .word %(colours)s
layers:
    .long %(layer_ptrs)s
%(layer_src)s
""" % {"state": STATE, "n": len(LAYERS), "first": FIRST_SLOT, "sprites": len(LAYERS) * COLUMNS, "pal_due": PAL_DUE,
       "on": ON, "fade_in": fade_in, "fade_out": fade_out, "blackout": BLACKOUT, "palette": PALETTE, "after": after,
       "columns": COLUMNS, "colours": ",".join("0x%04X" % w for w in words),
       "layer_ptrs": ",".join("layer%d" % i for i in range(len(LAYERS))), "layer_src": "\n".join(layer_src)},
        why="game over: smog clouds")
    jsr = lambda to: bytes.fromhex("4EB9") + to.to_bytes(4, "big")
    rom.write(FADE_IN_CALL, jsr(code), expect=jsr(fade_in), why="game over scene: its smog set up")
    rom.write(FADE_OUT_CALL, jsr(code + 8), expect=jsr(fade_out), why="game over scene: its smog off after the fade")
    rom.write(VBLANK_END + 2, (code + 4).to_bytes(4, "big"), expect=after.to_bytes(4, "big"),
              why="vblank wait's end: the game over smog")
