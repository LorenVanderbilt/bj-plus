NAME = "turn-down-exit"
DESCRIPTION = "NPC rooms: turning down the riddle man's riddles or Red's duel leaves at once; after the riddles, a moment before the fade; the boatman throws you out when you can't pay"

# Turning the riddle man down a third time, or Red's duel ("I GUESS I'M A COWARD."), ends the talk with 0x25ABE
# (from each choice table) and the room loop goes on to its wait before the fade out - which npc-wait made a wait for
# a button (for reading a last line). Here the last thing was an answer just chosen, so it looked stuck. Now those
# choices go through `refused` (the original action, then SKIP set), and each room's wait (`move.w #30,d0 ; jsr
# <npc-wait's routine>`) through its own: SKIP set - cleared, a frame; else as before - except the riddle man's,
# where the last line is already closed by a press (that press ends the talk), so npc-wait waited for a second one, up
# to 10 s: there, the room's 30 frames and LINGER more instead (the quiz lost or won: his line stays a moment).
# SKIP is cleared as each room starts (in its set-up: the 8 bytes at START, run as they were, then the clear).
# The boatman's NO FLOWERS, NO BOAT, GET OUT! (text-fixes) ends the talk with its end-of-text callback (0x22502, as
# renting a boat does): BOATMAN_BROKE's callback now sets SKIP first, so his room's wait is LINGER frames - time to
# read it - and then you're out, no press needed (a rented boat's last line still waits for one).
ROOMS = [   # (name, the choice table entry (0x25ABE) or None, START, the wait (move.w #N,d0 ; jsr npc-wait),
            #  npc-wait kept?, frames before leaving when SKIP is set)
    ("quiz", 0x266B6, 0x25A4A, 0x25AAC, False, 1),  # (START: clr.l 0x786A(a6) ; clr.b 0x7861(a6))
    ("red", 0x28304, 0x27AF0, 0x27B60, True, 1),    # (START: clr.b 0x7861(a6) ; clr.b 0x786F(a6))
    ("boat", None, 0x21B0A, 0x21B70, True, 60),     # (START: clr.l 0x786A(a6) ; clr.b 0x7861(a6))
]
BOATMAN_BROKE = 0x22528        # lea <NO FLOWERS, NO BOAT, GET OUT!>,a0 - its 0xFC callback: 0x22502 (the talk ends)
TALK_ENDS = 0x22502
REFUSE_ACTION = 0x25ABE
SKIP = 0x10E9FC              # a byte (spare RAM: may hold anything at first - cleared as a room starts)
WAIT = 0xE858                # d0 = frames
LINGER = 60


def apply(rom):
    table, rooms = "", ""
    for name, _, start, wait, keep, linger in ROOMS:
        assert rom.u16(wait) == 0x303C and rom.u16(wait + 4) == 0x4EB9, "expected npc-wait's call"
        frames, npc_wait = rom.u16(wait + 2), rom.u32(wait + 6)
        set_up = ", ".join("0x%02X" % b for b in rom.data[start:start + 8])
        after = ("    move.w #%d,%%d0\n    jmp 0x%X\n" % (frames, npc_wait)) if keep else \
                ("    move.w #%d+%d,%%d0\n    jmp 0x%X\n" % (frames, LINGER, WAIT))
        table += "    bra.w %s_start\n    bra.w %s_wait\n" % (name, name)
        rooms += r"""
%(name)s_start:
    .byte %(set_up)s
    clr.b 0x%(skip)X
    rts
%(name)s_wait:
    tst.b 0x%(skip)X
    beq 1f
    clr.b 0x%(skip)X
    move.w #%(linger)d,%%d0
    jmp 0x%(wait)X
1:
%(after)s""" % {"name": name, "set_up": set_up, "skip": SKIP, "wait": WAIT, "linger": linger, "after": after}
    code = rom.place_code(r"""
    bra.w refused
%(table)s%(rooms)s
refused:
    jsr 0x%(refuse)X
    st 0x%(skip)X
    rts
""" % {"table": table, "rooms": rooms, "refuse": REFUSE_ACTION, "skip": SKIP}, why="NPC rooms: turned down, out at once")
    for n, (name, entry, start, wait, keep, linger) in enumerate(ROOMS):
        start_at, wait_at = code + 4 + 8 * n, code + 8 + 8 * n      # (the table: bra.w each)
        if entry is not None:
            rom.write(entry, code.to_bytes(4, "big"), expect=REFUSE_ACTION.to_bytes(4, "big"),
                      why="%s: turned down - noted, so the room is left at once" % name)
        rom.write(start, bytes.fromhex("4EB9") + start_at.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  why="%s's room: its leave-at-once note cleared" % name)
        rom.write(wait, bytes.fromhex("4EB9") + wait_at.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
                  why="%s's room: its wait before leaving (none after turning down)" % name)
    # the boatman's GET OUT!: its callback sets SKIP, then ends the talk as before
    text = rom.u32(BOATMAN_BROKE)
    end = text
    while rom.data[end] not in (0xFF, 0xFC, 0xFB):
        end += 1
    assert rom.data[end] == 0xFC and rom.u32(end + 1) == TALK_ENDS, "expected the line's callback to 0x%X" % TALK_ENDS
    thrown = rom.place_code("""
    st 0x%(skip)X
    jmp 0x%(talk_ends)X
""" % {"skip": SKIP, "talk_ends": TALK_ENDS}, why="boatman: can't pay - thrown out")
    rom.write(end + 1, thrown.to_bytes(4, "big"), expect=TALK_ENDS.to_bytes(4, "big"),
              why="boatman's NO FLOWERS, NO BOAT, GET OUT!: out of the house after it")
