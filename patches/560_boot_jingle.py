NAME = "boot-jingle"
DESCRIPTION = "The eyecatcher's jingle (the BIOS's sound code 2) played as 3 Count Bout plays it: its instruments and its echoes"

# At power-on the BIOS asks the game's sound driver (the Z80 in the M1 ROM) for sound code 2: the eyecatcher jingle,
# the same melody in every game but with each game's own instruments. Blue's Journey's driver plays it from streams
# at 0x586-0x6C8: two channels of the long-note melody on voice 106 (3F 6A), and the fast arpeggio on voice 8
# (3F 08). A voice is a 40-byte record at VOICES + 40 * n. For each operator in turn (the chip's OP1, OP2, OP3, OP4,
# at registers +0, +8, +4, +C) it holds attack, decay, sustain rate, release, sustain level, total level, key scale,
# multiple and detune, followed by feedback, algorithm, the L/R byte and 0xFF.
#
# Voices 106 and 8 are also used by the game's music, so the jingle gets copies of 3 Count Bout's two voices in two
# unused slots (FREE: no music or sound effect loaded them when every code was played through).
VOICES = 0xB77B            # the voice table; the driver reads its base from 0x020A
FREE = {"melody": 129, "bell": 130}
# 3 Count Bout's voices as it writes them: one channel's registers (0x30 + 4 * operator slot and so on) and B0
MELODY_VOICE = {0x30: 0x33, 0x34: 0x74, 0x38: 0x78, 0x3C: 0x30, 0x40: 0x15, 0x44: 0x40, 0x48: 0x14, 0x4C: 0x14,
          0x50: 0x0F, 0x54: 0x0F, 0x58: 0x0F, 0x5C: 0x0F, 0x60: 0x0C, 0x64: 0x0C, 0x68: 0x0C, 0x6C: 0x05,
          0x70: 0x06, 0x74: 0x06, 0x78: 0x05, 0x7C: 0x00, 0x80: 0x07, 0x84: 0x97, 0x88: 0x17, 0x8C: 0x27, 0xB0: 0x04}
BELL_VOICE = {0x30: 0x00, 0x34: 0x06, 0x38: 0x00, 0x3C: 0x01, 0x40: 0x14, 0x44: 0x1A, 0x48: 0x22, 0x4C: 0x22,
        0x50: 0x19, 0x54: 0xD9, 0x58: 0x59, 0x5C: 0x59, 0x60: 0x02, 0x64: 0x02, 0x68: 0x06, 0x6C: 0x0C,
        0x70: 0x0A, 0x74: 0x09, 0x78: 0x0A, 0x7C: 0x0F, 0x80: 0x14, 0x84: 0x02, 0x88: 0x15, 0x8C: 0xA5, 0xB0: 0x0C}
LR = 0xC0                  # both speakers; the streams pan as they play
TEMPO = 0x88               # the jingle's own: a 16th is ~6.5 frames, as in 3 Count Bout
# The jingle is rebuilt note for note as 3 Count Bout plays it, from its YM2610 writes logged in MAME (MVS set): the
# melody and the bell arpeggio. Each note is struck loud and then made quieter while it rings, by keying it on again
# without a new attack, a 32nd later for the bell and step by step for the melody's long notes. The bell pans left,
# centre, right, centre. Each part is doubled on a second channel a moment later, with the melody's double 2 levels
# quieter.
#
# The driver's streams are MML-like (dispatched at 0xD678): ? voice, T tempo, V volume (a carrier's level is
# 0x7F - V), O octave (block), A-G a note (# for sharp), length bytes (0x20 a 32nd, 0x08 an 8th, . dotted), R rest,
# Q gate, l / s / r pan, d hi lo a frequency without a new attack (0xDAFF: key on without key off, a slide), and 0xFF
# to end. MELODY and BELL list the events (frame, MIDI note, carrier level, L/R), with the pitch written just after
# the key on. The doubles start with a short rest (DOUBLE_DELAYS). The bell's double is its own stream entered early;
# the melody's is a copy DOUBLE_QUIETER levels down at DOUBLE_AT, since there's no room for a bell copy. The rest go
# at STREAMS_AT (free space, 0xFF in RAM), and the jingle's stream table (POINTERS: melody, its double, bell, its
# double) points at them.
POINTERS = 0x240
STREAMS_AT = 0xF48C            # free up to 0xF800; this window shows the same ROM bytes while the jingle plays
FRAMES_PER_32ND = 3.27
DOUBLE_AT = 0x014B             # free from after FINE_SLIDE to 0x0200
DOUBLE_DELAYS = {"melody": 0x40, "bell": 0x30}   # a 64th and a triplet 32nd (~2 frames), so the opening swells as
                                                 # in 3 Count Bout
