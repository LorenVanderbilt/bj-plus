# Blue's Journey - secrets and NPC houses (from John Lynch's hint file, GameFAQs)

Summary of "Blue's Journey Hint File" by John Lynch (GameFAQs, neo/582029-blues-journey, FAQ 4), pasted into the
project chat on 2026-09-29. Level names as the FAQ spells them ("Starge Space" is now STRANGE SPACE in the hack).
Useful for checking the hack doesn't break any of these (the big hero, collision fixes like `wall-pocket`, the
drowning cover) - tick them off as they're checked in play.

## NPC houses ("IN" doors)
- **Jungle 1:** a man sells a boat - buy it and ride it to reach a **silver cocoon** (only reachable by boat).
- **Lower Earth Empire 1:** a magician's trick for 5 flowers - say you liked it and he gives **honey** (health).
- **Lower Earth Empire 2:** a **travel agent** - warp to the last area of Lower Earth, Empire Marsh, or Mechanical City.
- **Lower Earth Empire 3:** rival **Ret**'s leaf-throw duel - beat him for a **torch** (used in Mechanical City 3).
- **Empire Marsh 1:** a man asks if you're Blue - say yes and he tells you the **quiz man's name** (random each game).
- **Empire Marsh 2:** the **quiz man** - answer "I got it", then "one question", then his name. Prize: flower cap
  up to 255, or **never lose flowers when you die** (the FAQ recommends the second). (Found in the ROM too - see
  TODO "Silent flower penalties".)
- **Empire Marsh 3:** a card game - odds 2-1 against, pays 1-1.
- **Strange Space:** a man lost his axe - fetch it (a little to the left), he cuts a tree: an **invisible gold
  cocoon** behind it (shoot around until it appears).
- **Mechanical City 2:** a derelict - keep listening for a **silver cocoon or 30 flowers**.
- **Mechanical City 3:** a hard-to-find house (stay near the bottom) - with Ret's torch, melt the ice around a
  **princess**; she gives protection from Nero's magic.

## Secret rooms / hidden areas
- **Jungle 1:** a little ditch at the bottom - needs the **key**.
- **Lower Earth Empire 1:** right after the first bridge, a stray flower and a hidden entrance - **be small** and
  jump down there.
- **Lower Earth Empire 2** (found by us, not in the FAQ): the one-cell tunnel through the brick wall beside the
  water, for the **shrunk** hero, to a hidden spot ~250 px left (`wall-pocket` keeps the normal hero out of its mouth).
