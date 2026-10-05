NAME = "text-fixes"
DESCRIPTION = "In-game text: typo and wording fixes (from docs/in_game_text.csv)"

# The text is stored inline, packed between code and the text engine's control bytes (0xFE new line, 0xFC / 0xFB
# followed by a long, 0xFF end, 0x0A ...), so a line can't grow where it is. Each fix below replaces a phrase
# found near a string's address (docs/in_game_text.md); a longer phrase may only take trailing spaces that end
# its line. Fixes that don't fit are left out (and listed when building) until the text can be moved elsewhere.
# "?" is character 0x0A (tile 0x50A); many question lines already end with it.
FIXES = [
    (0x2BE3A, "STARGE SPACE", "STRANGE SPACE"),                 # the map screen's area name
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
    (0x2EA02, ["  HEH, OKAY, IT WAS ME.", "  NO, I DIDN'T!"]),   # (was FINE, I SET HIM FREE. - she asked whether he freed her)
    # the magician's opener (was LOOK MY MAGIC. / IT'S ONLY 5 FLOWERS.); his box takes 27, as the quiz hint's
    (0x26A88, ["WANT TO SEE A TRICK?", "ONLY 5 FLOWERS"], 27),
    (0x26AEC, ["  SURE!", "  NO THANKS."]),                       # (was I'LL LOOK. / I WON'T LOOK.)
    (0x26ED4, ["YOU MAKE ME HAPPY.", "TAKE THIS NECTAR WITH YOU."]),  # (was ... HONEY ..., as the shop's NECTAR)
    # the boatman, after SEE THE LARGE RIVER AHEAD? - YES (was IT'S GOOD IF YOU KNOW IT.)
    # ... after NO (the IVY is the swinging vine; Japanese: rope), and his menu
    (0x22664, ["THE BIG RIVER IS POLLUTED.", "FALL IN AND YOU'RE DONE FOR.", "YOU CAN CROSS WITH THE VINE,",
               "BUT MANY HAVE DIED TRYING."]),
    (0x22718, ["TAKE MY ADVICE.", "RENT ONE OF MY BOATS."]),           # (was FOGET THAT IDEA. / YOU SHOULD USE MY BOAT.)
    (0x22462, ["  A LEAF BOAT, PLEASE.", "  A MUD BOAT, PLEASE.", "  NO THANKS."]),   # ASK FOR LEAF MADE BOAT ...
    (0x2280C, ["SORRY, YOU CAN'T AFFORD IT."]),                        # (was YOU HAVE RUN OUT OF MONEY.)
    # the Daruma Empire 1 mini boss's offer (was IF YOU BECOME / ONE OF US / I WON'T TAKE / YOUR LIFE.) and Blue's
    # answers (was YES I WILL. / NO KIDDING. - read as agreeing; Japanese: はい喜んで。 / 馬鹿言うな！)
    (0x32DE4, ["JOIN ME, AND", "I'LL SPARE", "YOUR LIFE."]),
    # the fake ending after the first boss's I'LL GO HOME! (was BLUE'S IRRESPONSIBILITY CAUSED / THE POLLUTION THAT
    # RUINED RAGUY.), and the fake endings' tag line (was DO YOU BELIEVE IT?; Japanese: なんちゃって, "just kidding")
    (0x234E4, ["BLUE GAVE UP AND WENT HOME.", "RAGUY WAS RUINED BY POLLUTION.", " ", "          THE END              "]),
    (0x235B0, ["JUST KIDDING!"]),
    # the last level's mini boss (was MY MISSIONIS TO / KILL YOU BLUE. - its box showed only KILL YOU)
    (0x33B22, ["MY ONLY MISSION", "IS TO KILL YOU!"]),
    # ... and after his defeat (the rest of that scene: RELOCATED)
    (0x2F2B8, ["NONE OF YOUR WEAPONS CAN", "EVEN SCRATCH HIM."]),   # (was YOU CAN'T HURT HIM WITH ANY OF / YOUR WEAPONS.)
    (0x3636A, ["YOU DARE", "DEFY ME?"]),                    # the final boss (was ARE YOU / RESISTINS ME?)
    # Mechanical City 3: the frozen princess's house (Japanese as a guide; the longer lines: RELOCATED)
    (0x2E064, ["  GO CLOSER.", "  LEAVE."]),                              # APPROACH. / JUST IGNORE IT.
    (0x2E178, ["WHAT WILL YOU DO?"]),                                      # WHAT ARE YOU GOING TO DO?
    (0x2E21E, ["  PRETEND NOT TO SEE.", "  CALL HER NAME.", "  USE A TORCH.", "  JUST WAIT."], 30),
    (0x2E466, ["..."]),                                                    # JUST WAIT.'s ....... (7)
    (0x2E340, ['"PRINCESS LIM!" BLUE SHOUTED.']),                         # "PRICESS LIM", BLUE SHOUTED.
    (0x2E42E, ["BLUE DOESN'T HAVE A TORCH."]),                              # BLUE DID NOT HAVE THE TORCH / WITH HIM.
    (0x2EDA8, ["WITH THIS CHARM, NEROS'S", "SPELL WON'T FREEZE YOU."]),     # THIS SPELL PROTECTS YOU FROM / ...
    (0x2DF16, ["BLUE COULDN'T ANSWER,", "SO HE RAN AWAY."]),                 # (time-up) ... SO HE RUN AWAY.
    # the shop: anything she won't sell for a reason other than its price (but the magic wand's YOU'RE NOT CURSED)
    (0x20372, ["SORRY,", "SOLD OUT!"]),                                    # YOUR STAMINA / IS FULL. (nectar)
    (0x20442, ["SORRY,", "SOLD OUT!"]),                                    # YOU ALREADY / HAVE IT.
    # the shop: the 2nd and 3rd can't-afford lines (the 1st and 4th: MOVED)
    (0x201C0, ["STILL BROKE,", "HONEY?"]),                                 # CHECK YOUR / POCKET MONEY
    (0x201FC, ["A DISCOUNT?", "NO WAY!"]),                                 # A DISCOUNT? / NO KIDDING!
    # Lower Earth Empire: Red's duel for the torch
    (0x27E9A, ["WHAT?! YOU BEAT ME IN THE", "CONTEST! NOW FIGHT ME!"]),          # WHAT?! / YOU BEAT ME IN THE CONTEST, / ...
    (0x27F38, ["YOU BEAT ME IN THE CONTEST,", "BUT I'VE BEEN TRAINING.", "NOW FIGHT ME!"]),   # I'VE BEEN TRAINIG SINCE THEN,
    (0x28010, ["  YOU'RE ON!", "  NO TIME TO FIGHT."]),                   # YOU HAVE MY WORD. / THERE'S NO TIME TO FIGHT.
    (0x280C2, ["FIRST ONE TO GET HIT LOSES.", "HERE WE GO!"]),           # WHOEVER RECEIVES ANY DAMAGE IS / IS THE LOSTER.
    (0x281E0, ["  FINE, I'LL FIGHT.", "  I'M IN A HURRY."]),             # I HAVE NO CHOICE.I'LL FIGHT. / I'M HURRYING.
    (0x282D2, ["  WHAT?! I'LL DO IT!", "  I GUESS I'M A COWARD."]),       # WHAT? I'LL DO IT. / I'M A COWARD AFTER ALL.
    (0x28760, ["DANG IT! BACK TO TRAINING.", "BLUE, TAKE THIS.", " ", " BLUE TOOK THE TORCH."]),   # GOT THEN! ... BULE
    (0x28808, ["HA! NOW I'M THE STRONGEST!", "SO LONG, BLUE."]),          # AHH, ... SO LONG, BULE.
    # the travel agent (Japanese: the "Pyuu" travel center)
    (0x2724A, ["NEED A RIDE SOMEWHERE?"]),                 # (was WILL YOU USE THE TRAVEL AGENT?)
    (0x2744C, ["  10 FLOWERS", "    TO THIS AREA'S BOSS", "  20 FLOWERS", "    TO THE EMPIRE MARSH",
               "  60 FLOWERS", "    TO THE MECHANICAL CITY", "  NO THANKS."]),   # (was USE 10 FLOWERS TO GET TO / ...)
    (0x27620, ["HEY! NO FREE RIDES!"]),      # too few flowers (was ARE YOU GOING TO GRAB A RIDE?; Japanese: a fare dodger!)
    (0x27660, ["ALL ABOARD!"]),                            # (was O.K. LET'S GO.)
    (0x27362, ["COME AGAIN!"]),                            # (was COME AGAIN.)
    (0x32E9B, [" YES, SIR!", "  DREAM ON!"]),       # (after its 0x11, the cursor)
    # ... and YES, SIR!'s ending (was RAGUY IS RUINED BY POLLUTION. / BLUE LIVES THE REST OF HIS LIFE / IN THE
    # DARUMA TRIBE.; Japanese: Raguy was destroyed by pollution, but Blue lived his whole life as one of the Daruma)
    (0x239D0, ["RAGUY WAS RUINED BY POLLUTION,", "AND BLUE LIVED OUT HIS DAYS", "AS ONE OF THE DARUMA TRIBE.",
               " " * 31, " " * 12 + "THE END"]),
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
    # the shop: buying what you can't afford - her lines, one per try (the 4th sends you off; 0x2012A + 4 * n)
    (0x2012A, 0x20198, ["NICE TRY.", "YOU CAN'T", "AFFORD IT."]),      # (was   YOU CAN'T /   BUY IT.)
    (0x2012E, 0x20198, ["NICE TRY.", "YOU CAN'T", "AFFORD IT."]),
    (0x2013A, 0x20230, ["COME BACK", "WHEN YOU'RE", "RICH!"]),          # (was I WON'T TALK / TO POOR.)
    # the ocarina's two prices (was IT'S TOY.; it gets the lottery's 1st prize for a song: ocarina-song)
    (0x20F50, 0x21006, ["OCARINA", "5 FLOWERS", "  LUCKY", "  MELODIES"]),
    (0x20F70, 0x21022, ["OCARINA", "10 FLOWERS", "  LUCKY", "  MELODIES"]),
    (0x2C852, 0x2C89C, ["  TELL ME", "  NO"]),        # (was   YES /   NO; the first explains the rules)
    # the final boss's question's answers: the first fights, the second gives in (the Daruma tribe ending) - was
    # I CAN'T FORGIVE / NO WAY! (which read as refusing; Japanese: probably とんでもない, "of course not")
    (0x363C8, 0x3640E, ["\x11 YOU'RE FINISHED!", "  I SURRENDER..."]),
    (0x247A4, 0x24810, ["  YOU'RE ON!", "  NO WAY!"]),     # Red's challenge (was YOU HAVE MY WORD. / NO KIDDING!)
    # the princess on the continue screen (was GIVE A HAND / TO RAGUY'S / PEOPLE.; Japanese: a loving hand for
    # Raguy's people...)
    (0x346D0, 0x3495A, ["BLUE, PLEASE", "DON'T GIVE", "UP ON US!"]),
    # the frozen princess's house: Blue's last choice - the second asks why her charm didn't save her (Japanese:
    # "if you had that, you wouldn't have turned to ice"; her answer: no antidote without knowing the poison)
    (0x2EDF2, 0x2EE44, ["  THANK YOU, PRINCESS LIM.", "  ...WAIT, THEN HOW DID", "  YOU GET FROZEN YOURSELF?"]),
]

