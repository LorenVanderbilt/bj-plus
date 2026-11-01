NAME = "turn-down-exit"
DESCRIPTION = "NPC rooms: turning down the riddle man's riddles or Red's duel leaves at once; after the riddles, a moment before the fade; the boatman throws you out when you can't pay"

# Turning the riddle man down a third time, or refusing Red's duel ("I GUESS I'M A COWARD."), ends the talk through
# 0x25ABE. The room then waits before fading out, and npc-wait turned that wait into a wait for a button so a last
# line can be read. Here the last thing on screen is the answer just chosen, so the room looked stuck.
#
# Those choices now go through `refused`, which runs the original action and sets SKIP. Each room's wait
# (move.w #30,d0 ; jsr <npc-wait>) goes through its own routine: if SKIP is set it clears it and waits one frame,
# otherwise it waits as before. The riddle man is the exception. His last line is already closed by the press that
# ends the talk, so npc-wait would wait up to 10 s for a second press. His room waits its 30 frames plus LINGER
# instead, so his last line stays up a moment whether the quiz was won or lost.
#
# SKIP is cleared as each room starts: the room set-up's 8 bytes at START run as before, then the clear.
#
# The boatman's NO FLOWERS, NO BOAT, GET OUT! (text-fixes) ends the talk with its end-of-text callback, 0x22502, the
# same one renting a boat uses. BOATMAN_BROKE's callback now sets SKIP first, so his room waits LINGER frames, long
# enough to read it, and then throws you out without a press. A rented boat's last line still waits for one.
ROOMS = [   # (name, choice table entry for 0x25ABE or None, START, the wait (move.w #N,d0 ; jsr npc-wait),
            #  keep npc-wait?, frames before leaving when SKIP is set)
    ("quiz", 0x266B6, 0x25A4A, 0x25AAC, False, 1),  # START: clr.l 0x786A(a6) ; clr.b 0x7861(a6)
    ("red", 0x28304, 0x27AF0, 0x27B60, True, 1),    # START: clr.b 0x7861(a6) ; clr.b 0x786F(a6)
    ("boat", None, 0x21B0A, 0x21B70, True, 60),     # START: clr.l 0x786A(a6) ; clr.b 0x7861(a6)
]
BOATMAN_BROKE = 0x22528        # lea <NO FLOWERS, NO BOAT, GET OUT!>,a0; its 0xFC callback is 0x22502
TALK_ENDS = 0x22502
REFUSE_ACTION = 0x25ABE
SKIP = 0x10E9FC              # spare RAM byte, cleared as each room starts
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
        start_at, wait_at = code + 4 + 8 * n, code + 8 + 8 * n      # the bra.w table
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
