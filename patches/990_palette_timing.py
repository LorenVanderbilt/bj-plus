NAME = "palette-timing"
DESCRIPTION = "Our colour changes are made in the vblank, not while the picture is drawn (no streaks on real hardware)"

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
QUEUE, QUEUE_SIZE = 0x10D600, 0xC00   # spare RAM, to 0x10E1FF
AFTER_ANIM = bytes.fromhex("4EF9000099A0")   # anim-speed's jmp to the game's vblank handler
GAME_MODE = 0x10FD80            # negative while the game (not the BIOS) is running
ELEVATOR = bytes.fromhex("720E" "30D9" "51C9FFFC")   # elevator-spin: moveq #14,d1 ; 1: move.w (a1)+,(a0)+ ; dbf d1,1b
SPARKLE = bytes.fromhex("23F00000"), bytes.fromhex("23F00004")
                                # goal bells: move.l (a0,d0.w),<colour> ; move.l 4(a0,d0.w),<the next two>
PENDULUM = bytes.fromhex("41F900400FC2")      # goal bells: lea 0x400FC2,a0 ; then 3 x move.w #colour,(a0)+ ; rts
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