# Strings that end in a callback (0xFC) or a chain (0xFB: the next text, then a callback), too long for their space:
# written elsewhere with their ending, and the long that points at them changed - an lea's operand, or the 0xFB
# pointer in the text before (by name: a chain to a string moved here too points at its new place). The robot mini
# boss in the last level, after his defeat (Japanese: it's not programmed into him - he was only built to fight).
RELOCATED = [   # (name, where its address is (an lea's operand) or None, old address, new lines, the 0xFB next by name)
    # the endings (Japanese as a guide)
    # Red's duel for the torch: his greeting (was ... A LONG TIME TO SEE YOU.)
    ("red1", 0x27ADE, 0x27C92, ["BLUE, I'VE BEEN WAITING", "A LONG TIME TO SEE YOU AGAIN.", "DON'T TELL ME YOU FORGOT ME!"], None),
    ("end1", 0x23BCA, 0x23CAC, ["THE DARUMA TRIBE LEFT, AND", "NATURE RETURNED TO RAGUY."], None),
    ("end2", 0x23D04, 0x23D78, ["ALL WHO FELL ILL FROM THE", "POLLUTION WERE CURED,", " ", "INCLUDING PRINCESS FA."], None),
    ("end4", 0x23F14, 0x240F6, ["OF COURSE, FA SAID YES.", "AND THEY LIVED", "HAPPILY EVER AFTER."], None),
    ("end4b", 0x24DB6, 0x24E28, ["OF COURSE, FA SAID YES.", "AND THEY LIVED", "HAPPILY EVER AFTER."], None),
    ("end5", 0x23F8A, 0x23FD8, ["BUT NEROS'S CURSE", "TURNED BLUE TO ICE."], None),        # THEN BLUE WAS FROZEN BY NROS'S ...
    ("end6", 0x25094, 0x250E4, ["BLUE HADN'T EARNED ENOUGH", "FLOWERS, SO FA TURNED", "HIM DOWN..."], None),  # ... NOT WELL PAID.
    ("end7", 0x2402A, 0x24058, ["HOLD IT RIGHT THERE!"], None),                           # JUST A MINUTE!
    ("end8", 0x243B6, 0x2469A, ["BLUE... I'VE ALWAYS", "LOVED FA..."], None),
    ("end9", 0x24718, 0x2476C, ["LET'S SETTLE THIS, BLUE.", "IF I WIN, YOU STEP ASIDE."], None),  # FIGHT ME! / ...
    ("end11", 0x2487E, 0x248C6, ["SHUT UP! WE'RE FIGHTING,", "NO MATTER WHAT!"], None),
    ("end12", 0x24A5A, 0x24CB6, ["BLUE... MAKE FA HAPPY,", "OKAY?"], None),                  # (Blue won the duel)
    ("end13", 0x24A76, 0x24E96, ["WAHAHA! FA IS MINE!", "SO LONG, BLUE!"], None),            # (Red won)
    ("end14", 0x24F4C, 0x24FA0, ["BLUE NEVER RECOVERED", "FROM THE SHOCK."], None),
    ("end15", 0x24B2A, 0x24B7E, ["I'M SORRY... I CAN'T CHOOSE", "BETWEEN YOU."], None),       # (a draw)
    ("end15b", 0x24C12, 0x24C62, ["NEITHER OF THEM EVER", "RECOVERED FROM THE SHOCK."], None),
    ("end16", 0x23704, 0x237BE, ["BLUE COLLAPSED, AND RAGUY", "WAS RUINED BY POLLUTION.", " " * 30,
                                 " " * 12 + "GAME OVER"], None),                         # BLUE IS EXHAUSTED AND ...
    # the boatman, after SEE THE LARGE RIVER AHEAD? - YES (was IT'S GOOD IF YOU KNOW IT.)
    ("boat1", 0x223AE, 0x22596, ["IT'S GOOD THAT YOU", "ALREADY KNOW.", "YOU CAN RENT MY BOAT."], None),
    # the lottery host after each boss: the Japanese opens with "we're a family of travelling merchants", which the
    # English left out (so its THEY CAPTURED US DURING A TRIP. came from nowhere) - a third text chained in front
    ("lot3", None, 0x295E6, ["THANKS FOR", "FREEING US!", "10 FLOWERS FOR", "A LOTTERY DRAW!"], None),  # THIS IS A REWARD ...
    ("lot2", None, 0x29588, ["THE DARUMA", "CAUGHT US ON", "THE ROAD."], "lot3"),                  # THEY CAPTURED ...
    ("lot1", 0x2946C, 0x29588, ["WE'RE A FAMILY", "OF TRAVELING", "GNOMES."], "lot2"),
    # the frozen princess's house (Mechanical City 3)
    ("lim1", 0x2DDFA, 0x2DFCE, ["A WOMAN STANDS FROZEN IN ICE.", "WHAT WILL YOU DO?"], None),  # A WOMAN FROZE BEFORE. / ...
    ("lim2", 0x2E0D0, 0x2E12E, ["W-WAIT! ISN'T THAT LIM,", "THE PRINCESS OF RAGUY?!"], None),  # ISN'T SHE PRINCESS "LIM" OF / ...
    ("lim3", 0x2E39E, 0x2E3E0, ["BUT NOTHING HAPPENED."], None),          # NOTHING HAPPENED.
    ("lim4", 0x2E520, 0x2E55E, ["THE ICE QUICKLY MELTED AWAY."], None),    # THE ICE IS MELTING.
    ("lim5", 0x2E662, 0x2E790, ["OH... THAT'S RIGHT, THE WIZARD", "NEROS FROZE ME...", "DID YOU SET ME FREE?"], None),
    ("lim6", 0x2E90C, 0x2E964, ["REALLY? THEN WHAT'S THAT", "BURNING IN YOUR HAND?"], None),     # IS THAT SO? / ...
    ("lim7", 0x2E852, 0x2E8BA, ["THANK YOU! LET ME CAST A", "CHARM ON YOU IN RETURN.", " ", "     EZORF!"], None),
    ("lim9", 0x2E4AE, 0x2E4EA, ["...THAT WAS A WASTE OF TIME."], None),    # IT'S JUST A WASTE OF TIME.
    ("lim8", 0x2DEBC, 0x2DF7E, ["I HATE INDECISIVE MEN."], None),           # (time-up) I DATE UNSURE MEN.
    ("robot5", None, 0x2F4D0, ["THIS IS THE END FOR ME...", "FAREWELL, MY ETERNAL RIVAL..."], None),   # IT SEEMS LIKE ...
    ("robot4", 0x2F420, 0x2F45A, ["...I WAS ONLY BUILT", "TO FIGHT."], "robot5"),                  # I'M NOT HURT.
    ("robot3", 0x2F376, 0x2F3A6, ["THEN HOW CAN I BEAT HIM?!"], None),                           # WHAT CAN WE DO? (Blue)
    ("robot1", 0x2F08C, 0x2F228, ["YOU WIN, BLUE... BUT EMPEROR", "DARUMA IS FAR STRONGER.", "HIS WEAPON IS DRIVEN BY",
                                  "HIS EVIL WILL."], None),         # I LOST BUT EMPEROR DARUMA IS STRONGER. / ...
]


