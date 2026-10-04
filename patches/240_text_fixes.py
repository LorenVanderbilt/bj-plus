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
    (0x25F28, "HAVE YOU ANSWERED", "HAVE YOU ANSWERED?"),
    (0x260E0, "TAKE THE FLOWERS.", "TAKE YOUR FLOWERS"),
    (0x2613C, "WHAT IS MY NAME", "WHAT IS MY NAME?"),
    (0x262AF, "YOUR DREAM COME", "YOUR DREAMS COME"),
    (0x2630C, "WHAT DO YOU PREFER", "WHAT DO YOU PREFER?"),
    (0x26556, "WANT TO KNOW", "WANT TO KNOW?"),
    (0x26926, "ARE YOU INTERESTED", "ARE YOU INTERESTED?"),
    (0x269A6, "ARE YOU SURPRISED", "ARE YOU SURPRISED?"),
    (0x26BC8, "GO BUCK", "GO BACK"),
    (0x26C0A, "HERE WE GO.", "HERE WE GO!"),
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
    (0x2CCD6, "ENOUGH FLOWER.", "ENOUGH FLOWERS"),
    (0x2D3FE, "UNTERSTAND", "UNDERSTAND"),
    (0x2D68A, "LISTEN TO ME", "LISTEN TO ME?"),
    (0x2DB3C, "TIME BY PLAING", "TIME PLAYING"),
    (0x2DF7E, "I TATE", "I DATE"),
    (0x2E42E, "WUTH", "WITH"),
    (0x2E964, "IS THAT SO", "IS THAT SO?"),
    (0x2E970, "ON YOUR HAND.", "ON YOUR HAND?"),
    (0x2F3A6, "WHAT CAN WE DO", "WHAT CAN WE DO?"),
    (0x32D70, "CAN YOU BEAT ME", "CAN YOU BEAT ME?"),
    (0x33B20, "MISSIN", "MISSION"),
    (0x54551, "JUMP !", "JUMP! "),
    (0x54799, "THE DUMP WILL", "THE LEAF TO"),
    (0x547BD, "OVER RUN THE", "STUN YOUR"),
    (0x547E1, "ENEMYS.", "ENEMIES."),
    (0x5484F, "THE ENEMY.", "A STUNNED ENEMY"),
    (0x54899, "THE FLOWER IS", "THE FLOWERS ARE"),
    (0x548E1, "HUNG ON TO IT.", "HANG ON TO THEM"),
    (0x34986, "BAD GUY.", "YOU JERK"),                  # (YOU JERK! doesn't fit)
    # the lottery after each boss
    (0x295E6, "DREWING.", "DRAWING."),
    (0x2971D, "OKEY,I BET.", "LET'S PLAY!"), (0x2971D, "I'LL PASS.", "NO THANKS."),
    (0x29B02, "FIRST PRIZE!", "1ST PRIZE!"), (0x29BF0, "2ND PRIZE.", "2ND PRIZE!"),
    (0x29CDC, "3RD PRIZE.", "3RD PRIZE!"), (0x29DF0, "4TH PRIZE.", "4TH PRIZE!"),
]

