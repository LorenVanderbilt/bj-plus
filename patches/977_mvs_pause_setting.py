NAME = "mvs-pause-setting"
DESCRIPTION = "Arcade (MVS): pausing is an operator setting - PAUSE OFF / ON in the BIOS's game settings, OFF unless set - and a plain pause (no menu)"

# The user, 2026-11-23: on an arcade cabinet a paused game just holds the machine, and Start is how player 2 joins,
# so pausing (pause-start, pause-menu) is an operator's choice there: a seventh soft-DIP, PAUSE, with OFF (the
# default) and ON. Home MVS owners can switch it on in the BIOS's settings. The home console always pauses.
#
# The soft-DIP tables (one for Japan, one for the US and Europe: the header's pointers at SOFT_DIPS) list the
# game's settings for the BIOS's menu: a name, special settings, ten bytes of simple settings (default in the high
# nibble, how many choices in the low; 0 = none) and then their 12-character strings in order. Both tables are
# copied with PAUSE added after the six the game has (the originals sit back to back before code: no room in
# place), and the header points at the copies. The BIOS keeps each simple setting's choice at 0x10FD8A + its
# number, so PAUSE's is PAUSE_DIP (0 OFF, 1 ON).
#
# Pausing starts at pause-start's Start check, called from the game's main loop at CHECK_SITES (pause, unpause):
# while the arcade's PAUSE is OFF those calls report no press. With it ON the arcade gets a plain pause (the user,
# 2026-11-23): PAUSE, the game and music frozen, Start goes on - pause-menu's RESUME / RESTART LEVEL / QUIT TO TITLE
# belong to the home console (quitting would throw a credit away). Its jump at PAUSE_SITE goes to its menu on the
# home console only; the arcade pauses the game's way (PAUSE_PRINT) and waits a frame at a time for the unpause
# check, then PAUSE_END - its own loop, as pause-menu's jump overwrote the start of the game's (0x11AD0). That check
# is a plain new press of player 1's Start: pause-start's also wants bit 0 of 0x106800 (player 1 in the game)
# set, but on the arcade a player 1 game has bit 1 there, so the game never unpaused.
SOFT_DIPS = [0x116, 0x11A, 0x11E]   # the header's soft-DIP pointers: Japan, US, Europe
SIMPLE = 22                  # the simple settings' bytes in a table (after the 16-byte name and 6 of specials)
PAUSE_SETTING = (b"PAUSE", [b"OFF", b"ON"], 0)   # name, choices, default
PAUSE_DIP = 0x10FD90         # BIOS: the 7th simple setting's choice
SYSTEM_MODE = 0x10FD82       # BIOS: 0 the home console
PAUSE_SITE = 0x11ACC         # the main loop's pause: pause-menu's jmp <its menu> (was bsr.w 0x1541A ; jsr 0xE856 ...)
PAUSE_PRINT = 0x1541A        # the game's pause: PAUSE printed, the game frozen (and pause-start's music pause)
FRAME_WAIT = 0xE856          # the game's wait for the next frame
PAUSE_END = 0x15446          # the game's unpause (PAUSE blanked, the game going again)
AFTER_PAUSE = 0x11B16        # the main loop after its pause
CHECK_SITES = [0x11AC0, 0x11B06]   # jsr <pause-start's Start check, as wrapped since> ; nop ; nop (pause, unpause)
PREV_START = 0x10E800        # pause-start's: player 1's Start last frame


def table_end(rom, p):
    """The address just past the soft-DIP table at p."""
    q = p + 32
    for k in (20, 21):                       # the counts' names
        if rom.data[p + k] != 0xFF:
            q += 12
    for s in rom.data[p + SIMPLE:p + SIMPLE + 10]:
        if s == 0:
            break
        q += 12 * (1 + (s & 15))
    return q


def with_pause(rom, p):
    """The table at p with PAUSE_SETTING added as its next simple setting."""
    end = table_end(rom, p)
    table = bytearray(rom.data[p:end])
    simple = table[SIMPLE:SIMPLE + 10]
    k = simple.index(0)
    name, choices, default = PAUSE_SETTING
    table[SIMPLE + k] = default << 4 | len(choices)
    for s in [name] + choices:
        table += s.ljust(12)
    return bytes(table)


def apply(rom):
    copies = {}
    for at in SOFT_DIPS:
        p = rom.u32(at)
        if p not in copies:
            table = with_pause(rom, p)
            copies[p] = rom.alloc(len(table), align=2)
            rom.data[copies[p]:copies[p] + len(table)] = table
        rom.write(at, copies[p].to_bytes(4, "big"), expect=p.to_bytes(4, "big"),
                  why="soft-DIPs: the table with PAUSE (OFF / ON) added")
    for site in CHECK_SITES:
        assert rom.u16(site) == 0x4EB9, hex(site)
        check = rom.u32(site + 2)
        on = "    jmp 0x%X\n" % check if site == CHECK_SITES[0] else """    move.l %%d1,-(%%sp)                | (the unpause: a new press of player 1's Start)
    moveq #0,%%d0
    move.b 0x10FDAC,%%d0
    and.b #1,%%d0
    move.b 0x%(prev)X,%%d1
    move.b %%d0,0x%(prev)X
    not.b %%d1
    and.b %%d1,%%d0
    move.l (%%sp)+,%%d1
    tst.b %%d0
    rts
"""
        gate = rom.place_code(("""
    tst.b 0x%(mode)X                    | the home console: as ever
    beq 1f
    tst.b 0x%(dip)X                     | the arcade with PAUSE ON: on below
    bne 2f
    moveq #0,%%d0                       | the arcade with PAUSE OFF: no press (Z)
    rts
1:  jmp 0x%(check)X
2:
""" + on) % {"mode": SYSTEM_MODE, "dip": PAUSE_DIP, "check": check, "prev": PREV_START},
            why="pause: on the arcade only with PAUSE ON")
        rom.write(site + 2, gate.to_bytes(4, "big"), expect=check.to_bytes(4, "big"),
                  why="the main loop's pause check: the arcade's PAUSE setting first")
    assert rom.u16(PAUSE_SITE) == 0x4EF9
    menu = rom.u32(PAUSE_SITE + 2)
    unpause = rom.u32(CHECK_SITES[1] + 2)
    plain = rom.place_code("""
    tst.b 0x%(mode)X                    | the home console: pause-menu's menu
    bne 1f
    jmp 0x%(menu)X
1:  jsr 0x%(print)X                     | the arcade: the game's own pause
2:  jsr 0x%(frame)X                     | a frame at a time until Start
    jsr 0x%(unpause)X
    beq 2b
    jsr 0x%(end)X
    jmp 0x%(after)X
""" % {"mode": SYSTEM_MODE, "menu": menu, "print": PAUSE_PRINT, "frame": FRAME_WAIT, "unpause": unpause,
       "end": PAUSE_END, "after": AFTER_PAUSE},
        why="pause: the arcade's is plain (no menu)")
    rom.write(PAUSE_SITE + 2, plain.to_bytes(4, "big"), expect=menu.to_bytes(4, "big"),
              why="the main loop's pause: the menu on the home console only")
