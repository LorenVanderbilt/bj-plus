NAME = "turn-down-exit"
DESCRIPTION = "NPC rooms: turning down the quiz grandpa's quiz or Red's duel leaves at once; after the quiz, a moment before the fade"

# Turning the quiz grandpa down a third time, or Red's duel ("I GUESS I'M A COWARD."), ends the talk with 0x25ABE
# (from each choice table) and the room loop goes on to its wait before the fade out - which npc-wait made a wait for
# a button (for reading a last line). Here the last thing was an answer just chosen, so it looked stuck. Now those
# choices go through `refused` (the original action, then SKIP set), and each room's wait (`move.w #30,d0 ; jsr
# <npc-wait's routine>`) through its own: SKIP set - cleared, a frame; else as before - except the quiz grandpa's,
# where the last line is already closed by a press (that press ends the talk), so npc-wait waited for a second one, up
# to 10 s: there, the room's 30 frames and LINGER more instead (the quiz lost or won: his line stays a moment).
# SKIP is cleared as each room starts (in its set-up: the 8 bytes at START, run as they were, then the clear).
ROOMS = [   # (name, the choice table entry (0x25ABE), START, the wait (move.w #N,d0 ; jsr npc-wait), npc-wait kept?)
    ("quiz", 0x266B6, 0x25A4A, 0x25AAC, False),     # (START: clr.l 0x786A(a6) ; clr.b 0x7861(a6))
    ("red", 0x28304, 0x27AF0, 0x27B60, True),       # (START: clr.b 0x7861(a6) ; clr.b 0x786F(a6))
]
REFUSE_ACTION = 0x25ABE
SKIP = 0x10E9FC              # a byte (spare RAM: may hold anything at first - cleared as a room starts)
WAIT_FRAME = 0xE856
WAIT = 0xE858                # d0 = frames
LINGER = 60


def apply(rom):
    table, rooms = "", ""
    for name, _, start, wait, keep in ROOMS:
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
    jmp 0x%(frame)X
1:
%(after)s""" % {"name": name, "set_up": set_up, "skip": SKIP, "frame": WAIT_FRAME, "after": after}
    code = rom.place_code(r"""
    bra.w refused
%s%s
refused:
    jsr 0x%X
    st 0x%X
    rts
""" % (table, rooms, REFUSE_ACTION, SKIP), why="NPC rooms: turned down, out at once")
    for n, (name, entry, start, wait, keep) in enumerate(ROOMS):
        start_at, wait_at = code + 4 + 8 * n, code + 8 + 8 * n      # (the table: bra.w each)
        rom.write(entry, code.to_bytes(4, "big"), expect=REFUSE_ACTION.to_bytes(4, "big"),
                  why="%s: turned down - noted, so the room is left at once" % name)
        rom.write(start, bytes.fromhex("4EB9") + start_at.to_bytes(4, "big") + bytes.fromhex("4E71"),
                  why="%s's room: its leave-at-once note cleared" % name)
        rom.write(wait, bytes.fromhex("4EB9") + wait_at.to_bytes(4, "big") + bytes.fromhex("4E714E71"),
                  why="%s's room: its wait before leaving (none after turning down)" % name)