# Whole strings rewritten in their own space: the new lines, then the original's ending (an end byte, or a
# callback: 0xFC + the code's address, which doesn't move), the rest padded after it (never read).
STRINGS = [
    # the hint about the quiz man (one per name): QUESTINS, his name, and a few words shortened to make room
] + [(addr, ["IN THE SHABARN MARSH EMPIRE", "YOU'LL FIND AN OLD MAN WHO", "LOVES QUIZZES.", "HE'LL HELP YOU",
             "IF YOU ANSWER HIS QUESTIONS", "HIS NAME IS %s." % name])
     for addr, name in [(0x22B88, "POPOPPE"), (0x22C92, "PIKKYURU"), (0x22D9A, "PUKAMONME")]] + [
    # his name, as the quiz's answers: HOHOPPEY / PECULU / PUCAMONMME, romanized again from the Japanese
    # (ポポッペー, ピッキュル, プカモンメ)
    (0x261CA, ["  POPOPPE", "  PIKKYURU", "  PUKAMONME"]),
    # his greeting (after his laugh) and its choices, closer to the Japanese (クイズじいさん, "Quiz Grandpa"; わかった / いやだ！)
    (0x25DC0, ["I'M THE QUIZ GRANDPA!", "YOU GET TWO QUESTIONS.", "MISS ONE AND I'LL TAKE", "ALL YOUR FLOWERS!"]),
    (0x25E66, ["  GOT IT!", "  NO WAY!"]),
    # the happy ending: FA ACCEPTED PROPOSE. / THEY LED A HAPPY LIFE. (ACCEPTED THE PROPOSAL doesn't fit)
    # (the ending's box takes 32: BLUE, HAVE A HAPPY LIFE WITH FA. at 0x24CB6)
    (0x24E28, ["FA ACCEPTED.", "THEY LIVED HAPPILY EVER AFTER."], 32),
    # the story cinema (the box takes 33: FA WAS OVERCOME BY THE POLLUTION. at 0x358A2)
    (0x34BA8, ["THE PLANET RAGUY WAS ONCE", "BEAUTIFUL."]),
    (0x34C38, ["BUT..."]),
    (0x34DCA, ["THEN THE DARUMA TRIBE", "INVADED,"]),
    (0x34E6E, ["AND THEIR POLLUTION GETS", "WORSE EVERY DAY."]),
    (0x35710, ["THIS IS BLUE,", "A MASTER OF THE", "LEAF DUMP."]),      # (LEAF DUMP kept: a fan favourite)
    (0x357E2, ["BLUE LOVES PRINCESS FA", "OF RAGUY'S ROYAL FAMILY."]),
    (0x358A2, ["FA FELL ILL FROM THE POLLUTION."]),
    (0x3595E, ["BLUE, DRIVE OUT THE DARUMA", "AND BRING RAGUY BACK TO LIFE!"], 33),
    # (after "THEN WHAT'S BURNING ON YOUR HAND?") IN FACT,I SET HIM FREE. / NO I DIDN'T
    (0x2EA02, ["  FINE, I SET HIM FREE.", "  NO, I DIDN'T!"]),
    # the magician's opener (was LOOK MY MAGIC. / IT'S ONLY 5 FLOWERS.); his box takes 27, as the quiz hint's
    (0x26A88, ["WANT TO SEE A TRICK?", "ONLY 5 FLOWERS"], 27),
    (0x26AEC, ["  SURE!", "  NO THANKS."]),                       # (was I'LL LOOK. / I WON'T LOOK.)
    (0x26ED4, ["YOU MAKE ME HAPPY.", "TAKE THIS NECTAR WITH YOU."]),  # (was ... HONEY ..., as the shop's NECTAR)
    # the card game: "DO YOU KNOW THE RULES?" - its first answer (YES) actually explained them; WHAT'YOUR BET?
    (0x2C826, ["DO YOU WANT THE RULES?"]),
    (0x2CA0E, ["PLACE YOUR BET."]),
    (0x2C960, ["YOU WIN IF YOU PICK THE SAME", "CARD AS ME.", "WIN DOUBLE YOUR BET.", "ONE GAME ONLY.",
               "OK. LET'S GO."]),     # (was ... OPEN ... / ODD ARE DOUBLE. / YOU ONLY GET TO PLAY ONCE. / O.K. ...;
                                      # Japanese: the payout is 2x, a one-game match)
    # the lottery after each boss (its box takes 15: SETTING US FREE at 0x295E6)
    (0x29900, ["OK! MAYBE", "NEXT TIME."]),                        # I SEE. / SEE YOU LATER.
    (0x29958, ["SORRY! YOU NEED", "10 FLOWERS."], 15),                 # NO. / YOU DON'T HAVE / 10 FLOWERS.
    (0x29F26, ["SORRY!", "NO PRIZE"]),                             # OH. / SORRY MISS.
    (0x2A036, ["LIFE BALL", "1 MORE HEART."], 15),                     # (+1 maximum heart)
    (0x2A08A, ["SILVER COCOON", "FIVE OF THEM", "FOR A 1UP."]),
    (0x2A0E0, ["NECTAR", "RESTORES", "1 HEART."]),                 # HONEY. / STAMIRA RECOV- / ERS.
    (0x2A132, ["LUCKY RING", "IT WILL BRING", "YOU LOVE."]),       # (the princess always says yes)
    (0x2A1B0, ["30 FLOWERS", "YOU'RE RICH!"]),
    (0x2A1F6, ["GOLD COCOON", "1UP!"]),                            # GOLDEN COCOON. / 1 UP.
]


