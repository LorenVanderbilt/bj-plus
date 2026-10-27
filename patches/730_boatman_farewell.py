NAME = "boatman-farewell"
DESCRIPTION = "Boatman: a parting line as you leave - BON VOYAGE, LAD! after renting a boat, SUIT YOURSELF, MATEY. after NO THANKS"

# The boatman's menu handlers (the table MENU_TABLE_REF's lea loads - boatman-close's copy, its wrappers: leaf boat,
# mud boat, no thanks) end his room at once (0x22502: DONE set), with no line after - but for a boat he can't pay for: NO FLOWERS, NO BOAT, GET
# OUT!, typed (0x2152C, the box cleared first: 0x21CD2) and ending the room from its callback (0xFC 0x22502). Now each
# handler, when it did end the room, takes that back and types a parting line (FAREWELLS) the same way, its callback
# holding it HOLD frames and then ending the room - no button wait (boatman-close's PICKED stays: the room closes by
# itself).
MENU_TABLE_REF = 0x222FC       # (the operand of lea <the handlers>,a1 at 0x222FA)
END_ROOM = 0x22502
CLEAR_BOX, TYPE = 0x21CD2, 0x2152C
BOX_AT = 0x7092                # (the fix address his lines start at)
DONE = 0x107861
PICKED = 0x10EFF8              # (boatman-close's)
WAIT = 0xE858                  # (d0 frames)
HOLD = 60
FAREWELLS = [["BON VOYAGE, LAD!"], ["BON VOYAGE, LAD!"], ["SUIT YOURSELF, MATEY."]]   # (leaf boat, mud boat, no thanks)


def record(lines, callback):
    """A line for the text engine: its lines (0xFE between), then 0xFC and the callback - on an even byte."""
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
    beq 1f                              | (a line instead - he can't pay: it ends the room)
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