def relocate(rom, old, lines, next_text=None):
    end = old
    while rom.data[end] not in (0xFF, 0xFC, 0xFB):
        end += 1
    tail = bytearray(rom.data[end:end + {0xFF: 1, 0xFC: 5, 0xFB: 9}[rom.data[end]]])
    if next_text is not None:
        tail[1:5] = next_text.to_bytes(4, "big")
    text = b"\xfe".join(l.encode() for l in lines).replace(b"?", b"\x0a")
    if tail[0] != 0xFF and (len(text) + 1) % 2:
        text += b" "              # (the callback's long on an even byte; the text starts on one)
    text += bytes(tail)
    at = rom.alloc(len(text), align=2)
    rom.data[at:at + len(text)] = text
    return at


# A text that ends in 0xFB (show the next text) waits 63 frames (0x21832: move.b #63,0x78A8(a6)) - for every such
# chain. The card game's rules are long: before its PLACE YOUR BET. they wait longer; so is the boatman's warning
# about the river (4 lines), before his next line.
LONGER_WAITS = {0x2CA0E: 123, 0x2C9F2: 123,       # next text (English, Japanese) -> frames
                0x22718: 210, 0x226E2: 210,
                0x2F2B8: 123, 0x2F284: 123}       # (the robot mini boss's first line, before NONE OF YOUR WEAPONS ...)
