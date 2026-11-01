NAME = "sound-test-names"
DESCRIPTION = "Sound test: the MUSIC: line names each track and skips the ones that aren't music; the SOUND FX: line's names from the live sheet"

# The sound test's MUSIC: line (st2_loop in title-menu) used to show only the track number. Now the track's name
# follows it, read from docs/music_labels.csv: one row per track, with its number in hex and its name. "E" or blank
# means not music and is skipped; "?" means unnamed.
#
# Two sites in title-menu's code are hooked, found by their bytes since that code moves if it grows. NAME_CALL, where
# the line is set up for st2_line, now points a2 at the track's name. STEP_STORE, where Left / Right store the new
# number, now keeps stepping past skipped tracks, wrapping round the range. Names are padded to the longest, so a
# short name clears the end of a longer one.
#
# The SOUND FX: line's list (title-menu's sfx_table) is built from a frozen copy of the sheet so title-menu's size
# never changes. Here it's replaced by a list from the live docs/sfx_labels.csv, a grid with the code's high digit as
# the row and its low digit as the column. SFX_NAME jumps to a copy of st2_sfx that reads the new list, and the range
# checks (SFX_FIRST_CHECK, SFX_STEP) get the new length.
LABELS = "docs/music_labels.csv"
FIRST, END = 0x04, 0x24        # music is 0x04-0x23 (title-menu's FIRST_SOUND to FIRST_EFFECT - 1)
MUSIC_NO = 0x10E931            # RAM: the MUSIC: line's track number
NAME_CALL = bytes.fromhex("10390010E931323C")     # move.b MUSIC_NO,d0 ; move.w #ST2_LINE0,d1 ; moveq #0,d3 ;
                                                  # sub.l a2,a2 ; bsr st2_line
STEP_STORE = bytes.fromhex("13C00010E931")        # move.b d0,MUSIC_NO (d0 = new number, d2 = step, -1 or 1)
LINE_ROOM = 32 - len("MUSIC: ") - 2 - 1 - 1       # LINE_BUF holds the label, 2 digits, a space, the name and a 0
SFX_LABELS = "docs/sfx_labels.csv"
SOUND_NO = 0x10E901            # RAM: the SOUND FX: line's position in the list
SFX_NAME = bytes.fromhex("700010390010E901C0FC")  # st2_sfx: moveq #0,d0 ; move.b SOUND_NO,d0 ; mulu #<entry>,d0 ...
SFX_FIRST_CHECK = bytes.fromhex("10390010E9010C40")   # move.b SOUND_NO,d0 ; cmp.w #<count>,d0, on entry
SFX_STEP = bytes.fromhex("303C")                      # move.w #<count>-1,d0 ; cmp.w #<count>,d0, on Left / Right
SFX_ROOM = 32 - len("SOUND FX: ") - 2 - 1 - 1


def labels():
    import csv
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), LABELS)
    rows = list(csv.reader(open(path, encoding="utf-8")))
    while rows and not rows[0][0].startswith("Number"):     # skip the title row Numbers adds on export
        rows.pop(0)
    names = {}
    for row in rows[1:]:
        code = int(row[0], 16)
        name = row[2].strip().replace("’", "'").upper()
        if name in ("", "E"):
            continue
        if set(name) <= {"?"}:
            name = "?"
        bad = [c for c in name if not ("A" <= c <= "Z" or "0" <= c <= "9" or c in " !'(),-.?/")]
        if bad:
            raise SystemExit("music-names: %s's name %r has characters the font lacks: %r" % (hex(code), name, bad))
        names[code] = name
    assert all(FIRST <= c < END for c in names) and FIRST in names
    return names


def sfx_labels():
    """[(code, name)] in code order, from the live sheet."""
    import csv
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), SFX_LABELS)
    rows = list(csv.reader(open(path, encoding="utf-8")))
    while rows and rows[0][0].strip():                       # skip the title row Numbers adds on export
        rows.pop(0)
    cols = [int(c, 16) for c in rows[0][1:]]
    out = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        hi = int(row[0], 16)
        for lo, cell in zip(cols, row[1:]):
            name = cell.strip().replace("\u2019", "'").upper()
            if name in ("", "E"):
                continue
            if set(name) <= {"?"}:
                name = "?"
            bad = [c for c in name if not ("A" <= c <= "Z" or "0" <= c <= "9" or c in " !'(),-.?/")]
            if bad:
                raise SystemExit("sound-test-names: %s's name %r has characters the font lacks: %r"
                                 % (hex(hi << 4 | lo), name, bad))
            out.append((hi << 4 | lo, name))
    return sorted(out)


