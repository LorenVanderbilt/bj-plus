NAME = "quiz-room-exit"
DESCRIPTION = "Quiz grandpa's house: turning his quiz down a third time leaves at once; after the quiz, a moment before the fade"

# Turned down a third time, the quiz grandpa lets you go: the choice's action (0x25ABE, from the choice table at
# 0x266B6) ends the talk, and the room loop (0x25A5E) goes on to its wait before the fade out - which npc-wait made
# a wait for a button (for reading a last line). Here the last thing was an answer just chosen, so it looked stuck.
# Now that choice goes through `refused` (the original action, then SKIP set), and the room's wait (0x25AAC:
# move.w #30,d0 ; jsr npc-wait's routine) through `room_wait`: SKIP set - cleared, a frame; else the room's own 30
# frames and LINGER more - but not npc-wait's wait for a press: here the last line is already closed by a press (that
# press ends the talk), so it waited for a second one, up to 10 s (the quiz lost or won: his line stays a moment).
REFUSE_ENTRY = 0x266B6       # the choice table's first entry (I'M SURE.): 0x25ABE
REFUSE_ACTION = 0x25ABE
ROOM_WAIT = 0x25AAC          # move.w #30,d0 ; jsr <npc-wait's routine>
SKIP = 0x10E9FC              # a byte (spare RAM: may hold anything at first - cleared as the room starts, ROOM_START)
ROOM_START = 0x25A4A         # clr.l 0x786A(a6) ; clr.b 0x7861(a6) - the room loop's set-up
WAIT_FRAME = 0xE856
WAIT = 0xE858                # d0 = frames
LINGER = 60


def apply(rom):
    assert rom.u16(ROOM_WAIT) == 0x303C and rom.u16(ROOM_WAIT + 4) == 0x4EB9, "expected npc-wait's call"
    frames = rom.u16(ROOM_WAIT + 2)
    code = rom.place_code(r"""
    bra.w refused
    bra.w room_wait
    bra.w room_start
room_wait:
    tst.b 0x%(skip)X
    beq 1f
    clr.b 0x%(skip)X
    jmp 0x%(frame)X
1:  move.w #%(frames)d+%(linger)d,%%d0
    jmp 0x%(frames_wait)X
refused:
    jsr 0x%(action)X
    st 0x%(skip)X
    rts
room_start:
    clr.l 0x786A(%%a6)
    clr.b 0x7861(%%a6)
    clr.b 0x%(skip)X
    rts
""" % {"skip": SKIP, "frame": WAIT_FRAME, "frames": frames, "action": REFUSE_ACTION,
       "linger": LINGER, "frames_wait": WAIT},
        why="quiz grandpa's house: turned down, out at once")
    rom.write(REFUSE_ENTRY, code.to_bytes(4, "big"), expect=REFUSE_ACTION.to_bytes(4, "big"),
              why="quiz grandpa: turned down a third time - noted, so the house is left at once")
    rom.write(ROOM_START, bytes.fromhex("4EB9") + (code + 8).to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("42AE786A422E7861"), why="quiz grandpa's house: its leave-at-once note cleared")
    rom.write(ROOM_WAIT, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              why="quiz grandpa's house: its wait before leaving (none after turning him down)")