FNUMS = 0xE745 + 0x20          # the driver's frequency table: C, then 8 bytes a semitone
DOUBLE_QUIETER = 2
LAST_LENGTH = 0x08
# The driver keys a note off when its gate runs out (0xDB2C: Q 0 is a tick before the end, Q 1-6 are fractions of
# it), which made the slides (d) strike again. Q 0xFF, unused by any song, now means no gate, so a note sounds until
# the next strike or the end. GATE_CALL (ld a,(ix+0x2B) ; and a) calls NO_GATE, which answers as before, or for 0xFF
# stores a gate of 0 that is never counted down and returns from 0xDB2C itself. The jingle's streams set it.
#
# 3 Count Bout detunes each doubled part against its twin, with the double about 6 frequency units flatter, for a
# chorus. The doubles' prefixes set the driver's fine tune (g, added to a note's frequency) to DETUNE, which the
# twins never run. Slides (d, a raw frequency) ignored the fine tune, so SLIDE_CALL (call 0xDA54 in d's handler) now
# goes through FINE_SLIDE, which adds it first. The streams end with g 0 so nothing after the jingle is detuned.
DETUNE = -6
MELODY_TUNE = (2, -4)          # the melody's twins have their own streams, for 3 Count Bout's exact pitches
SLIDE_CALL = 0xDB0F
FINE_SLIDE = 0x0134            # after NO_GATE
FINE_SLIDE_CODE = bytes.fromhex(
    "dd7e39"      # ld a,(ix+0x39)   the fine tune (signed)
    "6f"          # ld l,a
    "17"          # rla
    "9f"          # sbc a,a
    "67"          # ld h,a           sign-extended
    "dd4e27"      # ld c,(ix+0x27)   the slide's frequency (low, high)
    "dd4626"      # ld b,(ix+0x26)
    "09"          # add hl,bc
    "dd7527"      # ld (ix+0x27),l
    "dd7426"      # ld (ix+0x26),h
    "c354da")     # jp 0xDA54        writes the frequency, as before
GATE_CALL = 0xDB33
NO_GATE = 0x0120               # free (0xFF) in the always-mapped first window
NO_GATE_CODE = bytes.fromhex(
    "dd7e2b"      # ld a,(ix+0x2B)
    "feff"        # cp 0xFF
    "2802"        # jr z,+2
    "a7"          # and a          as before: Z for Q 0
    "c9"          # ret
    "e1"          # pop hl         the call's return
    "dd362c00"    # ld (ix+0x2C),0
    "dd362d00"    # ld (ix+0x2D),0
    "d1"          # pop de         0xDB2C's push
    "c9")         # ret            to 0xDB2C's caller
