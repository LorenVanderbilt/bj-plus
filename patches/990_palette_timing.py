NAME = "palette-timing"
DESCRIPTION = ("Our colour changes are made in the vblank, not while the picture is drawn (no streaks on real "
               "hardware); screen-blackout's VRAM reads wait as the console needs")

# The patches' colour changes are queued during the frame and written at the start of the next vblank.
#
# On the real Neo Geo the CPU has priority over the video chip for palette RAM. A colour written while a line is
# drawn shows on screen for a pixel or more, as short 1-pixel streaks that jump about from frame to frame. MAME
# doesn't show them. The game itself writes its colours at the top of the frame, but many patches wrote theirs from
# the frame's work, anywhere down the screen. tools/palette_timing.py finds them.
#
# Each of those writes is a copy loop (move.w (aS)+,(aD)+ ; dbf dK), with aD set to a palette address. The loop is
# swapped for a jsr of the same length to a copy that puts the words in QUEUE instead, as (address, words - 1,
# words), and leaves the registers as the loop did. The goal bells' sparkles are copied another way, so they get a
# routine of their own. The HUD's lives (ten fixed colours, every frame of play) and the bells' pendulum (three) only
# set a flag (DRAWN), and the vblank writes their colours. That costs the frame next to nothing, where a queued copy
# made busy frames run over a little more often.
#
# The queue is written out in the vblank interrupt, after anim-speed's hook (AFTER_ANIM) and before the game's
# handler. That is after water-tint's set-up, so the line its timer counts from doesn't move. The screen changes and
# ROUND CLEAR's dim still write palette RAM themselves, from the vblank wait. They run after the queue has been
# written, so their colours win just as they did before.
#
# A copy that doesn't fit in the queue, or whose address isn't palette RAM (screen-blackout's gaps send the elevator
# cone's colours to spare RAM while the screen is black), is made at once as before.
USED = 0x10D5F0                 # spare RAM (a word): bytes in the queue; 0 = empty, as the attract's RAM clear leaves it
DRAWN = 0x10D5F2                # spare RAM (2 bytes): set when the HUD's lives / the bells' pendulum want their colours
QUEUE, QUEUE_SIZE = 0x10D600, 0x400   # spare RAM, to 0x10D9FF (the busiest frame seen queued ~220 bytes: the shop)
AFTER_ANIM = bytes.fromhex("4EF9000099A0")   # anim-speed's jmp to the game's vblank handler
GAME_MODE = 0x10FD80            # negative while the game (not the BIOS) is running
ELEVATOR = bytes.fromhex("720E" "30D9" "51C9FFFC")   # elevator-spin: moveq #14,d1 ; 1: move.w (a1)+,(a0)+ ; dbf d1,1b
SPARKLE = bytes.fromhex("23F00000"), bytes.fromhex("23F00004")
                                # goal bells: move.l (a0,d0.w),<colour> ; move.l 4(a0,d0.w),<the next two>
PENDULUM = bytes.fromhex("41F900400FC2")      # goal bells: lea 0x400FC2,a0 ; then 3 x move.w #colour,(a0)+ ; rts
BLACK_LOOP = bytes.fromhex("48D000FE" "42A8001C" "41E80020" "51C8FFF2")
                                # screen-blackout: 1: movem.l d1-d7,(a0) ; clr.l 28(a0) ; lea 32(a0),a0 ; dbf d0,1b
REVEAL_SHARE = 64               # the reveal's palettes copied in each vblank (about 20 lines' worth)
DIM_QUARTERS = 4                # ROUND CLEAR's dim: worked out a quarter of the palettes at a time, two a frame
DIM_STAGES = (0x10A800, 0x10DA00)   # 2 KB each, a quarter's colours: the shops' object store (free at ROUND CLEAR,
                                # as round-clear-dim's BUF after it) and spare RAM after the queue (to 0x10E1FF)
DIM_RAM = 0x10D5E0              # spare RAM: +0 / +4 where each stage's quarter goes (0 = none), +8 the stage the
                                # dim's tick works into (longs)
