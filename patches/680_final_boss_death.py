NAME = "final-boss-death"
DESCRIPTION = "Final boss: Blue's answer bubbles appear with their text (YES / NO's narrower); at his death he screams AHHHH and the dust bank covers his cape"

# As the final boss is beaten he screams (SCREAM_AT: move.w #SCREAM_WAS,d0 ; jsr the sound request - a Japanese voice
# clip) and sinks into a bank of billowing dust: 9 puff objects (code PUFF), 8 px apart, spawned from inline templates
# (PUFF_TEMPLATES: y, x, the code, the first frame ...). Now he screams SCREAM (the English-sounding AHHHH), and the
# bank is SHIFT px further left: his cape poked out past its left end as he sank.
# With one hit left he asks a YES / NO question: Blue's answer bubble (QUESTION_TEMPLATE, an inline object template
# whose frame is BUBBLE) is 11 tiles wide - the width his other answer (YOU'RE FINISHED! / I SURRENDER...) needs. The
# question's gets a narrower copy: BUBBLE's columns KEEP (its left edge, the middle up to the tail, the right edge).
# Both answer bubbles appeared empty while the boss's line typed, their text ~2/3 s later: now each is blank (frame 0)
# till the answers are up - the top answer's first letter at TEXT_AT on the fix layer, no longer BLANK (not the cursor:
# it moves down to the other answer) - each frame of its object
# (ANSWER's code, wrapped through the templates' code fields ANSWER_TEMPLATES).
# While the YES / NO bubble is up (from its creation), Blue ignores the stick - pressing Down to NO made him duck: its
# code sets ANSWERING each frame (not the opening answer's: Blue is walked into the hall then, by the game moving his
# stick, and the question comes up before he's there), and his direction check (DIRECTIONS: the stick's direction,
# 0x103908, to
# an action; Down ducks) acts as if the stick were still while it's set (counted down there, so it ends with the
# bubble).
# (Tried and dropped: the scream played again a few frames later as an echo; the puffs' frames there and back -
# smoother spacing, but the billow rocked.)
SCREAM_AT = 0x36712            # (the move.w's operand)
SCREAM_WAS, SCREAM = 0x6E, 0x74
PUFF = 0x36F3C
PUFF_TEMPLATES = 0x36DC2       # the first's y, x (then one every 0x2A bytes, x 0x400 - 8 px - apart)
TEMPLATE_STEP, PUFFS = 0x2A, 9
SHIFT = 8                      # px left (x: 128 a px)
QUESTION_TEMPLATE = 0x36BAC    # (the YES / NO answer bubble's frame, in its template; the other answer's: 0x36202)
BUBBLE = 0x345C                # 11 x 4 tiles: left edge, 4 middle, the tail's, 4 middle, right edge (with flips)
KEEP = [0, 1, 2, 3, 4, 5, 10]
ANSWER = 0x294CA               # the answer bubble's object code (the cursor and the choice)
ANSWER_TEMPLATES = [0x361FE, 0x36BA8]   # (its code field in each template: the opening answer, the YES / NO)
DIRECTIONS = 0x3E794           # btst #4,0x3909(a6) ; beq ... - Blue's stick to an action (d0 0: none)
DIRECTIONS_REST = 0x3E79A
ANSWERING = 0x10EA92           # a byte (spare RAM): frames left of Blue ignoring the stick
TEXT_AT, BLANK = 0x708E, 0x520     # (fix: column 4, row 14 - the Y of YES and of YOU'RE; a fix tile word's low 12 bits)
FRAME_TABLE = 0x60772


def frame_grid(rom, frame):
    """A frame's (columns, rows, palette, [column][row] = (tile or None, flip bits or 0)), as the game reads it."""
    d, p = rom.data, rom.u32(FRAME_TABLE + frame)
    cols, rows, _, palette, hi = d[p:p + 5]
    q, grid = p + 5, []
    for c in range(cols + 1):
        grid.append([])
        for r in range(rows + 1):
            b, flips = d[q], 0
            q += 1
            if b == 1:                       # 1, attribute (0x40: a palette, 0x20: a high byte follow), low byte
                a = d[q]
                q += 1
                assert not a & 0x40
                if a & 0x20:
                    hi = d[q]
                    q += 1
                b, flips = d[q], a & 0x9F
                q += 1
            grid[-1].append(((hi << 8) | b if b else None, flips))
    assert d[q] == 0xFF
    return cols + 1, rows + 1, palette, grid


