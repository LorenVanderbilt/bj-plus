# Blue's Journey - game internals

Reverse-engineering notes that aren't tied to one patch (each patch's header comment documents its own
findings). Moved here from TODO.md.

## Hero size and the player
Found from `recordings/powerup.inp` (powerup at frames ~5683-6219); see also patches/020_hero_big_art.py.
- The player state block (0x107000 P1 / 0x107400 P2) has a form byte at +1: 0 = shrunk (C button, half
  size), 1 = normal, 2 = powerup (1.5x). Powerup timer at +0x24 (512 frames). Player objects: P1 0x104000, P2 0x104080.
- Each animation exists in three variants chosen by an "art set" word at object+98: 0 normal, 0x40 shrunk,
  0x80 big. The lookup is at 0x434C4. Hit rectangles (8.8 fixed point): shrunk 3,4 / normal 6,8 / big 9,12.
- The per-frame player update dispatches on the form byte at 0x3BDB8 (0 -> 0x3E824, 1 -> 0x3BFB2, 2 -> 0x40996).
  The white flashing is only the powerup timer toggling a palette byte.
- The sprite drawing routine (main function 0xA426) has separate paths for facing right (flipped, 0xA67A),
  facing left inline (0xA47C-0xA4C8) and zoomed objects (0xA5B2 / 0xA72C); an object's first word is its SCB3 Y
  and second word its SCB4 X, and extra pieces are drawn by 0xAF1C / 0xA7F4.
- Starting at form 2 (patching the `move.b #1,form` sites) makes the hero big but disables the C-button
  shrink, so that approach was dropped.
- The Z80 sound driver (022-m1.m1, code at Z80 0xC000-0xDFFF): NMI 0xD4F5 stores the command at 0xF800;
  dispatcher 0xCE44: 1/3 system, 0x04-0x23 music tracks, 0x24-0xEF sound effects, 0xF0+ special (0xD2DF:
  0xF2 = pause, 0xF3 = resume, 0xFF = stop all). The 68k queues commands with 0xA27A; the wait routine
  0xE856 delivers one per frame.
- The game has two gameplay loops depending on BIOS mode but both use the main loop at 0x11ABC, which
  runs the per-frame update (0x11720) then checks for the pause button. The attract-mode demo uses a
  separate loop at 0x10740.

## The travel agency's ride scene (sta/aes/travel_ticket.sta: press A)
A pseudo-3D flight built from hardware shrinking: Blue's creature is a sprite chain whose shrink (SCB2) steps down
each frame (0xFFF, 0xCD5, 0xAAD, 0x785, 0x55D ... 0x22E over ~4 s) while it moves toward the horizon at the screen's
centre. Its columns alternate neighbouring horizontal shrinks (0xCD5 / 0xDD5) for in-between widths - finer than
the 16 horizontal steps. The pink bubbles (tiles 0x55D0-0x55D2) are drawn several times at different shrinks, small
ones slow near the centre, big ones fast toward the edges (depth by speed). The blue perspective grid's horizontal
lines move toward the camera (the user, 2026-10-07; how - scrolling strips or palette cycling - not yet looked at).