WAITING = 0x10D5F4              # spare RAM (a byte): set during the reveal's own vblank waits
HEIGHTS_LOOP = bytes.fromhex("3680" "30D4" "5240" "51C9FFF8")
                                # screen-blackout: 1: move.w d0,(a3) ; move.w (a4),(a0)+ ; addq.w #1,d0 ; dbf d1,1b
CODE_START = 0xB69A0            # the patches' new code (see tools/hackbuild.py)
LOOPS = 24                      # copy loops into palette RAM in the patches' code, as found when this was written


def copy_loops(rom):
    """Every copy loop into palette RAM in the new code: [(loop address, source, destination, counter)]."""
    found = []
    for at in range(CODE_START, len(rom.data) - 6, 2):
        op = rom.u16(at)
        if op & 0xF1F8 != 0x30D8 or rom.data[at + 2] != 0x51 or rom.data[at + 3] & 0xF8 != 0xC8 \
                or rom.u16(at + 4) != 0xFFFC:
            continue
        dst = (op >> 9) & 7
        for lea in range(at - 2, at - 18, -2):          # the last lea <address>,aD before it
            if rom.u16(lea) == 0x41F9 | dst << 9:
                if 0x400000 <= rom.u32(lea + 2) <= 0x401FFF:
                    found.append((at, op & 7, dst, rom.data[at + 3] & 7))
                break
    return found


def queue_copy(src, dst, counter):
    """The queueing copy for a loop with these registers, as an assembler routine named q<src><dst><counter>."""
    x = next("d%d" % r for r in (1, 2, 3) if r != counter)
    y = next("a%d" % r for r in (2, 3, 4) if r not in (src, dst))
    return """
q%(s)d%(d)d%(k)d:
    move.w %%%%sr,-(%%%%sp)
    ori.w #0x0700,%%%%sr                | no vblank while the queue is half written
    movem.l %%%%%(x)s/%%%%%(y)s,-(%%%%sp)
    cmpa.l #0x400000,%%%%a%(d)d
    bcs 8f
    move.w %%%%d%(k)d,%%%%%(x)s                 | the entry's size: 6 + 2 x words
    add.w %%%%%(x)s,%%%%%(x)s
    addq.w #8,%%%%%(x)s
    add.w 0x%%(used)X,%%%%%(x)s
    cmp.w #0x%%(size)X,%%%%%(x)s
    bhi 8f
    lea 0x%%(queue)X,%%%%%(y)s
    adda.w 0x%%(used)X,%%%%%(y)s
    move.w %%%%%(x)s,0x%%(used)X
    move.l %%%%a%(d)d,(%%%%%(y)s)+
    move.w %%%%d%(k)d,(%%%%%(y)s)+
1:  move.w (%%%%a%(s)d)+,(%%%%%(y)s)+
    addq.l #2,%%%%a%(d)d
    dbf %%%%d%(k)d,1b
    bra 9f
8:  move.w (%%%%a%(s)d)+,(%%%%a%(d)d)+
    dbf %%%%d%(k)d,8b
9:  movem.l (%%%%sp)+,%%%%%(x)s/%%%%%(y)s
    move.w (%%%%sp)+,%%%%sr
    rts
""" % {"s": src, "d": dst, "k": counter, "x": x, "y": y}


def fixed(flag, runs):
    """Assembler for the vblank: if the flag is set, clear it and write the fixed colours [(address, [words])]."""
    return "    tst.b 0x%X\n    beq 1f\n    clr.b 0x%X\n" % (flag, flag) + "".join(
        "    move.w #0x%04X,0x%X\n" % (w, at + 2 * i) for at, words in runs for i, w in enumerate(words)) + "1:\n"


def find1(rom, pattern, what):
    at = rom.data.find(pattern, CODE_START)
    assert at >= 0 and rom.data.find(pattern, at + 1) < 0, "palette-timing: %s not found once" % what
    return at


