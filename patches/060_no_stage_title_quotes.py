NAME = "no-stage-title-quotes"
DESCRIPTION = "Remove the quotation marks around the act number on the stage title card (e.g. JUNGLE ZONE \"1\")"

# Each stage's title card text (e.g. "JUNGLE ZONE  \"1\"") is a plain ASCII string in the program ROM,
# one per zone/act combination (6 zones x 4 acts = 24 strings). The act number is wrapped in a pair of
# literal '"' characters; this patch overwrites both quotes with spaces so it just reads e.g. "1".
QUOTE_SITES = [
    (0x147CA, 0x147CC), (0x147F0, 0x147F2), (0x14816, 0x14818), (0x1483C, 0x1483E),   # JUNGLE ZONE
    (0x1486F, 0x14871), (0x148A5, 0x148A7), (0x148DB, 0x148DD), (0x14911, 0x14913),   # THE LOWER EARTH EMPIRE
    (0x1493B, 0x1493D), (0x14963, 0x14965), (0x1498B, 0x1498D), (0x149B3, 0x149B5),   # EMPIRE MARSH
    (0x14A85, 0x14A87), (0x14AAF, 0x14AB1), (0x14AD9, 0x14ADB), (0x14B03, 0x14B05),   # MECHANICAL CITY
    (0x14BD3, 0x14BD5), (0x14BFB, 0x14BFD), (0x14C23, 0x14C25), (0x14C4B, 0x14C4D),   # STARGE SPACE
    (0x14C74, 0x14C76), (0x14C9C, 0x14C9E), (0x14CC4, 0x14CC6), (0x14CEC, 0x14CEE),   # DARUMA EMPIRE
]


def apply(rom):
    for open_q, close_q in QUOTE_SITES:
        rom.write(open_q, b"\x20", expect=b"\x22", why="no opening quote before the act number")
        rom.write(close_q, b"\x20", expect=b"\x22", why="no closing quote after the act number")
