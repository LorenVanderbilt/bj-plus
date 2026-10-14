NAME = "boatman-close"
DESCRIPTION = "Boatman: picking a boat (or NOT NECESSARY) closes his room at once, not after a 10 s wait for a button"

# npc-wait makes each NPC room wait, after its last line, for a button press (up to 10 s) so it can be read. The
# boatman's room ends when a boat (or none) is picked from his menu - its handlers end the room (0x22502) with no
# line after - so his room sat there with an empty box, as if hung. His menu's handlers (the table at 0x224A6)
# now go through wrappers that set PICKED when the pick ended the room (a boat he can't pay for prints NO FLOWERS,
# NO BOAT, GET OUT! instead, whose callback ends it: no PICKED - turn-down-exit gives that line its own pause). With
# PICKED his room's wait is only its own (30 frames, as the original); after a line the button wait stays.
ROOM_WAIT = 0x21B74     # jsr npc_wait  (npc-wait's; its `move.w #30,d0` before it)
WAIT = 0xE858
MENU_TABLE_REF = 0x222FC    # lea 0x224A6,a1 (the menu's handlers: leaf boat, mud boat, none)
MENU_TABLE = 0x224A6
DONE = 0x107861
PICKED = 0x10EFF8       # a byte (spare RAM)


def apply(rom):
    old = bytes(rom.data[ROOM_WAIT:ROOM_WAIT + 6])
    if old[:2] != bytes.fromhex("4EB9"):
        raise SystemExit("boatman-close: no jsr at 0x%X" % ROOM_WAIT)
    npc_wait = int.from_bytes(old[2:], "big")
    handlers = [int.from_bytes(rom.data[MENU_TABLE + 4 * i:MENU_TABLE + 4 * i + 4], "big") for i in range(3)]
    wraps = [rom.place_code(
        "    st 0x%X\n"
        "    jsr 0x%X\n"
        "    tst.b 0x%X\n"
        "    bne.s 1f\n"
        "    clr.b 0x%X                       | (a line instead: it ends the room)\n"
        "1:  rts\n" % (PICKED, h, DONE, PICKED), why="boatman: his menu's pick %d, noted" % i)
        for i, h in enumerate(handlers)]
    table = rom.alloc(12, align=2)
    rom.data[table:table + 12] = b"".join(w.to_bytes(4, "big") for w in wraps)
    rom.write(MENU_TABLE_REF, table.to_bytes(4, "big"), expect=MENU_TABLE.to_bytes(4, "big"),
              why="boatman: his menu's handlers, through the wrappers")
    at = rom.place_code(
        "    tst.b 0x%X\n"
        "    beq.s 1f\n"
        "    clr.b 0x%X\n"
        "    jmp 0x%X                         | (a boat, or none, was picked: no line to read)\n"
        "1:  jmp 0x%X\n" % (PICKED, PICKED, WAIT, npc_wait),
        why="boatman: no button wait when his menu closed the room")
    rom.write(ROOM_WAIT, bytes.fromhex("4EB9") + at.to_bytes(4, "big"), expect=old,
              why="boatman: his room's wait - a button wait only after a line")