# Shop descriptions (English, 0x21000-0x214FF), each written once per price variant: name / price / description
# lines. Rewritten whole in the original's space: the price line kept, new name and description, then the end byte
# (the rest of the space padded after it). The spike shoes' text ended after "AVOIDS" (an end byte where a new line
# was meant), orphaning "  SLIPPING", which runs straight into the next string; those variants take its space too.
SHOP = [
    # (addresses of the price variants, new name, new description lines or None = keep, also take the orphan)
    ([0x2107C, 0x210AA, 0x212A8], "NECTAR", ["  RESTORES", "  1 HEART"], False),
    ([0x210D8, 0x21108, 0x21138, 0x212D6, 0x21306, 0x21336], "FLIPPERS", ["  SWIM", "  FASTER"], False),
    ([0x21168, 0x2118C, 0x21366, 0x2138A], "ICE SHOES", [" NO SLIPPING"], True),
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


def whole_string(rom, addr, lines, width=None):
    end = addr
    while rom.data[end] not in (0xFF, 0xFC, 0xFB):
        if rom.data[end] < 0x20 and rom.data[end] != 0x0A:
            raise SystemExit("text-fixes: 0x%X isn't a plain string" % addr)
        end += 1
    tail = bytes(rom.data[end:end + {0xFF: 1, 0xFC: 5, 0xFB: 9}[rom.data[end]]])   # (0xFB: next text, then a callback)
    room = end + len(tail) - addr
    # keep each line within the box (the longest original line, unless a wider one is given)
    width = width or max(len(l) for l in bytes(rom.data[addr:end]).split(b"\xfe"))
    if max(len(l) for l in lines) > width:
        raise SystemExit("text-fixes: %r has a line over %d characters" % (lines, width))
    text = b"\xfe".join(l.encode() for l in lines).replace(b"?", b"\x0a")
    if tail[0] != 0xFF and (addr + len(text) + 1) % 2:
        text += b" "             # a callback's address is read as a long: it must stay on an even byte (68000)
    text += tail
    if len(text) > room:
        raise SystemExit("text-fixes: %r is %d bytes, room %d" % (lines, len(text), room))
    return text.ljust(room, b" "), room


# Strings too long for their space, written elsewhere: (where the game loads the string's address, old address,
# new lines). The card game's answers to DO YOU WANT THE RULES? (TELL ME / NO: the first explains them, as YES did).
MOVED = [
    (0x2C852, 0x2C89C, ["  TELL ME", "  NO"]),        # (was   YES /   NO; the first explains the rules)
]


# A text that ends in 0xFB (show the next text) waits 63 frames (0x21832: move.b #63,0x78A8(a6)) - for every such
# chain. The card game's rules are long: before its PLACE YOUR BET. they wait longer.
LONGER_WAITS = {0x2CA0E: 123, 0x2C9F2: 123}       # next text (English, Japanese) -> frames
CHAIN_WAIT = 0x21832


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
    for addr, lines, *width in STRINGS:
        text, room = whole_string(rom, addr, lines, *width)
        rom.write(addr, text, expect=bytes(rom.data[addr:addr + room]), why="text: %s" % " / ".join(lines))
    src = "    move.b #63,0x78A8(%a6)\n"
    for i, (nxt, frames) in enumerate(LONGER_WAITS.items(), 1):
        src += "    cmp.l #0x%X,0x78A4(%%a6)\n    bne.s %df\n    move.b #%d,0x78A8(%%a6)\n%d:\n" % (nxt, i, frames, i)
    wait = rom.place_code(src + "    rts\n", why="text chains: longer waits before some texts")
    rom.write(CHAIN_WAIT, bytes.fromhex("4EB9") + wait.to_bytes(4, "big"), expect=bytes.fromhex("1D7C003F78A8"),
              why="text chains: the wait, longer before some texts")
    for ref, old, lines in MOVED:
        text = b"\xfe".join(l.encode() for l in lines) + b"\xff"
        at = rom.alloc(len(text))
        rom.data[at:at + len(text)] = text
        rom.write(ref, at.to_bytes(4, "big"), expect=old.to_bytes(4, "big"), why="text: %s (moved)" % " / ".join(lines))
    print("  (text-fixes: already end with ? in the game) %d lines" % len(already))
    for s in skipped:
        print("  (text-fixes: doesn't fit yet) " + s)