# ... and its next line then waits less before the scene moves on: its callback's object counts down from this
ROBOT_LINE2_HOLD = (0x2F30D, 31)              # (63)
# The good ending's lines (THE DARUMA TRIBE LEFT ... / ALL WHO FELL ILL ... / BLUE PROPOSED TO HER.) each wait 30
# frames once typed (their callbacks: move.w #30,d0 ; jsr 0xE858) - rushed: now ENDING_HOLD. And Fa's yes (both
# happy endings' line, callback 0x2411E) set the scene's done flag at once - it faded out as the line ended: it now
# holds HAPPY_HOLD frames first.
ENDING_WAITS = [0x23CE4, 0x23DD6, 0x23E46]
ENDING_HOLD = 90
HAPPY_DONE = 0x2411E          # move.b #1,0x7861(a6)
HAPPY_HOLD = 150
SAD_WAIT, SAD_HOLD = 0x24FD4, 180            # the turned-down, Red-won and draw endings' last line: move.w #50,d0 ; ...
FROZEN_WAIT, FROZEN_HOLD = 0x24002, 180
# Red's interruption: HOLD IT RIGHT THERE! and his BLUE... I'VE ALWAYS LOVED FA... went by fast (30 frames each once
# typed), and Blue's answer to his challenge was timed: 127 frames (0x1078BC, set at 0x247E4), then he picked for you
RED_WAITS = [(0x2406C, 30, 90), (0x246C0, 30, 120), (0x246F8, 30, 120),
             (0x24CDC, 60, 150)]   # (and BLUE... MAKE FA HAPPY, / OKAY? after the duel)   # (move.w #N,d0 ; jsr 0xE858), old, new
