NAME = "continue-question"
DESCRIPTION = "Continue screen: CONTINUE? with a question mark (and a space before its countdown)"

# The continue screen prints CONTINUE in the big two-row font with the inline printer (PRINT: jsr 0x9FE6, then the
# top row's address 0x7085, 0xFC 0x56, its characters, 0xFE, the bottom row's address, its characters and 0xFF).
# The big font's tiles are 0x600 + the character byte, with the bottom half 0x10 on, and its ? is 0xCE / 0xDE. The
# countdown is drawn separately from column 13. There's no room for a ? in place, so the print now calls TEXT (the
# same text with the ?, one column left, making CONTINUE? 08) and branches past the old text.
PRINT = 0x346A2
OLD = bytes.fromhex("4EB900009FE67085FC56838F8EA4898EA585FE7086939F9EB4999EB595FF")
AFTER = PRINT + len(OLD)              # the code just past the old text
TOP, BOTTOM = 0x7065, 0x7066          # column 3 (was 4), rows 5 / 6
TOP_CHARS = [0x83, 0x8F, 0x8E, 0xA4, 0x89, 0x8E, 0xA5, 0x85, 0xCE]   # C O N T I N U E ?


def apply(rom):
    assert bytes(rom.data[PRINT:PRINT + len(OLD)]) == OLD and AFTER % 2 == 0
    top = ",".join("0x%02X" % c for c in TOP_CHARS)
    bottom = ",".join("0x%02X" % (c + 0x10) for c in TOP_CHARS)
    text = rom.place_code("""
    jsr 0x9FE6
    .word 0x%(top_at)X
    .byte 0xFC,0x56,%(top)s,0xFE
    .word 0x%(bottom_at)X
    .byte %(bottom)s,0xFF
    .even
    rts
""" % {"top_at": TOP, "bottom_at": BOTTOM, "top": top, "bottom": bottom}, why="continue screen: CONTINUE?")
    rom.write(PRINT, bytes.fromhex("4EB9") + text.to_bytes(4, "big") + bytes.fromhex("6000") +
              (AFTER - (PRINT + 8)).to_bytes(2, "big"), expect=OLD[:10], why="continue screen: CONTINUE? printed")
