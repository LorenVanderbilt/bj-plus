NAME = "boatman-farewell"
DESCRIPTION = "Boatman: a parting line as you leave - BON VOYAGE, LAD! after renting a boat, SUIT YOURSELF, MATEY. after NO THANKS"

# The boatman's menu handlers (the table that MENU_TABLE_REF loads, boatman-close's wrapped copy: leaf boat, mud
# boat, no thanks) end his room at once (0x22502 sets DONE) with no line after. The exception is a boat he can't be
# paid for: NO FLOWERS, NO BOAT, GET OUT! is typed out (0x2152C, after clearing the box with 0x21CD2) and ends the
# room from its callback (0xFC, 0x22502).
#
# Now, when a handler ended the room, it's undone and a parting line (FAREWELLS) is typed the same way. Its callback
# holds it for HOLD frames and then ends the room. There's no button wait, since boatman-close's PICKED stays set
# and the room closes by itself.
MENU_TABLE_REF = 0x222FC       # the operand of lea <handlers>,a1 at 0x222FA
END_ROOM = 0x22502
CLEAR_BOX, TYPE = 0x21CD2, 0x2152C
BOX_AT = 0x7092                # the fix address his lines start at
DONE = 0x107861
PICKED = 0x10EFF8              # boatman-close's flag
WAIT = 0xE858                  # waits d0 frames
HOLD = 60
FAREWELLS = [["BON VOYAGE, LAD!"], ["BON VOYAGE, LAD!"], ["SUIT YOURSELF, MATEY."]]   # leaf boat, mud boat, no thanks


def record(lines, callback):
    """Text for the text engine: the lines with 0xFE between them, then 0xFC and the callback, on an even byte."""
    text = b"\xfe".join(l.encode() for l in lines).replace(b"?", b"\x0a")
    if (len(text) + 1) % 2:
        text += b" "
    return text + b"\xfc" + callback.to_bytes(4, "big")


def apply(rom):
    end = rom.place_code("""
    move.w #%d,%%d0
    jsr 0x%X
    jmp 0x%X
""" % (HOLD, WAIT, END_ROOM), why="boatman: his parting line held, then the room ends")
    assert rom.u16(MENU_TABLE_REF - 2) == 0x43F9
    table = rom.u32(MENU_TABLE_REF)
    for n, lines in enumerate(FAREWELLS):
        was = rom.u32(table + 4 * n)
        text = record(lines, end)
        at = rom.alloc(len(text), align=2)
        rom.data[at:at + len(text)] = text
        rom.log.append("  0x%06X  %d byte(s)  boatman's parting line: %s" % (at, len(text), " / ".join(lines)))
        code = rom.place_code("""
    jsr 0x%(was)X
    tst.b 0x%(done)X
    beq 1f                              | can't pay: his line ends the room instead
    clr.b 0x%(done)X                    | the room ends after his parting line
    jsr 0x%(clear)X
    lea 0x%(text)X,%%a0
    move.w #0x%(box)X,%%d0
    jsr 0x%(type)X
1:  rts
""" % {"was": was, "done": DONE, "clear": CLEAR_BOX, "text": at, "box": BOX_AT, "type": TYPE},
            why="boatman: his parting line after pick %d" % n)
        rom.write(table + 4 * n, code.to_bytes(4, "big"), expect=was.to_bytes(4, "big"),
                  why="boatman: his menu's pick %d, then a parting line" % n)
