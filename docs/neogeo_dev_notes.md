# Neo Geo developer notes (from community threads)

Collected from an X thread (September 2026) by h0ffman (@therealh0ffman, making a Zero Wing port built from a full
disassembly), with replies from other Neo Geo developers. Screenshots were shared in the project chat on
2026-09-29. Relevance to this project is noted under each point.

## Sprite budget
- **96 sprites per scanline** is the hardware limit. Everything counts: the tile-map backgrounds are sprites too
  (full-height strips), as well as the actual objects.
- **380 sprite slots in total.** Besides the per-line limit you need enough slots.
- Sprites at the **left / right edges of the display area still count** toward a line's budget, even when mostly
  off screen.
- A sprite only counts on the lines where it is **active in the display**; off the top or bottom of the screen it
  doesn't count.
- *For us:* `drown-in-front` draws extra sprites on the same lines as the hero while he sinks (the hero and
  splash again, plus about 5 cover strips). In a busy water or lava pit this could push a line past 96 and make
  something flicker or vanish - watch for that when checking the pits. Any future effect that adds sprites
  (parallax layers, the options-screen animation, swimming transparency) has the same budget to respect.

## Wrap-around and the "centre gap" trick
- Sprite positions wrap in both directions: the play field is **512 x 512**, and one sprite can be **16 x 512**
  (32 tiles). Keep moving a sprite down and it reappears at the top.
- Zero Wing's trick: sprites 103-105 start near the bottom of the screen and wrap round to the top, so a single
  sprite covers both a floor piece and a ceiling piece with an empty gap in the middle. Only the visible lines count
  toward the per-line budget.
- *For us:* Blue's Journey's layers are full-height (512 px) strips like this; the level map wraps in a 512 x 512
  VRAM window (see `wall-pocket`'s notes).

## Sticky bit (SCB3) vs individual sprites
- The **sticky bit** in SCB3 chains a sprite to the previous one, so a whole strip of sprites moves with one set of
  coordinates (wiki.neogeodev.org, "Sprites").
- h0ffman **drops chaining and crops the strips** instead: you have to write more positions, but you get more
  sprites out of the budget (each strip only as tall as it needs to be).

## Parallax layers
- Zero Wing's three background layers were regrouped (by tile priority) into the Neo Geo port's **six parallax
  layers** with a custom tool, then the maps were hand-edited to **remove sections hidden behind other layers**, to
  save sprites. Jérémy Lemaire did the same for a Sengoku 2 hack (removing background tiles that were never seen).
- *For us:* relevant to the "More dynamic parallax layers" TODO - any extra layer costs sprites on every line it
  covers.

## Interrupts and hardware vs MAME
- The **timer (line) interrupt** can switch sprites off and on partway down the screen (multiplexing) - more
  complicated and slower. An effect of this kind worked on hardware but not in MAME because of timing differences;
  it needed tweaks to work on both.
- It's said you **always need the anchor point on real hardware** but can get away without it in MAME. Someone
  multiplexed 50 extra enemy bullets this way.
- *For us:* anything timing-sensitive has to be tested on a real console, not only MAME (same as the auto-save
  TODO).

## Source to study
- h0ffman's team's demo **"TTE - Vaporous"**: github.com/grahambates/tte-vaporous-public (timer-interrupt effects).

## NeoGeoSDK (Reddit, r/neogeo, September 2026)
- **NeoGeoSDK** by Eagle Software is an open-source homebrew SDK: a 2D engine (horizontal / vertical scrolling,
  camera, collision and physics, particles, palette effects), its own Z80 / YM2610 sound stack (ADPCM-A/B, FM, SSG),
  build tools, and **EagleBIOS**, an open replacement system ROM. github.com/eaglesoftware777/neogeosdk - a reference
  for how a modern engine drives the hardware (physics, parallax, sound TODOs).
- Their demos ship as **NeoSD `.neo` images** for real AES / MVS hardware (the NeoSD flash cart). *For us:* the
  practical way to test the hack on a real console (auto-save TODO) - hackbuild could write a `.neo` alongside the
  MAME set.

## MAME vs hardware (neo-geo.com forum thread "MAME vs hardware"; DoomGeo)
- MAME is put at roughly 85-90% hardware-accurate for the Neo Geo; the known gaps are **wait states** (some
  graphical glitches), **palette** quirks, sound (PCM2 decryption) and some protection chips' start-up.
- *For us:* `drown-in-front` (the cover strips) and the collision lookup read VRAM from the 68000 (set 0x3C0000,
  read 0x3C0002 straight away) and write sprite blocks during the frame. The original game does exactly this (its
  collision lookup 0xD9B6 reads the front layer back from VRAM the same way), so it should hold on hardware - but it
  belongs on the real-console test list, as do the palette-cycling effects (the shop cursor's light).
- DoomGeo (github.com/sabino/DoomGeo), a Doom-like renderer on the Neo Geo: draws with sprite strips and pre-baked
  graphics, updating the sprite control blocks each frame rather than drawing pixels, HUD on the fix layer.
- General references: Rodrigo Copetti's architecture write-up (copetti.org/writings/consoles/neogeo/), the NeoGeo
  Dev Wiki (wiki.neogeodev.org, e.g. "System ROM", "Sprites"), and the arcade-projects.com "Mark of the Wolves"
  reverse-engineering thread.

## arcade-projects.com "Mark of the Wolves reverse engineering" thread (pages 1-2, via the Wayback Machine)
The live site refuses automated fetches (403); web.archive.org has pages 1-2 (January 2024); pages 3-4 (pasted by
the user, 2025-2026) are only collectors' talk - Garou's final version still can't be reproduced on its own cart
(the NEO-SMA bank switching), flash carts run it - nothing technical. Mostly about getting Garou onto 161-in-1 multi carts (its NEO-SMA bank-switching chip, its 512 KB S ROM -
not our concerns). The useful parts:
- **Finding who writes the screen** (ekorz): watchpoints on the VRAM registers. `wpset 3c0000,2,w,wpdata>7000&&
  wpdata<7500` stops on every VRAM address set in the fix layer area, showing the writing PC; the data then streams
  to $3C0002. *For us:* the same thing we do with Lua write taps on 0x3C0000 / 0x3C0002 (tracking the address,
  logging the PC) - the MAME debugger version for interactive use.
- **Eyecatcher** (wiki.neogeodev.org "Eyecatcher", "68k program header"): header byte $114 picks who draws the boot
  logo (0 = the BIOS), $115 is the upper byte of the logo's sprite tiles. *For us:* Blue's Journey has $114 = 0,
  $115 = 0x5F, so the BIOS logo uses tiles 0x5F00-0x5FFF - not the low tiles (spare-tiles skipped the blank runs at
  0x26 and 0x5B on that worry; they could be freed too).
- Tools named: Matt Greer's sprite / tile viewer (neospriteviewer.mattgreer.dev, shows tile numbers), YYCHR (an
  S ROM fix tile editor), aluzed's MiSTer / DarkSoft ROM set generator (github.com/aluzed/MiSTer-Neogeo-Rom-Decrypter),
  and Nicole Express's "high-speed coding on the Neo Geo" write-up (nicole.express/2021/high-speed-coding-neo-geo.html).
- NeoGeoDev wiki pages it leans on: "VRAM", "Sprites", "Fix bankswitching" (only for games with a big S ROM).