def dim_writes(rom, jsr):
    """ROUND CLEAR's dim: worked out into DIM_STAGES during the frame, copied in at the next vblank's start."""
    # The dim worked out each step's colours straight into palette RAM, half the palettes a frame, and the work ran
    # down the whole picture (the user saw diagonal lines on the BackBit). Its tick now works a quarter at a time
    # into a stage in RAM, two quarters a frame (each into its own stage, DIM_STAGES, as no 4 KB in one piece is
    # free), and at the start of the next frame's vblank wait both are copied in with movem (about 28 lines, inside
    # the vblank), before the next two are worked out. A step still takes 2 frames: the fade is as it was.
    dim = rom.other_patch("round-clear-dim")
    entry = rom.u32(dim.ROUTINES[0] + 2)
    head = entry + 4                    # its table's second entry: bra.w frame (the vblank wait loop's jump)
    assert rom.u16(head) == 0x6000
    frame = head + 2 + int.from_bytes(rom.data[head + 2:head + 4], "big", signed=True)
    assert rom.data[frame:frame + 4] == bytes.fromhex("301F6100"), "palette-timing: round-clear-dim's frame moved?"
    tick = frame + 4 + int.from_bytes(rom.data[frame + 4:frame + 6], "big", signed=True)
    body = rom.data[tick:tick + 0x100]

    def at(pattern):
        k = body.find(pattern)
        assert k >= 0 and body.find(pattern, k + 1) < 0, "palette-timing: round-clear-dim's %s" % pattern.hex()
        return tick + k
    quarter_pals, quarter_bytes = dim.PALS // DIM_QUARTERS, dim.PALS * 32 // DIM_QUARTERS
    half_pals, half_bytes = dim.PALS // dim.STEP_FRAMES, dim.PALS * 32 // dim.STEP_FRAMES
    edits = [(bytes.fromhex("C6FC") + half_bytes.to_bytes(2, "big"), bytes.fromhex("C6FC") + quarter_bytes.to_bytes(2, "big")),
             (bytes.fromhex("383C") + (half_pals - 1).to_bytes(2, "big"), bytes.fromhex("383C") + (quarter_pals - 1).to_bytes(2, "big")),
             (bytes.fromhex("C2FC") + half_pals.to_bytes(2, "big"), bytes.fromhex("C2FC") + quarter_pals.to_bytes(2, "big")),
             (bytes.fromhex("0C39") + dim.STEP_FRAMES.to_bytes(2, "big") + dim.HALF.to_bytes(4, "big"),
              bytes.fromhex("0C39") + DIM_QUARTERS.to_bytes(2, "big") + dim.HALF.to_bytes(4, "big")),
             (bytes.fromhex("43F9") + (0x400000 + dim.FIRST_PAL * 32).to_bytes(4, "big") + bytes.fromhex("D3C3"),
              bytes.fromhex("2279") + (DIM_RAM + 8).to_bytes(4, "big") + bytes.fromhex("4E71"))]
                                        # lea <palettes>,a1 ; adda.l d3,a1 -> movea.l <the stage>,a1 ; nop
    assert QUEUE + QUEUE_SIZE <= DIM_STAGES[1] and DIM_STAGES[1] + 0x800 <= 0x10E200
    for old, new in edits:
        rom.write(at(old), new, expect=old, why="ROUND CLEAR's dim: a quarter a frame, worked out into RAM")

    code = rom.place_code("""
| the vblank wait's loop, each frame: last frame's two quarters copied in, then round-clear-dim's frame as it was,
| with its tick called twice (a stage each), noting which quarter each works out
    lea 0x%(ram)X,%%a4
    lea 0x%(stage0)X,%%a0
    bsr copy
    lea 0x%(ram)X+4,%%a4
    lea 0x%(stage1)X,%%a0
    bsr copy
    move.w (%%sp)+,%%d0
    move.l #0x%(stage0)X,0x%(ram)X+8
    lea 0x%(ram)X,%%a5
    bsr part
    move.l #0x%(stage1)X,0x%(ram)X+8
    lea 0x%(ram)X+4,%%a5
    bsr part
    dbf %%d0,1f
    jmp 0x%(loop_end)X
1:  jmp 0x%(loop_top)X

| a stage (a0) copied to where (a4) says, if it says
copy:
    tst.l (%%a4)
    beq 1f
    movea.l (%%a4),%%a1
    clr.l (%%a4)
    move.w #%(pals)d-1,%%d1
2:  movem.l (%%a0)+,%%d2-%%d7/%%a2-%%a3
    movem.l %%d2-%%d7/%%a2-%%a3,(%%a1)
    lea 32(%%a1),%%a1
    dbf %%d1,2b
1:  rts

| the tick, into the stage set; if it worked a quarter out, where it goes noted at (a5) (d0, a5 kept)
part:
    moveq #0,%%d1
    move.b 0x%(half)X,%%d1              | the quarter it'll work out, if it does
    move.w 0x%(half)X-1,%%d2            | STEP and HALF (a byte each): changed if it did
    movem.l %%d0-%%d2/%%a5,-(%%sp)
    jsr 0x%(tick)X
    movem.l (%%sp)+,%%d0-%%d2/%%a5
    cmp.w 0x%(half)X-1,%%d2
    beq 1f
    mulu #%(bytes)d,%%d1
    add.l #0x%(pal)X,%%d1
    move.l %%d1,(%%a5)
1:  rts
""" % {"ram": DIM_RAM, "stage0": DIM_STAGES[0], "stage1": DIM_STAGES[1], "pals": quarter_pals, "half": dim.HALF,
       "tick": tick, "bytes": quarter_bytes, "pal": 0x400000 + dim.FIRST_PAL * 32, "loop_end": dim.FRAME_LOOP_END,
       "loop_top": dim.FRAME_LOOP_TOP}, why="ROUND CLEAR's dim: two quarters a frame, copied in at the vblank")
    into = rom.data.find(bytes.fromhex("4EF9") + head.to_bytes(4, "big"), CODE_START)
    assert into >= 0 and rom.data.find(bytes.fromhex("4EF9") + head.to_bytes(4, "big"), into + 1) < 0, \
        "palette-timing: the vblank wait loop's jump to round-clear-dim not found once"
    rom.write(into + 2, code.to_bytes(4, "big"), expect=head.to_bytes(4, "big"),
              why="vblank wait, each frame: ROUND CLEAR's dim copied in first")