MELODY = [   # (frame, MIDI note, carrier level, L/R)
    (0, 91, 0x14, 0xC0), (19, 91, 0x1C, 0xC0), (39, 88, 0x14, 0xC0), (58, 88, 0x1C, 0xC0), (78, 95, 0x14, 0xC0),
    (91, 95, 0x1C, 0xC0), (104, 93, 0x14, 0xC0), (117, 93, 0x16, 0xC0), (130, 93, 0x18, 0xC0), (143, 93, 0x1A, 0xC0),
    (156, 93, 0x1C, 0xC0), (170, 93, 0x1E, 0xC0), (183, 93, 0x20, 0xC0), (196, 93, 0x22, 0xC0), (209, 96, 0x14, 0xC0),
    (228, 96, 0x1C, 0xC0), (248, 95, 0x14, 0xC0), (268, 95, 0x1C, 0xC0), (287, 91, 0x14, 0xC0), (300, 91, 0x1C, 0xC0),
    (314, 93, 0x14, 0xC0), (327, 93, 0x17, 0xC0), (340, 93, 0x1A, 0xC0), (353, 93, 0x1D, 0xC0), (366, 93, 0x20, 0xC0),
    (379, 93, 0x23, 0xC0), (392, 93, 0x26, 0xC0), (405, 93, 0x29, 0xC0),
]
BELL = [   # (frame, MIDI note, carrier level, L/R)
    (0, 79, 0x1A, 0xC0), (3, 79, 0x22, 0xC0), (6, 84, 0x1A, 0xC0), (9, 84, 0x22, 0xC0), (13, 86, 0x1A, 0x40),
    (16, 86, 0x22, 0x40), (19, 89, 0x1A, 0x40), (22, 89, 0x22, 0x40), (26, 91, 0x1A, 0xC0), (29, 91, 0x22, 0xC0),
    (32, 89, 0x1A, 0xC0), (35, 89, 0x22, 0xC0), (39, 86, 0x1A, 0x80), (42, 86, 0x22, 0x80), (45, 84, 0x1A, 0x80),
    (48, 84, 0x22, 0x80), (52, 86, 0x1A, 0xC0), (55, 86, 0x22, 0xC0), (58, 79, 0x1A, 0xC0), (62, 79, 0x22, 0xC0),
    (65, 84, 0x1A, 0x40), (68, 84, 0x22, 0x40), (71, 86, 0x1A, 0x40), (75, 86, 0x22, 0x40), (78, 86, 0x1A, 0xC0),
    (81, 86, 0x22, 0xC0), (85, 79, 0x1A, 0xC0), (88, 79, 0x22, 0xC0), (91, 84, 0x1A, 0x80), (94, 84, 0x22, 0x80),
    (98, 86, 0x1A, 0x80), (101, 86, 0x22, 0x80), (104, 81, 0x1A, 0xC0), (107, 81, 0x22, 0xC0), (111, 86, 0x1A, 0xC0),
    (114, 86, 0x22, 0xC0), (117, 88, 0x1A, 0x40), (121, 88, 0x22, 0x40), (124, 91, 0x1A, 0x40), (127, 91, 0x22, 0x40),
    (130, 93, 0x1A, 0xC0), (134, 93, 0x22, 0xC0), (137, 91, 0x1A, 0xC0), (140, 91, 0x22, 0xC0), (143, 88, 0x1A, 0x80),
    (147, 88, 0x22, 0x80), (150, 86, 0x1A, 0x80), (153, 86, 0x22, 0x80), (157, 88, 0x1A, 0xC0), (160, 88, 0x22, 0xC0),
    (163, 81, 0x1A, 0xC0), (166, 81, 0x22, 0xC0), (170, 86, 0x1A, 0x40), (173, 86, 0x22, 0x40), (176, 88, 0x1A, 0x40),
    (179, 88, 0x22, 0x40), (183, 88, 0x1A, 0xC0), (186, 88, 0x22, 0xC0), (189, 81, 0x1A, 0xC0), (192, 81, 0x22, 0xC0),
    (196, 86, 0x1A, 0x80), (199, 86, 0x22, 0x80), (202, 88, 0x1A, 0x80), (206, 88, 0x22, 0x80), (209, 84, 0x1A, 0xC0),
    (212, 84, 0x22, 0xC0), (215, 88, 0x1A, 0xC0), (219, 88, 0x22, 0xC0), (222, 91, 0x1A, 0x40), (225, 91, 0x22, 0x40),
    (229, 94, 0x1A, 0x40), (232, 94, 0x22, 0x40), (235, 96, 0x1A, 0xC0), (238, 96, 0x22, 0xC0), (242, 94, 0x1A, 0xC0),
    (245, 94, 0x22, 0xC0), (248, 91, 0x1A, 0x80), (251, 91, 0x22, 0x80), (255, 88, 0x1A, 0x80), (258, 88, 0x22, 0x80),
    (261, 94, 0x1A, 0xC0), (264, 94, 0x22, 0xC0), (268, 84, 0x1A, 0xC0), (271, 84, 0x22, 0xC0), (274, 88, 0x1A, 0x40),
    (278, 88, 0x22, 0x40), (281, 91, 0x1A, 0x40), (284, 91, 0x22, 0x40), (287, 94, 0x1A, 0xC0), (291, 94, 0x22, 0xC0),
    (294, 84, 0x1A, 0xC0), (297, 84, 0x22, 0xC0), (301, 88, 0x1A, 0x80), (304, 88, 0x22, 0x80), (307, 91, 0x1A, 0x80),
    (310, 91, 0x22, 0x80), (314, 81, 0x1A, 0xC0), (317, 81, 0x22, 0xC0), (320, 86, 0x1C, 0xC0), (323, 86, 0x24, 0xC0),
    (327, 88, 0x1E, 0x40), (330, 88, 0x26, 0x40), (333, 93, 0x20, 0x40), (336, 93, 0x28, 0x40), (340, 81, 0x22, 0xC0),
    (343, 81, 0x2A, 0xC0), (346, 86, 0x24, 0xC0), (350, 86, 0x2C, 0xC0), (353, 88, 0x26, 0x80), (356, 88, 0x2E, 0x80),
    (359, 93, 0x28, 0x80), (363, 93, 0x30, 0x80), (366, 81, 0x2A, 0xC0), (369, 81, 0x32, 0xC0), (373, 86, 0x2C, 0xC0),
    (376, 86, 0x34, 0xC0), (379, 88, 0x2E, 0x40), (382, 88, 0x36, 0x40), (386, 93, 0x30, 0x40), (389, 93, 0x38, 0x40),
    (392, 81, 0x32, 0xC0), (395, 81, 0x39, 0xC0), (399, 86, 0x34, 0xC0), (402, 86, 0x39, 0xC0), (405, 88, 0x36, 0x80),
    (409, 88, 0x39, 0x80), (412, 93, 0x38, 0x80), (415, 93, 0x39, 0x80),
]


