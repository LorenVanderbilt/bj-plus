NAME = "text-fixes"
DESCRIPTION = "In-game text: typo and wording fixes (from docs/in_game_text.csv)"

# The text is stored inline, packed between code and the text engine's control bytes (0xFE new line, 0xFC / 0xFB
# followed by a long, 0xFF end, 0x0A ...), so a line can't grow where it is. Each fix below replaces a phrase
# found near a string's address (docs/in_game_text.md); a longer phrase may only take trailing spaces that end
# its line. Fixes that don't fit are left out (and listed when building) until the text can be moved elsewhere.
# "?" is character 0x0A (tile 0x50A); many question lines already end with it.
FIXES = [
    # (string address, old phrase, new phrase)
    (0x227A6, "IHDECISION", "INDECISION"), (0x227A6, "HOWHERE", "NOWHERE"),
    (0x229D0, "BEAT EMPEROR DARUMA", "BEAT EMPEROR DARUMA?"),
    (0x22F86, "CUT THAT TREE", "CUT THAT TREE?"),
    (0x2323C, "MY HATCHET,", "MY HATCHET!"),
    (0x235B0, "BELIEVE IT", "BELIEVE IT?"),
    (0x24E28, "ACCEPTED PROPOSE.", "ACCEPTED THE PROPOSAL."),
    (0x25E66, "NO,I DON'T.", "NO, I DON'T"),
    (0x25F28, "HAVE YOU ANSWERED", "HAVE YOU ANSWERED?"),
    (0x260E0, "TAKE THE FLOWERS.", "TAKE YOUR FLOWERS"),
    (0x2613C, "WHAT IS MY NAME", "WHAT IS MY NAME?"),
    (0x262AF, "YOUR DREAM COME", "YOUR DREAMS COME"),
    (0x2630C, "WHAT DO YOU PREFER", "WHAT DO YOU PREFER?"),
    (0x26556, "WANT TO KNOW", "WANT TO KNOW?"),
    (0x26926, "ARE YOU INTERESTED", "ARE YOU INTERESTED?"),
    (0x269A6, "ARE YOU SURPRISED", "ARE YOU SURPRISED?"),
    (0x26A88, "LOOK MY MAGIC.", "SEE MY MAGIC."),     # (LOOK AT MY MAGIC. doesn't fit)
    (0x26BC8, "GO BUCK", "GO BACK"),
    (0x26C64, "IS SO THAT.", "IS THAT SO?"),
    (0x26DB2, "DID YOU ENJOY IT", "DID YOU ENJOY IT?"),
    (0x2724A, "THE TRAVEL AGENT", "THE TRAVEL AGENT?"),
    (0x27392, "WHERE ARE YOU GOING", "WHERE ARE YOU GOING?"),
    (0x27620, "GRAB A RIDE", "GRAB A RIDE?"),
    (0x27F38, "TRAINIG", "TRAINING"),
    (0x280C2, "LOSTER.", "LOSER."),
    (0x28168, "AWAY FROM ME", "AWAY FROM ME?"),
    (0x281E0, "CHOICE.I'LL FIGHT.", "CHOICE. I'LL FIGHT"),
    (0x28760, "BULE, YOU", "BLUE, YOU"), (0x28760, "BULE TOOK", "BLUE TOOK"),
    (0x2C6C6, "TIME FOR CARDS", "TIME FOR CARDS?"),
    (0x2C825, "KNOW THE RULES", "KNOW THE RULES?"),
    (0x2C960, "ODD ARE DOUBLE.", "ODDS ARE DOUBLE"),
    (0x2CCD6, "ENOUGH FLOWER.", "ENOUGH FLOWERS"),
    (0x2D3FE, "UNTERSTAND", "UNDERSTAND"),
    (0x2D68A, "LISTEN TO ME", "LISTEN TO ME?"),
    (0x2DB3C, "TIME BY PLAING", "TIME PLAYING"),
    (0x2DF7E, "I TATE", "I DATE"),
    (0x2E42E, "WUTH", "WITH"),
    (0x2E964, "IS THAT SO", "IS THAT SO?"),
    (0x2E970, "ON YOUR HAND.", "ON YOUR HAND?"),
    (0x2EA02, "NO I DIDN'T", "NO, I DIDN'T!"),
    (0x2F3A6, "WHAT CAN WE DO", "WHAT CAN WE DO?"),
    (0x32D70, "CAN YOU BEAT ME", "CAN YOU BEAT ME?"),
    (0x33B20, "MISSIN", "MISSION"),
    (0x3570E, "LEAF DUMP.", "LEAF THROW"),
    (0x54551, "JUMP !", "JUMP! "),
    (0x54799, "THE DUMP WILL", "THE LEAF TO"),
    (0x547BD, "OVER RUN THE", "STUN YOUR"),
    (0x547E1, "ENEMYS.", "ENEMIES."),
    (0x5484F, "THE ENEMY.", "A STUNNED ENEMY"),
    (0x54899, "THE FLOWER IS", "THE FLOWERS ARE"),
    (0x548E1, "HUNG ON TO IT.", "HANG ON TO THEM"),
    (0x34986, "BAD GUY.", "YOU JERK"),                  # (YOU JERK! doesn't fit)
]