RED_CHOICE_TIME = (0x247E4, 127, 360)       # BUT NEROS'S CURSE / TURNED BLUE TO ICE.: move.w #60,d0 ; jsr 0xE858, then the fade
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
    for at in ENDING_WAITS:
        rom.write(at + 2, ENDING_HOLD.to_bytes(2, "big"), expect=(30).to_bytes(2, "big"),
                  why="good ending: a line's hold once typed")
    rom.write(SAD_WAIT + 2, SAD_HOLD.to_bytes(2, "big"), expect=(50).to_bytes(2, "big"),
              why="sad endings: the last line stays before the fade")
    for at, old, new in RED_WAITS:
        rom.write(at + 2, new.to_bytes(2, "big"), expect=old.to_bytes(2, "big"), why="Red's interruption: a line's hold")
    at, old, new = RED_CHOICE_TIME
    rom.write(at + 2, new.to_bytes(2, "big"), expect=old.to_bytes(2, "big"), why="Red's challenge: more time to answer")
    rom.write(FROZEN_WAIT + 2, FROZEN_HOLD.to_bytes(2, "big"), expect=(60).to_bytes(2, "big"),
              why="frozen ending: its line stays before the fade")
    hold = rom.place_code(
        "    move.w #%d,%%d0\n"
        "    jsr 0xE858\n"
        "    move.b #1,0x7861(%%a6)\n"
        "    rts\n" % HAPPY_HOLD, why="happy ending: Fa's yes stays before the fade")
    rom.write(HAPPY_DONE, bytes.fromhex("4EB9") + hold.to_bytes(4, "big"), expect=bytes.fromhex("1D7C00017861"),
              why="happy ending: hold the last line")
    at, frames = ROBOT_LINE2_HOLD
    rom.write(at, bytes([frames]), expect=bytes([63]), why="robot mini boss: NONE OF YOUR WEAPONS ... a shorter hold")
    placed = {}
    for name, ref, old, lines, nxt in RELOCATED:
        if max(len(l) for l in lines) > 30:
            raise SystemExit("text-fixes: %r has a line over 30 characters" % lines)
        placed[name] = at = relocate(rom, old, lines, placed[nxt] if nxt else None)
        if ref is not None:
            rom.write(ref, at.to_bytes(4, "big"), expect=old.to_bytes(4, "big"), why="text: %s (moved)" % " / ".join(lines))
    for ref, old, lines in MOVED:
        text = b"\xfe".join(l.encode() for l in lines).replace(b"?", b"\x0a") + b"\xff"
        at = rom.alloc(len(text))
        rom.data[at:at + len(text)] = text
        rom.write(ref, at.to_bytes(4, "big"), expect=old.to_bytes(4, "big"), why="text: %s (moved)" % " / ".join(lines))
    print("  (text-fixes: already end with ? in the game) %d lines" % len(already))
    for s in skipped:
        print("  (text-fixes: doesn't fit yet) " + s)