def find(rom, pat):
    at = bytes(rom.data).find(pat)
    assert at > 0 and bytes(rom.data).find(pat, at + 1) < 0, "music-names: %s not found once" % pat.hex()
    return at


def apply(rom):
    names = labels()
    width = max(len(n) for n in names.values())
    assert width <= LINE_ROOM, "music-names: a name longer than the line's %d" % LINE_ROOM
    entry = width + 1
    table = b"".join(names.get(c, "").ljust(width).encode() + b"\0" for c in range(FIRST, END))
    skips = bytes(0 if c in names else 1 for c in range(FIRST, END))

    site = find(rom, NAME_CALL)
    line0 = rom.u16(site + 8)
    assert rom.data[site + 10:site + 16] == bytes.fromhex("760095CA6100")
    step = find(rom, STEP_STORE)

    def bytes_list(b):
        return ",".join("0x%02X" % x for x in b)
    code = rom.place_code("""
    bra.w name
    bra.w step
| MUSIC: line set-up: d1 / d3 as before, a2 = the name of track d0 (d0 kept)
name:
    move.w #0x%(line0)X,%%d1
    moveq #0,%%d3
    lea names(%%pc),%%a2
    moveq #0,%%d2
    move.b %%d0,%%d2
    sub.w #0x%(first)X,%%d2
    mulu #%(entry)d,%%d2
    add.w %%d2,%%a2
    rts
| Left / Right: d0 = new number, d2 = step; skip tracks that aren't music, wrapping round
step:
    lea skips(%%pc),%%a0
1:  tst.b -0x%(first)X(%%a0,%%d0.w)
    beq 3f
    add.w %%d2,%%d0
    cmp.w #0x%(first)X,%%d0
    bge 2f
    move.w #0x%(last)X,%%d0
2:  cmp.w #0x%(end)X,%%d0
    blt 1b
    move.w #0x%(first)X,%%d0
    bra 1b
3:  move.b %%d0,0x%(music_no)X
    rts
skips:
    .byte %(skips)s
names:
    .byte %(table)s
    .even
""" % {"line0": line0, "first": FIRST, "last": END - 1, "end": END, "entry": entry, "music_no": MUSIC_NO,
       "skips": bytes_list(skips), "table": bytes_list(table)},
        why="sound test: the music tracks' names, the ones that aren't music skipped")
    rom.write(site + 6, bytes.fromhex("4EB9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=rom.data[site + 6:site + 14], why="sound test, MUSIC: line: its track's name after the number")
    rom.write(step, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big"), expect=STEP_STORE,
              why="sound test, MUSIC: line: Left / Right skip what isn't music")

    # the SOUND FX: line's list, from the live sheet
    sfx = sfx_labels()
    sw = max(len(n) for c, n in sfx)
    assert sw <= SFX_ROOM, "sound-test-names: a sound effect's name longer than the line's %d" % SFX_ROOM
    sfx_entry = sw + 2
    sfx_table = b"".join(bytes([c]) + n.ljust(sw).encode() + b"\0" for c, n in sfx)
    name_at = find(rom, SFX_NAME)
    first = find(rom, SFX_FIRST_CHECK) + len(SFX_FIRST_CHECK)
    old = rom.u16(first)
    stp = find(rom, SFX_STEP + (old - 1).to_bytes(2, "big") + bytes.fromhex("0C40") + old.to_bytes(2, "big"))
    sfx_code = rom.place_code("""
    moveq #0,%%d0
    move.b 0x%(sound_no)X,%%d0
    mulu #%(entry)d,%%d0
    lea table(%%pc),%%a2
    add.w %%d0,%%a2
    moveq #0,%%d0
    move.b (%%a2)+,%%d0
    rts
table:
    .byte %(table)s
    .even
""" % {"sound_no": SOUND_NO, "entry": sfx_entry, "table": bytes_list(sfx_table)},
        why="sound test: the sound effects' list, from the live sheet")
    rom.write(name_at, bytes.fromhex("4EF9") + sfx_code.to_bytes(4, "big"), expect=SFX_NAME[:6],
              why="sound test, SOUND FX: line: its list from the live sheet")
    rom.write(first, len(sfx).to_bytes(2, "big"), expect=old.to_bytes(2, "big"),
              why="sound test, SOUND FX: line: the list's length (on entry)")
    rom.write(stp + 2, (len(sfx) - 1).to_bytes(2, "big") + bytes.fromhex("0C40") + len(sfx).to_bytes(2, "big"),
              expect=(old - 1).to_bytes(2, "big") + bytes.fromhex("0C40") + old.to_bytes(2, "big"),
              why="sound test, SOUND FX: line: the list's length (Left / Right)")