- **Empire Marsh 2:** right after the waterfall, **deep in the water**.
- **Empire Marsh 3:** hard to enter - wade right through the mud (it can't kill you) to a mountain; it's there.
- **Strange Space 1:** after facing Nero, ride the **sinking iceberg** to the bottom, then jump into the passage.
- **Strange Space 3:** underwater **key**, touch the ice blocking a small tunnel; a second key inside; out the other
  side.
- **Mechanical City 2:** a gap in the metal floor near the ground - drop in for the bonus board.
- **Mechanical City 3:** fall between two orange conveyor belts onto the secret room.
- **Daruma Empire 1 - "Mr. NEO-GEO":** after the hot blue lava, go right until you must go down; **get small**, jump
  on the first hovering platform, walk off it to the left and keep holding left through an **invisible wall**.
  "This is not the only invisible wall, there are others throughout the game."

## Other tips from the FAQ
- A second player joining at a boss means you don't restart the boss when you die.
- Jump on the other player's head to reach high spots.
- Shoot around a lot - hidden items pop up.
- **Spike shoes:** only useful in Strange Space 1 and 3. **Fins:** faster left / right swimming, no better control.
- (No details on the LIGHT / SUPER SAFE - see the TODO "Keep the item inventory after dying?".)

---

# From a second GameFAQs guide (neo/582029-blues-journey, FAQ 59677)

## Items (power-ups)
Found in unopened flowers (attack them), hidden underground (attack the ground at random), or bought in a shop
(a clover makes one appear; the same items in every shop). Eight inventory slots; one weapon at a time.
- **Leaf** (up to 3): longer range each time; stuns enemies (pick them up and throw them), hurts bosses.
- **Bomb** (up to 3): stronger each time, thrown in an arc, slow. **Boomerang** (up to 3): short, hurts instead of
  stunning, fast.
- **Clover:** a shop appears in the area. **Key:** opens a secret place nearby.
- **Catfish:** earthquake that stuns all enemies on screen.
- **Ocarina** (shop, 5): always win 1st prize (a heart) in the game of chance after each boss.
- **Light safe** (shop, 25): **some power-ups are kept after dying.** **Super safe** (shop, 75): **more are kept.**
- **Spike** (shop, 20-75): Strange Space's spikes don't hurt. **Swim fin** (shop, 15-70): swim faster.
- **One song** (shop, 10): lifts the curse. **Pine cone:** briefly invincible. **Stem / spring** (shop, 10): speed up.
- **Honey pot** (shop, 10): some life back. **Pink unbudded flower** (underground): full life.
  **Peach:** full life (confirmed in play, 2026-09-30).
- **Flowers (money), from the ROM's pickup table 0x4BA8A:** pink pair (type 0) +1, white lily (type 1) +10. The
  **purple flower (type 42) is a trap: it takes 10 flowers away** (not below 0), with its own sound and an effect.
  The cabbage is type 10 (the 10,000-point pickup).
- **Lottery after each boss (from the ROM):** 1st prize alternates by boss - bosses 1, 3, 5: **life ball** (frame
  0x326C, an oval gem): **+1 maximum heart** (up to 5); bosses 2, 4: **lucky ring** (frame 0x3268, a gem ring): a
  flag (player +26, shown on the item bar) used only in the ending: when Blue proposes, the princess accepts if a
  random 0-127 is below 64, or 128 with any flowers; the ring adds 64, so with the ring she always says yes even
  if he's broke. Other prizes: silver cocoon, honey (+1 heart), 30 flowers, gold cocoon (1UP), super safe; 4th
  prize 5 flowers.
- **Silver cocoon:** five = 1-up. **Gold cocoon:** 1-up (shop, 200, in Daruma Empire).
- Losing a life: **all power-ups are lost except keys and silver cocoons**, and the guide says all flowers too (the
  ROM takes a quarter - see TODO "Silent flower penalties"; the quiz man's prize stops that).

## Scoring and endings
- End of each area: jump onto the big flower - higher = more points (100-7770), plus time, luck (30+ flowers) and
  enemy (carry one) bonuses. Two flowers in the game are worth 10,000.
- **Five endings:** a high score - Blue proposes and the princess accepts; otherwise she refuses; still cursed by
  Nero - he freezes after proposing; if you met Ret, he appears and duels you: win = Blue marries her, lose = Ret
  does, draw = neither.

## Tips
- Jumping on an enemy (normal size) stuns it under Blue; jumping again kicks it spinning (it can ricochet back).
- Player 2 joining during a boss (even uncontrolled) lets the fight continue through deaths.

## Secret places, more exactly
- Most secret places are a room of flowers to grab quickly before a nasty enemy appears; leaving returns Blue near
  the entrance.
- **Lower Earth Empire 1:** a small passage under the end of the very first bridge.
- **Empire Marsh 2:** past the waterfall, a small passage the **shrunk** Blue can enter.
- **Empire Marsh 3:** near the start, from the right edge of the platform two storeys up, jump right into the lower
  open space - just far enough to land on a tiny platform - then into the small passage in the right wall.
- **Strange Space 1:** past the witch, stand on the narrow platform so it sinks, **shrink**; it leads to a small
  opening in the left wall.
- **Mechanical City 2:** before the first gears, a passage blending into the ground (looks like a step) - enter from
  the left. A mini-boss fight.
- **Mechanical City 3:** straight below the circular moving platforms between the two conveyor belts - free fall.
- **Mr. NEO-GEO (Daruma Empire 1):** at the bottom of the steps, a platform with a stem; shrink, jump left and hold
  left against the wall - Blue passes through it before falling in the lava; Mr. Neo-Geo is further along saying
  "Neo-Geo". Come back the same way.