def record(regs):
    """A voice record (40 bytes) from one channel's register values."""
    out = []
    for slot in (0, 8, 4, 12):
        dt_mul, tl, ks_ar = regs[0x30 + slot], regs[0x40 + slot], regs[0x50 + slot]
        dr, sr, sl_rr = regs[0x60 + slot], regs[0x70 + slot], regs[0x80 + slot]
        out += [ks_ar & 0x1F, dr & 0x1F, sr & 0x1F, sl_rr & 0x0F, sl_rr >> 4, tl & 0x7F, ks_ar >> 6, dt_mul & 0x0F,
                dt_mul >> 4]
    return bytes(out + [regs[0xB0] >> 3 & 7, regs[0xB0] & 7, LR, 0xFF])


def mml(rom, voice, events, tempo=None, bell=False):
    """The driver's stream for a list of events."""
    out = bytearray([0x3F, voice, 0x51, 0xFF] + ([0x54, tempo] if tempo else []))
    octave = length = level = pan = None
    for i, (frame, note, tl, lr) in enumerate(events):
        if i + 1 < len(events):
            gap = 1 if bell else round((events[i + 1][0] - frame) / FRAMES_PER_32ND)
        else:
            gap = None
        code = {1: [0x20], 4: [0x08], 6: [0x08, 0x2E], None: [LAST_LENGTH]}[gap]
        if code != length:
            out += bytes(code)
            length = code
        if level != 0x7F - tl:
            level = 0x7F - tl
            out += bytes([0x56, level])
        if lr != pan:
            pan = lr
            out += bytes([{0x80: 0x6C, 0xC0: 0x73, 0x40: 0x72}[lr]])
        struck = i == 0 or tl < events[i - 1][2]
        o = note // 12 - 2
        if o != octave:
            octave = o
            out += bytes([0x4F, o])
        name = "C C# D D# E F F# G G# A A# B".split()[note % 12]
        if struck:
            out += name[0].encode() + (b"#" if "#" in name else b"")
        else:
            fnum = rom.sound[FNUMS + 8 * (note % 12)] | rom.sound[FNUMS + 8 * (note % 12) + 1] << 8
            out += bytes([0x64, fnum >> 8, fnum & 0xFF])
    return bytes(out + bytes([0x67, 0x00, 0xFF]))