def frame_bytes(grid, palette):
    """A definition for grid ([column][row] = (tile or None, flip bits)) in the game's per-tile form."""
    hi = next(t for col in grid for t, _ in col if t is not None) >> 8
    body = bytearray([len(grid) - 1, len(grid[0]) - 1, 0, palette, hi])
    for col in grid:
        for tile, flips in col:
            if tile is None:
                body.append(0)
            elif not flips and tile >> 8 == hi and (tile & 0xFF) > 1:
                body.append(tile & 0xFF)
            else:
                attr = flips | (0x20 if tile >> 8 != hi else 0)
                body += bytes([1, attr]) + (bytes([tile >> 8]) if tile >> 8 != hi else b"") + bytes([tile & 0xFF])
                hi = tile >> 8
    body.append(0xFF)
    return bytes(body)


def apply(rom):
    cols, rows, palette, grid = frame_grid(rom, BUBBLE)
    assert (cols, rows) == (11, 4)
    narrow = [grid[c] for c in KEEP]
    body = frame_bytes(narrow, palette)
    at = rom.alloc(len(body))
    rom.data[at:at + len(body)] = body
    frame = rom.next_frame
    rom.next_frame += 4
    rom.write(FRAME_TABLE + frame, at.to_bytes(4, "big"), why="frame 0x%X -> Blue's narrower answer bubble" % frame)
    rom.write(QUESTION_TEMPLATE, frame.to_bytes(2, "big"), expect=BUBBLE.to_bytes(2, "big"),
              why="final boss's YES / NO: Blue's answer bubble %d tiles wide (was 11)" % len(KEEP))
    for n, template in enumerate(ANSWER_TEMPLATES):
        assert rom.u32(template) == ANSWER, hex(template)
        shown = frame if template + 4 == QUESTION_TEMPLATE else rom.u16(template + 4)
        wrap = rom.place_code("""
%(still)s    move.w #0x%(text)X,0x3C0000         | the answers up yet? (the top one's first letter)
    move.w 0x3C0002,%%d0
    andi.w #0x0FFF,%%d0
    cmpi.w #0x%(blank)X,%%d0
    bne 1f
    clr.w 8(%%a5)                       | not yet: the bubble blank
    jmp 0x%(answer)X
1:  move.w #0x%(frame)X,8(%%a5)
    jmp 0x%(answer)X
""" % {"still": "    move.b #2,0x%X           | (Blue ignores the stick: the question's up)\n" % ANSWERING
                if template + 4 == QUESTION_TEMPLATE else "", "text": TEXT_AT, "blank": BLANK, "answer": ANSWER, "frame": shown},
            why="final boss: Blue's answer bubble %d shown with its text" % n)
        rom.write(template, wrap.to_bytes(4, "big"), expect=ANSWER.to_bytes(4, "big"),
                  why="final boss: Blue's answer bubble %d through its wrapper" % n)
    still = rom.place_code("""
    tst.b 0x%(answering)X
    beq 1f
    subq.b #1,0x%(answering)X
    moveq #0,%%d0                       | (a question's up: the stick as if still)
    rts
1:  btst #4,0x3909(%%a6)
    jmp 0x%(rest)X
""" % {"answering": ANSWERING, "rest": DIRECTIONS_REST}, why="Blue ignores the stick while he answers the final boss")
    rom.write(DIRECTIONS, bytes.fromhex("4EF9") + still.to_bytes(4, "big"), expect=bytes.fromhex("082E00043909"),
              why="Blue's stick: still while he answers the final boss")
    rom.write(SCREAM_AT, SCREAM.to_bytes(2, "big"), expect=SCREAM_WAS.to_bytes(2, "big"),
              why="final boss's death: he screams AHHHH")
    for i in range(PUFFS):
        at = PUFF_TEMPLATES + TEMPLATE_STEP * i
        assert rom.u32(at + 4) == PUFF, hex(at)
        x = rom.u16(at + 2)
        assert x == 0xA000 + 0x400 * i, hex(x)
        rom.write(at + 2, (x - SHIFT * 128).to_bytes(2, "big"), expect=x.to_bytes(2, "big"),
                  why="final boss's dust: puff %d %d px left" % (i, SHIFT))
