NAME = "shop-bounce"
DESCRIPTION = "Fairy shop: a little animation on the shopkeeper while she's selected"

# The shopkeeper's body is object 0x104480 (frame 0x3000, a 9 x 11 tile portrait, tiles 0x5200 + column + 8 * row;
# its per-frame code is an rts at 0x1FA34, set by the shop set-up's data at 0x1F74E). Her code is now `anim`: while
# a player's box (shop-grid-cursor, RAM 0x10E920 / 0x10E921; 8 = her) is on her, it steps through a few frames -
# copies of 0x3000 whose tiles at columns 1-4, rows 4-6 (those that change) are replaced by new tiles with part of
# the picture moved down / up a pixel or two (the pixels MASK fills in, else inside ELLIPSES) - then settles;
# otherwise it shows 0x3000.
BASE_FRAME = 0x3000
CODE_FIELD = 0x1F74E               # her spawn data's code pointer (0x0001FA34)
GRID_RAM = 0x10E920                # shop-grid-cursor: +0 / +1 boxes, +4 / +8 frame counter when each pointer last ran
FRAME_COUNTER = 0x100204
RAM = 0x10EC00                     # a byte: steps since she was selected
BLOCK = (1, 4, 4, 3)               # first column, row, and columns x rows of tiles that may change
ELLIPSES = [(37, 85, 12, 9), (57, 85, 9.5, 9)]   # what moves: frame pixels (centre x, y, radius x, y), one per side
SHIFTS = [2, 1, -1]                # the frames: the band moved down (+) / up (-) this many pixels
SEQUENCE = [1, 2, 0, 3, 0, 2, 0]   # per step (STEP frames each): 0 = the original frame, n = SHIFTS[n-1]; then 0
STEP = 4
PERIOD = 120                       # frames from one bounce to the next while she stays selected
# Which pixels move can be drawn: MASK (the BLOCK area, 16 px per tile: its pixels that move filled in - the picture's
# own, see BLOCK_REFERENCE - the rest clear). Without it, ELLIPSES pick them.
MASK = "art/shop/bounce_mask.png"
BLOCK_REFERENCE = "art/shop/bounce_block.png"   # (the BLOCK area as it is: for drawing the mask over)


def frame_body(rom, frame):
    """The raw definition bytes of an original frame, and where each (column, row) tile's low byte sits in them."""
    p = rom.u32(0x60772 + frame)
    cols, rows = rom.orig[p] + 1, rom.orig[p + 1] + 1
    q = p + 5
    at = {}
    for c in range(cols):
        for r in range(rows):
            b = rom.orig[q]
            if b == 1:                                   # an escape: 1, control, [attribute], [tile high], low
                ctl = rom.orig[q + 1]
                q += 2 + (1 if ctl & 0x40 else 0) + (1 if ctl & 0x20 else 0)
                at[(c, r)] = q
                q += 1
            else:
                if b:
                    at[(c, r)] = q
                q += 1
    end = q
    while rom.orig[end] != 0xFF:
        end += 1
    return bytes(rom.orig[p:end + 1]), p, at


def apply(rom):
    body, p, at = frame_body(rom, BASE_FRAME)
    c0, r0, nc, nr = BLOCK
    def orig(fx, fy):
        return rom.sprite_tile(0x5200 + fx // 16 + 8 * (fy // 16))[fy % 16][fx % 16]
    import os
    mask_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), MASK)
    if os.path.exists(mask_path):
        from png_tiles import read_rgba
        mask = read_rgba(mask_path)
        assert (len(mask[0]), len(mask)) == (nc * 16, nr * 16), "%s: %d x %d" % (MASK, nc * 16, nr * 16)
        def inside(fx, fy):
            return mask[fy - r0 * 16][fx - c0 * 16][1] > 0
    else:
        def inside(fx, fy):
            return any(((fx - cx) / rx) ** 2 + ((fy - cy) / ry) ** 2 <= 1 for cx, cy, rx, ry in ELLIPSES)
    frames = []
    for shift in SHIFTS:
        new = bytearray()
        last = 0
        repl = {}
        for dc in range(nc):
            for dr in range(nr):
                tile = []
                for y in range(16):
                    row = []
                    for x in range(16):
                        fx, fy = (c0 + dc) * 16 + x, (r0 + dr) * 16 + y
                        row.append(orig(fx, fy - shift) if inside(fx, fy) else orig(fx, fy))
                    tile.append(row)
                if tile != [[orig((c0 + dc) * 16 + x, (r0 + dr) * 16 + y) for x in range(16)] for y in range(16)]:
                    repl[(c0 + dc, r0 + dr)] = rom.add_sprite_tile(tile, why="shop: shopkeeper animation", share=True)
        # the definition with those tiles' low bytes replaced by one-tile escapes (1, 0xA0, high, low)
        for (c, r), q in sorted(at.items(), key=lambda kv: kv[1]):
            if (c, r) in repl:
                off = q - p
                new += body[last:off]
                n = repl[(c, r)]
                new += bytes([1, 0xA0, n >> 8, n & 0xFF])
                last = off + 1
        new += body[last:]
        addr = rom.alloc(len(new))
        rom.data[addr:addr + len(new)] = new
        n = rom.next_frame
        rom.next_frame = n + 4
        rom.write(0x60772 + n, addr.to_bytes(4, "big"), why="frame 0x%X: shopkeeper animation" % n)
        frames.append(n)
    table = "".join("    .word 0x%X\n" % ([BASE_FRAME] + frames)[k] for k in SEQUENCE)
    src = r"""
anim:
    moveq #0,%d0
    move.l FRAME_COUNTER,%d1         | player 1 on her? (in the shop: its pointer ran lately)
    sub.l GRID_RAM+4,%d1
    cmp.l #4,%d1
    bhi 1f
    cmp.b #8,GRID_RAM
    beq 3f
1:  move.l FRAME_COUNTER,%d1         | player 2?
    sub.l GRID_RAM+8,%d1
    cmp.l #4,%d1
    bhi 2f
    cmp.b #8,GRID_RAM+1
    beq 3f
2:  clr.b RAM                        | not selected: the usual picture
    move.w #BASE_FRAME,8(%a5)
    rts
3:  moveq #0,%d0
    move.b RAM,%d0
    addq.b #1,RAM
    cmp.b #PERIOD-1,%d0              | (again every PERIOD frames while she stays selected)
    bcs 4f
    clr.b RAM
4:  divu #STEP,%d0
    move.w #BASE_FRAME,%d1
    cmp.w #SEQ_LEN,%d0               | (past the end: the usual picture)
    bcc 5f
    add.w %d0,%d0
    lea seq(%pc),%a0
    move.w (%a0,%d0.w),%d1
5:  move.w %d1,8(%a5)
    rts
seq:
TABLE"""
    for k, v in (("FRAME_COUNTER", "0x%X" % FRAME_COUNTER), ("GRID_RAM", "0x%X" % GRID_RAM),
                 ("BASE_FRAME", "0x%X" % BASE_FRAME), ("SEQ_LEN", str(len(SEQUENCE))), ("PERIOD", str(PERIOD)),
                 ("STEP", str(STEP)), ("RAM", "0x%X" % RAM), ("TABLE", table)):
        src = src.replace(k, v)
    code = rom.place_code(src, why="shop: shopkeeper animation")
    rom.write(CODE_FIELD, code.to_bytes(4, "big"), expect=(0x1FA34).to_bytes(4, "big"),
              why="shop: the shopkeeper's object runs the animation")