# Shop descriptions (English, 0x21000-0x214FF), each written once per price variant: name / price / description
# lines. Rewritten whole in the original's space: the price line kept, new name and description, then the end byte
# (the rest of the space padded after it). The spike shoes' text ended after "AVOIDS" (an end byte where a new line
# was meant), orphaning "  SLIPPING", which runs straight into the next string; those variants take its space too.
SHOP = [
    # (addresses of the price variants, new name, new description lines or None = keep, also take the orphan)
    ([0x2107C, 0x210AA, 0x212A8], "NECTAR", ["  RESTORES", "  1 HEART"], False),
    ([0x210D8, 0x21108, 0x21138, 0x212D6, 0x21306, 0x21336], "FLIPPERS", ["  SWIM", "  FASTER"], False),
    ([0x21168, 0x2118C, 0x21366, 0x2138A], "ICE SHOES", ["  NO SLIPPING"], True),
    ([0x2123A, 0x21438], "MAGIC WAND", ["  DISPELS", "  CURSE"], False),
    ([0x21268, 0x21288, 0x21466, 0x21486], "FERN", [" SPEED UP"], False),
]


def shop_text(rom, addr, name, desc, orphan):
    end = addr
    while rom.data[end] != 0xFF:
        end += 1
    lines = bytes(rom.data[addr:end]).split(b"\xfe")
    end += 1                                     # through the end byte
    if orphan:
        end += len(b"  SLIPPING")
    new = [name.encode(), lines[1]] + ([l.encode() for l in desc] if desc is not None else lines[2:])
    text = b"\xfe".join(new) + b"\xff"
    room = end - addr
    if len(text) > room:
        raise SystemExit("text-fixes: shop text at 0x%X is %d bytes, room %d" % (addr, len(text), room))
    return text.ljust(room, b" "), room


def apply(rom):
    skipped, already = [], []
    for addr, old, new in FIXES:
        area = bytes(rom.data[addr - 4:addr + 400])
        at = area.find(old.encode())
        if at < 0:
            raise SystemExit("text-fixes: %r not found near 0x%X" % (old, addr))
        at += addr - 4
        if new == old + "?" and rom.data[at + len(old)] == 0x0A:
            already.append(new)
            continue
        room = len(old)
        while room < len(new) and rom.data[at + room] == 0x20:   # trailing spaces ending the line
            room += 1
        if len(new) > room:
            skipped.append("0x%X %r -> %r (%d more characters than fit)" % (addr, old, new, len(new) - room))
            continue
        text = new.ljust(room).encode().replace(b"?", b"\x0a")
        rom.write(at, text, expect=bytes(rom.data[at:at + room]), why="text: %s -> %s" % (old, new))
    for addrs, name, desc, orphan in SHOP:
        for addr in addrs:
            text, room = shop_text(rom, addr, name, desc, orphan)
            rom.write(addr, text, expect=bytes(rom.data[addr:addr + room]), why="shop text: %s" % name)
    print("  (text-fixes: already end with ? in the game) %d lines" % len(already))
    for s in skipped:
        print("  (text-fixes: doesn't fit yet) " + s)