def apply(rom):
    loops = copy_loops(rom)
    assert len(loops) == LOOPS, "palette-timing: %d copy loops into palette RAM, not %d - check the new ones" % (
        len(loops), LOOPS)
    elevator = find1(rom, ELEVATOR, "elevator-spin's colour copy") + 2
    loops.append((elevator, 1, 0, 1))

    hud = rom.other_patch("hud")
    hud_runs = [(0x400000 + pal * 32 + entry * 2, [int(w, 16) for w in new.split()])
                for pal, entry, old, new in hud.FACE_COLOURS]
    hud_moves = b"".join(bytes.fromhex("33FC") + w.to_bytes(2, "big") + (at + 2 * i).to_bytes(4, "big")
                         for at, words in hud_runs for i, w in enumerate(words))
    hud_at = find1(rom, hud_moves, "hud's lives colours")

    sparkle = None
    for at in range(CODE_START, len(rom.data) - 16, 2):
        if rom.data[at:at + 4] == SPARKLE[0] and rom.data[at + 8:at + 12] == SPARKLE[1] \
                and rom.u32(at + 12) == rom.u32(at + 4) + 4 and 0x400000 <= rom.u32(at + 4) <= 0x401FFF:
            assert sparkle is None, "palette-timing: goal bells' sparkle colours found twice"
            sparkle = at
    assert sparkle, "palette-timing: goal bells' sparkle colours not found"
    pendulum = find1(rom, PENDULUM + bytes.fromhex("30FC"), "goal bells' pendulum colours")
    assert all(rom.u16(pendulum + 6 + 4 * i) == 0x30FC for i in range(3)) and rom.u16(pendulum + 18) == 0x4E75
    pendulum_runs = [(0x400FC2, [rom.u16(pendulum + 8 + 4 * i) for i in range(3)])]

    after_anim = find1(rom, AFTER_ANIM, "anim-speed's jmp to the game's vblank handler")
    copies = sorted({(s, d, k) for _, s, d, k in loops})
    code = rom.place_code(("""
    bra.w flush                         | +0
    bra.w sparkle                       | +4
""" + "".join("    bra.w q%d%d%d\n" % c for c in copies) + """
| the vblank interrupt, before the game's handler: the queued colours written
flush:
    tst.b 0x%(game_mode)X
    bpl 9f
%(hud)s%(pendulum)s    tst.w 0x%(used)X
    beq 9f
    movem.l %%d0/%%a0-%%a2,-(%%sp)
    move.w 0x%(used)X,%%d0
    cmp.w #0x%(size)X,%%d0
    bhi 3f                              | (not a count this patch wrote: dropped)
    lea 0x%(queue)X,%%a0
    movea.l %%a0,%%a2
    adda.w %%d0,%%a2
1:  movea.l (%%a0)+,%%a1
    move.w (%%a0)+,%%d0
2:  move.w (%%a0)+,(%%a1)+
    dbf %%d0,2b
    cmpa.l %%a2,%%a0
    bcs 1b
3:  clr.w 0x%(used)X
    movem.l (%%sp)+,%%d0/%%a0-%%a2
9:  jmp 0x99A0

| goal bells: the sparkles' two colour pairs, from (a0,d0.w)
sparkle:
    movem.l %%d0/%%a0-%%a1,-(%%sp)
    lea 0(%%a0,%%d0.w),%%a0
    lea 0x%(sparkle_at)X,%%a1
    moveq #3,%%d0
    bsr q010
    movem.l (%%sp)+,%%d0/%%a0-%%a1
    rts
""" + "".join(queue_copy(*c) for c in sorted(set(copies) | {(0, 1, 0)}))) % {
        "game_mode": GAME_MODE, "used": USED, "size": QUEUE_SIZE, "queue": QUEUE, "sparkle_at": rom.u32(sparkle + 4),
        "hud": fixed(DRAWN, hud_runs), "pendulum": fixed(DRAWN + 1, pendulum_runs)}, why="palette timing: colours queued for the vblank")

    rom.write(after_anim + 2, code.to_bytes(4, "big"), expect=(0x99A0).to_bytes(4, "big"),
              why="vblank interrupt, after anim-speed: the queued colours written")
    jsr = lambda a: bytes.fromhex("4EB9") + a.to_bytes(4, "big")
    for at, s, d, k in loops:
        rom.write(at, jsr(code + 8 + 4 * copies.index((s, d, k))), expect=rom.data[at:at + 6],
                  why="palette timing: a colour copy queued for the vblank")
    end = hud_at + len(hud_moves)
    st = lambda a: bytes.fromhex("50F9") + a.to_bytes(4, "big")
    rom.write(hud_at, st(DRAWN) + bytes.fromhex("6000") + (end - (hud_at + 8)).to_bytes(2, "big"),
              expect=rom.data[hud_at:hud_at + 10], why="hud's lives: the face colours left to the vblank")
    rom.write(sparkle, jsr(code + 4) + bytes.fromhex("6008"), expect=rom.data[sparkle:sparkle + 8],
              why="goal bells: the sparkles' colours queued for the vblank")
    rom.write(pendulum, st(DRAWN + 1) + bytes.fromhex("4E75"), expect=rom.data[pendulum:pendulum + 8],
              why="goal bells: the pendulum's colours left to the vblank")

    # The same goes for VRAM, which has its own rule. The LSPC needs about 16 CPU cycles from setting the address
    # to a read (the NeoGeo Dev Wiki's VRAM page), and MAME and FBNeo don't enforce it. Screen-blackout read each
    # sprite's height 8 cycles after setting its address, so on the console it saved stale heights at random, and
    # the screens came back with sprites missing or misplaced. It was the only VRAM access in the patches that was
    # too fast (tools/vram_timing.py). The loop is now a jsr to the same loop with a wait before each read.
    blackout = rom.other_patch("screen-blackout")
    heights = find1(rom, bytes.fromhex("41F9") + blackout.SAVED.to_bytes(4, "big") + bytes.fromhex("303C8201323C") +
                    (blackout.SPRITES - 1).to_bytes(2, "big") + HEIGHTS_LOOP, "screen-blackout's sprite height reads")
    heights += 14
    wait = rom.place_code("""
1:  move.w %d0,(%a3)                    | the sprite's SCB3 address
    addq.w #1,%d0
    nop                                 | then 16 cycles or more before the read
    nop
    move.w (%a4),(%a0)+
    dbf %d1,1b
    rts
""", why="screen-blackout: each sprite's height read after the LSPC's wait")
    rom.write(heights, jsr(wait) + bytes.fromhex("4E714E71"), expect=HEIGHTS_LOOP,
              why="screen-blackout: the sprite heights read with the LSPC's wait")

    # Screen-blackout's two whole-palette jobs ran on past the vblank, and on the console they showed as diagonal
    # white lines on the black screen (the user, on the BackBit), before a title card and going into a shop.
    #
    # Going black cleared every palette a palette at a time, to about line 40. It now clears four palettes a pass
    # with eight zeroed registers, about a quarter faster, which finishes inside the vblank.
    #
    # The reveal's first part copied every new palette but the fix layer's and the backdrop's, with every sprite
    # hidden, and it ran to about line 183. Hidden sprites don't stop the streaks, so the copy is now spread over
    # several vblanks, REVEAL_SHARE palettes in each, starting at the next one. The screen stays black a few frames
    # longer. Its waits are nested inside the vblank wait's end, so WAITING makes screen-blackout's own hook there
    # pass them by.
    zero = find1(rom, BLACK_LOOP, "screen-blackout's palette clear")
    at = rom.data.find(bytes.fromhex("7C006100"), CODE_START)
    while at >= 0 and rom.data[at + 6:at + 14] != bytes.fromhex("13FC0001") + blackout.PHASE.to_bytes(4, "big"):
        at = rom.data.find(bytes.fromhex("7C006100"), at + 2)
    assert at >= 0, "palette-timing: screen-blackout's reveal (moveq #0,d6 ; bsr replay) not found"
    replay = at + 4 + int.from_bytes(rom.data[at + 4:at + 6], "big", signed=True)
    assert rom.data[replay:replay + 6] == bytes.fromhex("45F9") + blackout.LIST.to_bytes(4, "big")
    assert rom.u16(blackout.VBLANK_END) == 0x4EF9
    vblank_end = rom.u32(blackout.VBLANK_END + 2)
    pal_count = blackout.PALETTE_BYTES // 32
    assert pal_count % 4 == 0 and (pal_count - 16) % 4 == 0
    jobs = rom.place_code("""
    bra.w zero                          | +0
    bra.w share                         | +4
    bra.w end                           | +8
    bra.w last                          | +12

| going black: d0 = palettes - 1 (a multiple of 4), a0 the first, d1-d7 zero
zero:
    move.l %%a1,-(%%sp)
    suba.l %%a1,%%a1
    addq.w #1,%%d0
    lsr.w #2,%%d0
    subq.w #1,%%d0
1:  movem.l %%d1-%%d7/%%a1,(%%a0)
    movem.l %%d1-%%d7/%%a1,32(%%a0)
    movem.l %%d1-%%d7/%%a1,64(%%a0)
    movem.l %%d1-%%d7/%%a1,96(%%a0)
    lea 128(%%a0),%%a0
    dbf %%d0,1b
    movea.l (%%sp)+,%%a1
    rts

| the reveal's first part (replay with d6 = 0): the noted loads again, in order, but the fix layer's (0-15) and the
| backdrop's (255), %(share)d palettes a vblank from the next one
share:
    moveq #0,%%d6                       | palettes left in this vblank: none, the sprites were just hidden
    lea 0x%(list)X,%%a2
    move.w 0x%(count)X,%%d3
    bra 4f
2:  movem.l (%%a2)+,%%a0-%%a1
    move.w (%%a2)+,%%d2
3:  move.l %%a0,%%d0
    sub.l #0x%(pal)X,%%d0
    lsr.l #5,%%d0
    cmpi.w #16,%%d0
    bcs 7f
    cmpi.w #255,%%d0
    beq 7f
    subq.w #1,%%d6
    bpl 6f
    movem.l %%d0-%%d7/%%a0-%%a5,-(%%sp)
    st 0x%(waiting)X
    jsr 0xE856
    clr.b 0x%(waiting)X
    movem.l (%%sp)+,%%d0-%%d7/%%a0-%%a5
    move.w #%(share)d-1,%%d6
6:  movem.l (%%a1),%%d0-%%d1/%%d4-%%d5/%%d7/%%a3-%%a5
    movem.l %%d0-%%d1/%%d4-%%d5/%%d7/%%a3-%%a5,(%%a0)
7:  lea 32(%%a0),%%a0
    lea 32(%%a1),%%a1
    dbf %%d2,3b
4:  dbf %%d3,2b
    rts

| the reveal's second part (replay with d6 = 1): just the fix layer's palettes (0-15) and the backdrop's (255) - a
| load that can't hold any of them is passed over whole
last:
    lea 0x%(list)X,%%a2
    move.w 0x%(count)X,%%d3
    bra 4f
2:  movem.l (%%a2)+,%%a0-%%a1
    move.w (%%a2)+,%%d2
    move.l %%a0,%%d0
    sub.l #0x%(pal)X,%%d0
    lsr.l #5,%%d0                       | its first palette
    cmpi.w #16,%%d0
    bcs 3f
    add.w %%d2,%%d0                     | its last
    cmpi.w #255,%%d0
    bcs 4f
3:  move.l %%a0,%%d0
    sub.l #0x%(pal)X,%%d0
    lsr.l #5,%%d0
    cmpi.w #16,%%d0
    bcs 6f
    cmpi.w #255,%%d0
    bne 7f
6:  movem.l (%%a1),%%d0-%%d1/%%d4-%%d5/%%d7/%%a3-%%a5
    movem.l %%d0-%%d1/%%d4-%%d5/%%d7/%%a3-%%a5,(%%a0)
7:  lea 32(%%a0),%%a0
    lea 32(%%a1),%%a1
    dbf %%d2,3b
4:  dbf %%d3,2b
    rts

| the vblank wait's end: screen-blackout's, unless this is one of the reveal's own waits
end:
    tst.b 0x%(waiting)X
    bne 1f
    jmp 0x%(vblank_end)X
1:  movem.l (%%sp)+,%%d1-%%d7/%%a0-%%a5
    rts
""" % {"share": REVEAL_SHARE, "list": blackout.LIST, "count": blackout.COUNT, "pal": blackout.PALETTES,
       "waiting": WAITING, "vblank_end": vblank_end}, why="screen-blackout: going black and the reveal in the vblank")
    rom.write(zero, jsr(jobs) + bytes.fromhex("6008"), expect=BLACK_LOOP[:8],
              why="screen-blackout: going black, four palettes a pass")
    rom.write(at, jsr(jobs + 4), expect=rom.data[at:at + 6],
              why="screen-blackout: the reveal's palettes, a share each vblank")
    rom.write(blackout.VBLANK_END + 2, (jobs + 8).to_bytes(4, "big"), expect=vblank_end.to_bytes(4, "big"),
              why="the vblank wait's end: past screen-blackout's while the reveal waits")

    # The reveal's second part showed every sprite again (380 VRAM writes) and then put in the fix layer's and the
    # backdrop's palettes, which ran to about line 73. The palettes go first now, at the top of the vblank, and a load
    # that can't hold any of them is passed over whole (going through every palette of every load took most of the
    # time); the VRAM writes after them are fine during the picture.
    at = rom.data.find(bytes.fromhex("2F006100"), CODE_START)
    while at >= 0 and not (rom.data[at + 6:at + 10] == bytes.fromhex("7C016100") and rom.u16(at + 12) == 0x201F):
        at = rom.data.find(bytes.fromhex("2F006100"), at + 2)
    assert at >= 0, "palette-timing: screen-blackout's reveal, second part (bsr show_all ; moveq #1,d6 ; bsr replay)"
    second = at + 2
    show_all = second + 2 + rom.u16(second + 2)
    assert second + 8 + rom.u16(second + 8) == replay
    assert rom.data[show_all:show_all + 6] == bytes.fromhex("40E7007C0700"), "palette-timing: show_all moved?"
    bsr = lambda at, to: bytes.fromhex("6100") + (to - (at + 2)).to_bytes(2, "big", signed=True)
    dim_writes(rom, jsr)
    rom.write(second, bytes.fromhex("7C01") + bsr(second + 2, jobs + 12) + bsr(second + 6, show_all),
              expect=rom.data[second:second + 10], why="screen-blackout's reveal: the last palettes before the sprites")
