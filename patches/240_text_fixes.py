NAME = "text-fixes"
DESCRIPTION = "In-game text: typo and wording fixes (from docs/in_game_text.csv)"

# The text is stored inline, packed between code and the text engine's control bytes (0xFE new line, 0xFC / 0xFB
# followed by a long, 0xFF end, 0x0A ...), so a line can't grow where it is. Each fix below replaces a phrase
# found near a string's address (docs/in_game_text.md); a longer phrase may only take trailing spaces that end
# its line. Fixes that don't fit are left out (and listed when building) until the text can be moved elsewhere.
# "?" is character 0x0A (tile 0x50A); many question lines already end with it.
FIXES = [   # (string address, old phrase, new phrase)
    (0x2BE3A, "STARGE SPACE", "STRANGE SPACE"),                 # the map screen's area name
    (0x227A6, "IHDECISION", "INDECISION"), (0x227A6, "HOWHERE", "NOWHERE"),
    (0x229D0, "BEAT EMPEROR DARUMA", "BEAT EMPEROR DARUMA?"),
    (0x22F86, "CUT THAT TREE", "CUT THAT TREE?"),
    (0x2323C, "MY HATCHET,", "MY HATCHET!"),
    (0x235B0, "BELIEVE IT", "BELIEVE IT?"),
    (0x260E0, "TAKE THE FLOWERS.", "TAKE YOUR FLOWERS"),
    (0x2630C, "WHAT DO YOU PREFER", "WHAT DO YOU PREFER?"),
    (0x26556, "WANT TO KNOW", "WANT TO KNOW?"),
    (0x26926, "ARE YOU INTERESTED", "ARE YOU INTERESTED?"),
    (0x269A6, "ARE YOU SURPRISED", "ARE YOU SURPRISED?"),
    (0x26C0A, "HERE WE GO.", "HERE WE GO!"),
    (0x26C64, "IS SO THAT.", "IS THAT SO?"),
    (0x26DB2, "DID YOU ENJOY IT", "DID YOU ENJOY IT?"),
    (0x2724A, "THE TRAVEL AGENT", "THE TRAVEL AGENT?"),
    (0x27392, "WHERE ARE YOU GOING", "WHERE ARE YOU GOING?"),
    (0x27620, "GRAB A RIDE", "GRAB A RIDE?"),
    (0x280C2, "LOSTER.", "LOSER."),
    # each player's continue prompt by the HUD (centred in 14): CONTINUE? (the continue screen's own: `continue-question`)
    (0x12005, "   CONTINUE   ", "  CONTINUE?   "), (0x1265B, "   CONTINUE   ", "  CONTINUE?   "),
    (0x28168, "AWAY FROM ME", "AWAY FROM ME?"),
    (0x281E0, "CHOICE.I'LL FIGHT.", "CHOICE. I'LL FIGHT"),
    (0x2C6C6, "TIME FOR CARDS", "TIME FOR CARDS?"),
    (0x2CCD6, "ENOUGH FLOWER.", "ENOUGH FLOWERS"),
    (0x2D3FE, "UNTERSTAND", "UNDERSTAND"),
    (0x2DF7E, "I TATE", "I DATE"),
    (0x2E42E, "WUTH", "WITH"),
    (0x2E964, "IS THAT SO", "IS THAT SO?"),
    (0x2E970, "ON YOUR HAND.", "ON YOUR HAND?"),
    (0x2F3A6, "WHAT CAN WE DO", "WHAT CAN WE DO?"),
    (0x32D70, "CAN YOU BEAT ME", "CAN YOU BEAT ME?"),
    (0x54551, "JUMP !", "JUMP! "),
    (0x54799, "THE DUMP WILL", "THE LEAF TO"),
    (0x547BD, "OVER RUN THE", "STUN YOUR"),
    (0x547E1, "ENEMYS.", "ENEMIES."),
    (0x5484F, "THE ENEMY.", "A STUNNED ENEMY"),
    (0x54899, "THE FLOWER IS", "THE FLOWERS ARE"),
    (0x548E1, "HUNG ON TO IT.", "HANG ON TO THEM"),
    (0x34986, "BAD GUY.", "YOU JERK"),                  # YOU JERK! doesn't fit
    # the lottery after each boss
    (0x2971D, "OKEY,I BET.", "LET'S PLAY!"), (0x2971D, "I'LL PASS.", "NO THANKS."),
    (0x29B02, "FIRST PRIZE!", "1ST PRIZE!"), (0x29BF0, "2ND PRIZE.", "2ND PRIZE!"),
    (0x29CDC, "3RD PRIZE.", "3RD PRIZE!"), (0x29DF0, "4TH PRIZE.", "4TH PRIZE!"),
]

