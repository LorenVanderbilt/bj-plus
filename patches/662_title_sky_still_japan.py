NAME = "title-sky-still-japan"
DESCRIPTION = "Title screen (Japan): the sky stays still - with the RAGUY logo the drifting clouds put too many sprites on a line (it flickered)"

# On a Japanese board (the BIOS's country, REGION, 0) the title's logo is RAGUY: two sprite objects over the same
# 21 columns each. On the lines it shares with title-clouds' drifting band (the top 80 px) and the foliage (from line
# 64) that made 105 sprites - over the hardware's 96, so columns of the logo dropped out from frame to frame (the
# user, 2026-11-23). The logo can't sit clear of both (moving it 16 px lower kept 105 and ran it into the PLUS
# banner), so on a Japanese board the clouds don't drift: the call of title-clouds' frame routine in the title's
# per-frame chain (from FRAME_CALL) goes straight to what it calls first, title-menu's, and the sky stays as the
# title drew it, as in the original. The English title (83 at most) keeps its drift.
FRAME_CALL = 0x1AF94         # jsr <the title's per-frame chain: title-banner, title-clouds, title-menu>
REGION = 0x10FD83            # BIOS: the country - 0 Japan, 1 USA, 2 Europe
CLOUDS_SIGN = bytes.fromhex("48E7FFC040E7")   # title-clouds' frame, after its call on: movem.l d0-d7/a0-a1,-(sp) ;
                                              # move.w sr,-(sp)


def apply(rom):
    # Each link of the chain is a block starting `bra.w frame`, whose frame starts `jsr <the next link>`: follow it
    # to the call of title-clouds' code (found by what its frame does after its own call) and send that call here.
    site = FRAME_CALL + 2
    while True:
        link = rom.u32(site)
        frame = link + 2 + int.from_bytes(rom.data[link + 2:link + 4], "big", signed=True)
        assert rom.u16(link) == 0x6000 and rom.u16(frame) == 0x4EB9, "title-sky-still-japan: chain at 0x%X" % link
        if bytes(rom.data[frame + 6:frame + 12]) == CLOUDS_SIGN:
            break
        site = frame + 2
    menu = rom.u32(frame + 2)                    # what title-clouds calls first: title-menu's
    code = rom.place_code("""
    tst.b 0x%(region)X                  | Japan: on to title-menu's, the sky still
    bne 1f
    jmp 0x%(menu)X
1:  jmp 0x%(clouds)X
""" % {"region": REGION, "menu": menu, "clouds": link}, why="title (Japan): a still sky")
    rom.write(site, code.to_bytes(4, "big"), expect=link.to_bytes(4, "big"),
              why="the title's frame: the clouds drift outside Japan only")
