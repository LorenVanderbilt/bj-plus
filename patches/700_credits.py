NAME = "credits"
DESCRIPTION = "Ending credits: SOUND EFFECTS (was SOUND EFFECT), HARDWARE (was HARD WEARER), and a PLUS VERSION credit"

# The ending's staff roll (0x25330) steps through STEPS: at each frame count in TIMES (0x1078F0 counting) it calls the
# next routine in ROUTINES (0x1078B0 the step) - each credit clears the text layer (0x9FBE), prints its role and name
# with the inline text printer (0x9FE6: a fix address word, 0xFC 0x55, the text; 0xFE, an address, more; 0xFF) and
# draws the Japanese name from tiles (0x25444); the last two are THE END and the roll's end. Both tables are copied
# (LEAS: the absolute leas that load them) with:
#   * PLUS_CREDIT, a new credit before THE END (THE END and the end a step later: 256 frames, ~4 s);
#   * the SOUND EFFECT credit (SOUND_CREDIT) replaced by a copy that prints SOUND EFFECTS, then carries on in the
#     original after its text (the Japanese name);
# and HARD WEARER (the Japanese ハードウェア, "hardware") reads HARDWARE, in place.
TIMES, ROUTINES, STEPS = 0x253E4, 0x25404, 16
LEAS = [(0x253BC, TIMES), (0x253D4, ROUTINES)]   # (the lea's address operand, what it loads)
CLEAR, PRINT = 0x9FBE, 0x9FE6
SOUND_CREDIT = 0x257B2         # jsr CLEAR ; jsr PRINT ; its text ... ; then the Japanese name
SOUND_WAS, SOUND = b"SOUND EFFECT", b"SOUND EFFECTS"
HARD_AT, HARD_WAS, HARD = 0x25810, b"HARD WEARER", b"HARDWARE   "
BEFORE_THE_END = 14            # (the step PLUS_CREDIT goes in at)
ROLE_AT, NAME_AT = 0x724A, 0x724D   # (as the other credits: the role at column 18 row 10; a 20-letter name, column
                                    # 18 row 13)
PLUS_CREDIT = (b"PLUS VERSION", b"LOREN VANDERBILT III")


def record(parts):
    """An inline text record for PRINT: (fix address, text) pairs; padded to an even length."""
    out = bytearray()
    for n, (addr, text) in enumerate(parts):
        out += (bytes([0xFE]) if n else b"") + addr.to_bytes(2, "big") + (b"\xFC\x55" if not n else b"") + text
    out.append(0xFF)
    if len(out) % 2:
        out.append(0xFF)
    return bytes(out)


def as_bytes(b):
    return ",".join("0x%02X" % v for v in b)


def apply(rom):
    assert bytes(rom.data[HARD_AT:HARD_AT + len(HARD_WAS)]) == HARD_WAS and len(HARD) == len(HARD_WAS)
    rom.write(HARD_AT, HARD, expect=HARD_WAS, why="credits: HARDWARE (was HARD WEARER)")

    # SOUND EFFECTS: a copy of the credit's start with the longer text, then on in the original after its record
    assert rom.u16(SOUND_CREDIT) == 0x4EB9 and rom.u32(SOUND_CREDIT + 2) == CLEAR
    assert rom.u16(SOUND_CREDIT + 6) == 0x4EB9 and rom.u32(SOUND_CREDIT + 8) == PRINT
    text_at = SOUND_CREDIT + 12
    end = rom.data.index(b"\xFF", text_at)
    rest = end + 1 + ((end + 1) % 2)                   # (the record padded to an even length)
    old = bytes(rom.data[text_at:end])
    assert old == b"\x72\x4A\xFC\x55" + SOUND_WAS + b"\xFE\x72\xCD" + b"HIDEKI YAMAMOTO", old
    sound = rom.place_code("""
    jsr 0x%(clear)X
    jsr 0x%(print)X
    .byte %(text)s
    jmp 0x%(rest)X
""" % {"clear": CLEAR, "print": PRINT, "rest": rest,
       "text": as_bytes(record([(0x724A, SOUND), (0x72CD, b"HIDEKI YAMAMOTO")]))},
        why="credits: SOUND EFFECTS")

    plus = rom.place_code("""
    jsr 0x%(clear)X
    jsr 0x%(print)X
    .byte %(text)s
    rts
""" % {"clear": CLEAR, "print": PRINT, "text": as_bytes(record([(ROLE_AT, PLUS_CREDIT[0]), (NAME_AT, PLUS_CREDIT[1])]))},
        why="credits: PLUS VERSION")

    times = [rom.u16(TIMES + 2 * i) for i in range(STEPS)]
    routines = [rom.u32(ROUTINES + 4 * i) for i in range(STEPS)]
    assert times == [0x10] + [0x100 * i for i in range(1, STEPS)], [hex(t) for t in times]
    assert SOUND_CREDIT in routines
    routines = [sound if r == SOUND_CREDIT else r for r in routines]
    step = times[BEFORE_THE_END] - times[BEFORE_THE_END - 1]
    times = times[:BEFORE_THE_END] + [times[BEFORE_THE_END]] + [t + step for t in times[BEFORE_THE_END:]]
    routines = routines[:BEFORE_THE_END] + [plus] + routines[BEFORE_THE_END:]
    tables = b"".join(t.to_bytes(2, "big") for t in times) + b"".join(r.to_bytes(4, "big") for r in routines)
    at = rom.alloc(len(tables), align=2)
    rom.data[at:at + len(tables)] = tables
    rom.log.append("  0x%06X  %d byte(s)  credits: the staff roll's times and routines (%d steps)" % (at, len(tables), len(times)))
    for operand, was in LEAS:
        new = at if was == TIMES else at + 2 * len(times)
        rom.write(operand, new.to_bytes(4, "big"), expect=was.to_bytes(4, "big"), why="credits: the new %s" % (
            "times" if was == TIMES else "routines"))