def apply(rom):
    for name, regs in (("melody", MELODY_VOICE), ("bell", BELL_VOICE)):
        at = VOICES + 40 * FREE[name]
        assert rom.sound[at + 39] == 0xFF, "voice %d isn't a record" % FREE[name]
        rom.write_sound(at, record(regs), expect=bytes(rom.sound[at:at + 40]),
                        why="voice %d: 3 Count Bout's jingle %s voice" % (FREE[name], name))
    rom.write_sound(NO_GATE, NO_GATE_CODE, expect=b"\xFF" * len(NO_GATE_CODE), why="sound driver: Q 0xFF - no gate")
    rom.write_sound(GATE_CALL, bytes.fromhex("cd") + NO_GATE.to_bytes(2, "little") + b"\x00",
                    expect=bytes.fromhex("dd7e2ba7"), why="sound driver: a note's gate - Q 0xFF, none")
    rom.write_sound(FINE_SLIDE, FINE_SLIDE_CODE, expect=b"\xFF" * len(FINE_SLIDE_CODE),
                    why="sound driver: a slide takes the fine tune")
    rom.write_sound(SLIDE_CALL, bytes.fromhex("cd") + FINE_SLIDE.to_bytes(2, "little"), expect=bytes.fromhex("cd54da"),
                    why="sound driver: d (a slide) - the fine tune added")
    blob, starts = bytearray(), {}
    quieter = [(frame, note, tl + DOUBLE_QUIETER, lr) for frame, note, tl, lr in MELODY]
    main_tune, double_tune = MELODY_TUNE
    double = bytes([0x67, double_tune & 0xFF, DOUBLE_DELAYS["melody"], 0x52]) + mml(rom, FREE["melody"], quieter, TEMPO)
    assert DOUBLE_AT + len(double) <= 0x0200, "the melody's double runs into code (%d bytes)" % len(double)
    rom.write_sound(DOUBLE_AT, double, expect=b"\xFF" * len(double),
                    why="eyecatcher jingle: the melody's double (%d bytes)" % len(double))
    starts["melody double"] = DOUBLE_AT
    starts["melody"] = STREAMS_AT + len(blob)
    blob += bytes([0x67, main_tune]) + mml(rom, FREE["melody"], MELODY, TEMPO)
    starts["bell double"] = STREAMS_AT + len(blob)
    blob += bytes([0x67, DETUNE & 0xFF, DOUBLE_DELAYS["bell"], 0x52])
    starts["bell"] = STREAMS_AT + len(blob)
    blob += mml(rom, FREE["bell"], BELL, bell=True)
    assert STREAMS_AT + len(blob) <= 0xF800, "the streams run into RAM (%d bytes)" % len(blob)
    rom.write_sound(STREAMS_AT, bytes(blob), expect=b"\xFF" * len(blob),
                    why="eyecatcher jingle: 3 Count Bout's performance (%d bytes)" % len(blob))
    table = b"".join(starts[n].to_bytes(2, "little") for n in ("melody", "melody double", "bell", "bell double"))
    rom.write_sound(POINTERS, table, expect=bytes(rom.sound[POINTERS:POINTERS + 8]),
                    why="eyecatcher jingle: its streams")