# Whole strings rewritten in their own space: the new lines, then the original's ending (an end byte, or a
# callback: 0xFC + the code's address, which doesn't move), the rest padded after it (never read).
STRINGS = [
    # the hint about the riddle man (one per name): QUESTINS, his name, and a few words shortened to make room;
    # LOVES TO QUIZ. is now LOVES RIDDLES. (2026-10-24)
] + [(addr, ["IN THE SHABARN MARSH EMPIRE", "YOU'LL FIND AN OLD MAN WHO", "LOVES RIDDLES.", "HE'LL HELP YOU",
             "IF YOU ANSWER HIS QUESTIONS", "HIS NAME IS %s." % name])
     for addr, name in [(0x22B88, "POPOPPE"), (0x22C92, "PIKKYURU"), (0x22D9A, "PUKAMONME")]] + [
    # his name, as the quiz's answers: HOHOPPEY / PECULU / PUCAMONMME, romanized again from the Japanese
    # (ポポッペー, ピッキュル, プカモンメ)
    (0x261CA, ["  POPOPPE", "  PIKKYURU", "  PUKAMONME"]),
    # his greeting's choices (the greeting itself is in RELOCATED: quiz_greeting), closer to the Japanese (クイズじいさん, "Quiz Grandpa"; わかった / いやだ！)
    (0x25E66, ["  GOT IT!", "  NO WAY!"]),
    # his first question: a giveaway (he's asked just the one) - was FIRST QUESTION IS, HOW MANY / QUESTIONS HAVE
    # YOU ANSWERED (zero, as worded; the Japanese is the old "question 1: which question is this?" joke) - and its
    # answers (was ONE QUESTION. / TWO QUESTIONS. / SEVENTY QUESTIONS; the first is right; the box takes 14)
    # The riddle man (2026-10-24): "which riddle is this?" keeps the Japanese joke and stays true however many times
    # he's pleaded first, which HOW MANY QUESTIONS HAVE I ASKED wasn't after a turn-down. The first answer is right
    (0x25F28, ["FIRST RIDDLE! WHICH RIDDLE", "IS THIS?"]),      # no colon in the font: it shows an A
    (0x25FAE, ["  THE FIRST", "  THE SECOND", "  WAIT...WHAT?"]),
    # his last: his name, asked as a grandpa's riddle (was YOU DID A GOOD JOB. / LAST QUESTION, WHAT IS MY NAME) -
    # the answers still his names, the hint's the right one
    (0x2613C, ["WHO'S THE WISEST, MOST", "HANDSOME MAN IN THE MARSH?"]),
    # turning him down: he asks three times, each with these choices (was NO, I WON'T. / YES, I WILL.; turned down a
    # third time, he lets you go): his second plea (was WHAT DO YOU WANT TO KNOW?, a mistranslation), his third (was
    # I'M PERSISTENT, LET'S PLAY.); his first is in RELOCATED (quiz_sure)
    (0x264D8, ["  I'M SURE.", "  OK, I'LL TRY"]),      # the box takes 14
    (0x2D824, ["  KEEP LISTENING.", "  SNEAK AWAY."]),   # the drunk's (was YOU'RE STILL LISTENING. / YOU BETTER LEAVE SOON.)
    # his prizes: the second now keeps the flowers through a game over (losing a life no longer takes any:
    # keep-flowers-on-death) - was FLOWERS WILL REMAIN EVEN AFTER DIE.
    (0x263A2, ["  YOU'LL GET UP TO 255 FLOWERS.", "  NEVER LOSE FLOWERS.", "  I WANT NOTHING."]),
    # winning: was GREAT! YOU'RE A GENIUS. / I'LL MAKE YOUR DREAM COME TRUE. - DREAMS, the first line's full stop
    # giving it room (his box takes the prizes' 37)
    (0x262B0, ["GREAT! YOU'RE A GENIUS", "I'LL MAKE YOUR DREAMS COME TRUE."], 37),
    (0x26556, ["COME ON, JUST ONE RIDDLE?"]),
    (0x26632, ["PRETTY PLEASE? JUST ONE?"]),
    # the story cinema (the box takes 33: FA WAS OVERCOME BY THE POLLUTION. at 0x358A2)
    (0x34BA8, ["THE PLANET RAGUY WAS ONCE", "BEAUTIFUL."]),
    # (BUT... - was BUT......: text-pause, its dots one at a time)
    (0x34DCA, ["THEN THE DARUMA TRIBE", "INVADED,"]),
    (0x34E6E, ["AND THEIR POLLUTION GETS", "WORSE EVERY DAY."]),
    (0x35710, ["THIS IS BLUE,", "A MASTER OF THE", "LEAF DUMP."]),      # LEAF DUMP kept: a fan favourite
    (0x357E2, ["BLUE LOVES PRINCESS FA", "OF RAGUY'S ROYAL FAMILY."]),
    (0x358A2, ["FA FELL ILL FROM THE POLLUTION."]),
    (0x3595E, ["BLUE, DRIVE OUT THE DARUMA", "AND BRING RAGUY BACK TO LIFE!"], 33),
    # (after "THEN WHAT'S BURNING ON YOUR HAND?") IN FACT,I SET HIM FREE. / NO I DIDN'T
    (0x2EA02, ["  HEH, OKAY, IT WAS ME.", "  NO, I DIDN'T!"]),   # was FINE, I SET HIM FREE. - she asked whether he freed her
    # the magician's opener (was LOOK MY MAGIC. / IT'S ONLY 5 FLOWERS.); his box takes 27, as the quiz hint's
    (0x26A88, ["WANT TO SEE A TRICK?", "ONLY 5 FLOWERS"], 27),
    (0x26BC8, ["NO FLOWERS, NO SHOW. SHOO!"]),     # the magician, too few flowers (was GO BUCK IF YOU'RE NOT BUYING.)
    (0x26AEC, ["  SURE!", "  NO THANKS."]),                       # was I'LL LOOK. / I WON'T LOOK.
    (0x26ED4, ["YOU MAKE ME HAPPY.", "TAKE THIS NECTAR WITH YOU."]),  # was ... HONEY ..., as the shop's NECTAR
    # the boatman's menu (his question, YES and NO: RELOCATED, boat_ask / boat1 / boat_warn)
    (0x22462, ["  A LEAF BOAT, PLEASE.", "  A MUD BOAT, PLEASE.", "  NO THANKS."]),   # ASK FOR LEAF MADE BOAT ...
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
    (0x2F2B8, ["NONE OF YOUR WEAPONS CAN", "EVEN SCRATCH HIM."]),   # was YOU CAN'T HURT HIM WITH ANY OF / YOUR WEAPONS.
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
    (0x2724A, ["NEED A RIDE SOMEWHERE?"]),                 # was WILL YOU USE THE TRAVEL AGENT?
    (0x2744C, ["  10 FLOWERS", "    TO THIS AREA'S BOSS", "  20 FLOWERS", "    TO THE EMPIRE MARSH",
               "  60 FLOWERS", "    TO THE MECHANICAL CITY", "  NO THANKS."]),   # was USE 10 FLOWERS TO GET TO / ...
    (0x27620, ["HEY! NO FREE RIDES!"]),      # too few flowers (was ARE YOU GOING TO GRAB A RIDE?; Japanese: a fare dodger!)
    (0x27660, ["ALL ABOARD!"]),                            # was O.K. LET'S GO.
    (0x27362, ["COME AGAIN!"]),                            # was COME AGAIN.
    (0x32E9B, [" YES, SIR!", "  DREAM ON!"]),       # after its 0x11, the cursor
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
    # the lottery after each boss (its box: 14 letters - a 15th touches its right rim)
    (0x29900, ["OK! MAYBE", "NEXT TIME."]),                        # I SEE. / SEE YOU LATER.
    (0x29958, ["SORRY! IT'S", "10 FLOWERS."]),
    # the lottery's super safe prize (was SUPER SAFE. / THIS PROTECTS / ITEMS FOR 3 / STAGES FROM / THE NEXT STAGE.):
    # item-keep made it last the whole game
    (0x2A246, ["SUPER SAFE!", "YOUR ITEMS ARE", "SAFE FOR THE", "WHOLE GAME."]),                             # NO. / YOU DON'T HAVE / 10 FLOWERS.
    # the later lotteries' intro (was THIS IS A / REWARD FOR / SETTING US FREE / A LOTTERY / DREWING.: its 15-letter
    # line touched the box's right rim - 14 at most; lines padded to 13 but the last, as the original's)
    (0x295E6, [l.ljust(13) for l in ["THIS IS A", "REWARD FOR", "FREEING US,", "A LOTTERY"]] + ["GAME."]),
    (0x29F26, ["SORRY!", "NO PRIZE"]),                             # OH. / SORRY MISS.
    (0x2A036, ["LIFE BALL", "1 MORE HEART."], 15),                     # +1 maximum heart
    (0x2A08A, ["SILVER COCOON", "FIVE OF THEM", "FOR A 1UP."]),
    (0x2A0E0, ["NECTAR", "RESTORES", "1 HEART."]),                 # HONEY. / STAMIRA RECOV- / ERS.
    (0x2A132, ["LUCKY RING", "IT WILL BRING", "YOU LOVE."]),       # the princess always says yes
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


# The safes' shop texts (item-keep changed what they do): longer than their space, so new strings - the price line
# kept - and the shops' description tables (DESC_TABLES: 4 shops x normal / doubled x 8 cells) pointed at them.
SAFE_TEXTS = [   # (the original texts - each price variant -, name, description lines)
    ([0x211B0, 0x211DA, 0x213AE, 0x213D8], "LIGHT SAFE", ["KEEPS ITEMS", "FOR 1 CONTINUE"]),
    ([0x21204, 0x21402], "SUPER SAFE", ["KEEPS ITEMS", "ALL GAME LONG"]),
]
DESC_TABLES = (0x20EF4, 0x20FF4)


def safe_texts(rom):
    for addrs, name, desc in SAFE_TEXTS:
        for old in addrs:
            price = bytes(rom.data[old:old + 64]).split(b"\xfe")[1]
            text = b"\xfe".join([name.encode(), price] + [l.encode() for l in desc]) + b"\xff"
            new = rom.alloc(len(text))
            rom.data[new:new + len(text)] = text
            for at in range(DESC_TABLES[0], DESC_TABLES[1], 4):
                if rom.u32(at) == old:
                    rom.write(at, new.to_bytes(4, "big"), expect=old.to_bytes(4, "big"),
                              why="shop text: %s %s" % (name, price.decode().strip()))


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
    tail = bytes(rom.data[end:end + {0xFF: 1, 0xFC: 5, 0xFB: 9}[rom.data[end]]])   # 0xFB: next text, then a callback
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
    (0x2012A, 0x20198, ["NICE TRY.", "YOU CAN'T", "AFFORD IT."]),      # was   YOU CAN'T /   BUY IT.
    (0x2012E, 0x20198, ["NICE TRY.", "YOU CAN'T", "AFFORD IT."]),
    (0x2013A, 0x20230, ["COME BACK", "WHEN YOU'RE", "RICH!"]),          # was I WON'T TALK / TO POOR.
    # the ocarina's two prices (was IT'S TOY.; it gets the lottery's 1st prize for a song: ocarina-song)
    (0x20F50, 0x21006, ["OCARINA", "5 FLOWERS", "  LUCKY", "  MELODIES"]),
    (0x20F70, 0x21022, ["OCARINA", "10 FLOWERS", "  LUCKY", "  MELODIES"]),
    (0x2C852, 0x2C89C, ["  TELL ME", "  NO"]),        # was   YES /   NO; the first explains the rules
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
RELOCATED = [   # name, where its address is (an lea's operand) or None, old address, new lines, the 0xFB next by name
    # the endings (Japanese as a guide)
    # the riddle man's house: answering that you're not Blue (was I THOUGHT IT WAS SOMEONE ELSE - 31 wide on one line)
    ("quiz_not_blue", 0x22A5A, 0x22A8A, ["SORRY, I THOUGHT YOU WERE", "SOMEONE ELSE"], None),
    # his greeting, after his laugh (was I'M THE QUIZ MAN. / YOU GET TWO QUESTIONS. / YOU'LL LOSE ALL YOU FLOWERS /
    # IF YOU CAN'T ANSWER ONE.; クイズじいさん, "Quiz Grandpa"). He's the riddle man since 2026-10-24. His lines kept
    # their lengths (RELOCATED text goes in free space - longer or shorter would move every later patch's code), the
    # greeting's first padded with spaces
    ("quiz_greeting", 0x25C6A, 0x25DC0, ["I'M THE RIDDLE MAN!  ", "ANSWER MY TWO QUESTIONS", "TO WIN. MISS ONE AND I'LL",
                                          "GET ALL YOUR FLOWERS!"], None),
    # ... and turning down his quiz (was ARE YOU SURE / YOU'LL LET ME QUIZ YOU?)
    ("quiz_sure", 0x25EE2, 0x26472, ["ARE YOU SURE YOU DON'T", "WANT MY TWO RIDDLES?"], None),
    # Red's duel for the torch: his greeting (was ... A LONG TIME TO SEE YOU.)
    ("red1", 0x27ADE, 0x27C92, ["BLUE, I'VE BEEN WAITING", "A LONG TIME TO SEE YOU AGAIN.", "DON'T TELL ME YOU FORGOT ME!"], None),
    ("red_challenge", 0x27D9E, 0x27E24, ["I CHALLENGE YOU TO A", "LEAF DUMP DUEL!"], None),   # was FIGHT ME.
    # Mechanical City 2's drunk (飲んだくれ - "the derelict" in English) and his grumbling, closer to the Japanese:
    # the beer's price (was THE PRICES ARE RISING ALONG / WITH THE TAXES.), the two-player games (was WE CAN'T WASTE
    # TIME BY PLAING / GAMES. - Blue's Journey is one), Raguy for Bakeen
    ("drunk_intro", 0x2D36C, 0x2D53C, ["YOU SEE A DRUNK SLUMPED OVER", "A MUG OF BEER.", "WHAT ARE YOU GOING TO DO?"],
     None),
    ("drunk_hey", 0x2D624, 0x2D68A, ["HEY, YOU THERE...", "C'MERE. LISTEN TO THIS."], None),
    ("drunk_slaves", 0x2D726, 0x2D786, ["THOSE DAMN DARUMAS... THEY", "MADE SLAVES OUTTA ALL OF US!"], None),
    ("drunk_raguy", 0x2D876, 0x2D8C4, ["RAGUY'S ALREADY FALLEN TO 'EM.", "RESISTANCE? HAH!"], None),
    ("drunk_tried", 0x2D914, 0x2D960, ["WE TRIED. DIDN'T DO A", "LICK OF GOOD."], None),
    ("drunk_beer", 0x2D9D8, 0x2DA3C, ["AN' NOW THEY'VE JACKED UP THE", "PRICE OF BEER! HIC"], None),
    ("drunk_games", 0x2DAC4, 0x2DB3C, ["AN' WHAT'S WITH ALL THESE", "TWO-PLAYER GAMES NOWADAYS?!"], None),
    ("drunk_sorry", 0x2DBBE, 0x2DC2C, ["SORRY, PAL. ALL I DO IS GRIPE.", "HERE, TAKE SOMETHIN' FOR",
                                       "YER TROUBLE."], None),
    ("drunk_prize", 0x2DC8A, 0x2DCD4, ["  30 FLOWERS.", "  A SILVER COCOON.", "  I JUST WANT TO LEAVE."], None),
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
    ("end12", 0x24A5A, 0x24CB6, ["BLUE... MAKE FA HAPPY,", "OKAY?"], None),                  # Blue won the duel
    ("end13", 0x24A76, 0x24E96, ["WAHAHA! FA IS MINE!", "SO LONG, BLUE!"], None),            # Red won
    ("end14", 0x24F4C, 0x24FA0, ["BLUE NEVER RECOVERED", "FROM THE SHOCK."], None),
    ("end15", 0x24B2A, 0x24B7E, ["I'M SORRY... I CAN'T CHOOSE", "BETWEEN YOU."], None),       # a draw
    ("end15b", 0x24C12, 0x24C62, ["NEITHER OF THEM EVER", "RECOVERED FROM THE SHOCK."], None),
    ("end16", 0x23704, 0x237BE, ["BLUE COLLAPSED, AND RAGUY", "WAS RUINED BY POLLUTION.", " " * 30,
                                 " " * 12 + "GAME OVER"], None),                         # BLUE IS EXHAUSTED AND ...
    # the boatman, after his question - YES (was IT'S GOOD IF YOU KNOW IT.)
    ("boat1", 0x223AE, 0x22596, ["GOOD, THAT SAVES MY BREATH.", "MY BOATS ARE FOR RENT!"], None),
    # ... and his question, the first line anyone hears in a house (was SEE THE LARGE RIVER AHEAD?; his Japanese
    # has an old man's voice: おぬし、この先に大河があるのを… - "you there, (know) there's a great river ahead?")
    # ... and after NO, his warning (was THE BIG RIVER IS POLLUTED. / YOU WILL DIE IF YOU FALL IN. / YOU CAN CROSS IT
    # BY USING IVY. / MANY PEOPLE HAVE DIED TRYING. - the IVY is the swinging vine; Japanese: rope) and his pitch (was
    # FOGET THAT IDEA. / YOU SHOULD USE MY BOAT.), chained (0xFB) - the pitch first, so the warning can point at it
    ("boat_pitch", None, 0x22718, ["SO SAVE YOURSELF THE TROUBLE.", "RENT ONE OF MY BOATS!"], None),
    ("boat_warn", 0x223EA, 0x22664, ["THEN LISTEN UP, LAD! THAT", "RIVER IS POLLUTED. ONE DIP", "AND YOU'RE DONE FOR. SOME",
                                     "SWING ACROSS ON THE VINE...", "MOST DON'T MAKE IT."], "boat_pitch"),
    ("boat_broke", 0x22528, 0x2280C, ["NO FLOWERS, NO BOAT, GET OUT!"], None),   # was YOU HAVE RUN OUT OF MONEY.
    ("boat_ask", 0x21AFC, 0x21C12, ["AHOY THERE, LAD! HEARD ABOUT", "THE GREAT RIVER UP AHEAD?"], None),
    # the lottery host after each boss: the Japanese opens with "we're a family of travelling merchants", which the
    # English left out (so its THEY CAPTURED US DURING A TRIP. came from nowhere) - a third text chained in front
    ("lot3", None, 0x295E6, ["THANKS FOR", "FREEING US!", "10 FLOWERS FOR", "A LUCKY DRAW!"], None),  # THIS IS A REWARD ...
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
    ("robot4", 0x2F420, 0x2F45A, ["...IF ANYONE HAS A CHANCE,", "IT IS YOU."], "robot5"),           # I'M NOT HURT.
    ("robot3", 0x2F376, 0x2F3A6, ["THEN HOW CAN I BEAT HIM?!"], None),                           # WHAT CAN WE DO? (Blue)
    ("robot1", 0x2F08C, 0x2F228, ["YOU WIN, BLUE... BUT EMPEROR", "DARUMA IS FAR STRONGER.", "HIS STRENGTH IS DRIVEN BY",
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
        text += b" "              # the callback's long on an even byte; the text starts on one
    text += bytes(tail)
    at = rom.alloc(len(text), align=2)
    rom.data[at:at + len(text)] = text
    return at


# A text that ends in 0xFB (show the next text) waits 63 frames (0x21832: move.b #63,0x78A8(a6)) - for every such
# chain. The card game's rules are long: before its PLACE YOUR BET. they wait longer; so is the boatman's warning
# about the river (4 lines), before his next line.
LONGER_WAITS = {0x2CA0E: 123, 0x2C9F2: 123,       # next text (English, Japanese) -> frames
                "boat_pitch": 210, 0x226E2: 210,    # a name: RELOCATED's, where it was moved to
                0x2F2B8: 123, 0x2F284: 123}       # (the robot mini boss's first line, before NONE OF YOUR WEAPONS ...)
# ... and its next line then waits less before the scene moves on: its callback's object counts down from this
ROBOT_LINE2_HOLD = (0x2F30D, 31)              # 63
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
        end = at + room
        while rom.data[end] == 0x20:
            end += 1
        if room > len(old) and rom.data[end] not in (0xFE, 0xFF, 0xFB, 0xFC):   # a space between words isn't spare
            room = len(old)
        if len(new) > room:
            skipped.append("0x%X %r -> %r (%d more characters than fit)" % (addr, old, new, len(new) - room))
            continue
        text = new.ljust(room).encode().replace(b"?", b"\x0a")
        rom.write(at, text, expect=bytes(rom.data[at:at + room]), why="text: %s -> %s" % (old, new))
    safe_texts(rom)
    for addrs, name, desc, orphan in SHOP:
        for addr in addrs:
            text, room = shop_text(rom, addr, name, desc, orphan)
            rom.write(addr, text, expect=bytes(rom.data[addr:addr + room]), why="shop text: %s" % name)
    for addr, lines, *width in STRINGS:
        text, room = whole_string(rom, addr, lines, *width)
        rom.write(addr, text, expect=bytes(rom.data[addr:addr + room]), why="text: %s" % " / ".join(lines))
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
    hold = rom.place_code("""
    move.w #%d,%%d0
    jsr 0xE858                          | wait d0 frames
    move.b #1,0x7861(%%a6)
    rts
""" % HAPPY_HOLD, why="happy ending: Fa's yes stays before the fade")
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
    src = "    move.b #63,0x78A8(%a6)\n"      # the chain's usual wait; longer before the texts LONGER_WAITS names
    for i, (nxt, frames) in enumerate(LONGER_WAITS.items(), 1):
        src += """
    cmp.l #0x%(text)X,0x78A4(%%a6)
    bne.s %(n)df
    move.b #%(frames)d,0x78A8(%%a6)
%(n)d:
""" % {"text": nxt if isinstance(nxt, int) else placed[nxt], "n": i, "frames": frames}
    wait = rom.place_code(src + "    rts\n", why="text chains: longer waits before some texts")
    rom.write(CHAIN_WAIT, bytes.fromhex("4EB9") + wait.to_bytes(4, "big"), expect=bytes.fromhex("1D7C003F78A8"),
              why="text chains: the wait, longer before some texts")
    for ref, old, lines in MOVED:
        text = b"\xfe".join(l.encode() for l in lines).replace(b"?", b"\x0a") + b"\xff"
        at = rom.alloc(len(text))
        rom.data[at:at + len(text)] = text
        rom.write(ref, at.to_bytes(4, "big"), expect=old.to_bytes(4, "big"), why="text: %s (moved)" % " / ".join(lines))
    print("  (text-fixes: already end with ? in the game) %d lines" % len(already))
    for s in skipped:
        print("  (text-fixes: doesn't fit yet) " + s)
