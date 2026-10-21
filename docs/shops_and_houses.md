# Shops and houses, level by level

Read from the ROM (2026-10-20), not from a hint file, unless marked. Item names and prices are as in the hack
(`text-fixes`, `shop-prices`); the original's names and price mismatches are at the end.

## Houses (NPC rooms)

A house door leads to one of the game's room routines: a 32-entry table at 0x132BC, indexed by 0x103C01. Only 10
entries have a room behind them (0, 1, 2, 4, 5, 6, 8, 9, 17, 18); the rest are a bare `rts`. So there are exactly 10
houses, and each level below has at most one.

| Level | House | What it does |
|---|---|---|
| Jungle 1 | Boatman | sells a boat; ride it to a silver cocoon |
| Lower Earth 1 | Magician | a trick for 5 flowers; say you liked it and he gives honey (nectar) |
| Lower Earth 2 | Travel agent | warps to the last area of Lower Earth, Empire Marsh or Mechanical City |
| Lower Earth 3 | Ret | leaf-throwing duel; beat him for the torch (room 4) |
| Empire Marsh 1 | A man | asks if you're Blue; say yes and he tells you the quiz man's name * |
| Empire Marsh 2 | Quiz man | give his name: prize is a higher flower cap, or never losing flowers on death |
| Empire Marsh 3 | Card game | pick the same card as him; 2-1 against, pays double |
| Mech City 2 | Drunk ("derelict") | keep listening: a silver cocoon or 30 flowers |
| Mech City 3 | Frozen princess | hard to find (stay low); Ret's torch melts her ice; protects from Nero's magic (room 18) * |
| Strange Space (one of 1-3) | Axe man | fetch his axe (a little to the left); he cuts a tree hiding an invisible gold cocoon * |

\* Level from the hint file ([blues_journey_secrets.md](blues_journey_secrets.md)); the others are checked against
the level (0x103005) in a save made at the door (sta/aes: boatman, magician_house, travel_agent, ret_house, quiz_in,
marsh3_cards, derelict_house). The user knows where all of them are.

Not houses (other code): the clover shops (below), the game of chance after each boss (the ocarina wins 1st prize),
and the secret flower rooms.

## Shops

Each shop is a hidden door placed in the level (object types 0x60-0x63, set up at 0x49110; the level object lists
come from the per-stage table at 0x60502). It appears only after a clover has been used (0x107026 / 0x107426) and Blue
comes near. The type's low 2 bits are the shop's variant (0x1078F6), which picks its stock and prices.

| Level | Shop | | Level | Shop |
|---|---|---|---|---|
| Jungle 1 | variant 0 | | Mech City 1 | - |
| Jungle 2 | - | | Mech City 2 | variant 0 |
| Lower Earth 1 | variant 0 | | Mech City 3 | variant 0 |
| Lower Earth 2 | variant 2 | | Mech City 4 | - |
| Lower Earth 3 | - | | Strange Space 1 | variant 0 |
| Lower Earth 4 | - | | Strange Space 2 | variant 0 |
| Empire Marsh 1 | variant 1 | | Strange Space 3 | variant 0 |
| Empire Marsh 2 | variant 1 | | Strange Space 4 | - |
| Empire Marsh 3 | variant 1 | | Daruma 1, 2, 4 | - |
| Empire Marsh 4 | - | | Daruma 3 | variant 3 |

12 shops; none in a 4th (boss) level, nor in Jungle 2.

### Stock and prices (flowers)

Every shop has the same 8 cells: the shopkeeper ("I'M NOT FOR SALE.") and 7 items, the last one differing by variant.

| Item | What it does | Variant 0 | Variant 1 | Variant 2 | Variant 3 |
|---|---|---|---|---|---|
| Nectar | restores 1 heart | 10 | 10 | 10 | 20 |
| Flippers | swim faster | 70 | 15 | 15 | 25 |
| Ice shoes | no slipping | 15 | 70 | 70 | 70 |
| Light safe | keeps items for 1 continue | 20 | 20 | 20 | 20 |
| Super safe | keeps items all game long | 75 | 75 | 75 | 75 |
| Magic wand | dispels the curse | 10 | 10 | 10 | 10 |
| Last cell | | Fern (speed up) 10 | Ocarina (lucky melodies) 5 | Fern 30 | Gold cocoon (1 up) 100 |

Variants by level: 0 = Jungle 1, Lower Earth 1, Mech City 2-3, Strange Space 1-3; 1 = Empire Marsh 1-3;
2 = Lower Earth 2; 3 = Daruma 3.

**Doubled prices:** choosing the shopkeeper's own cell ("I'M NOT FOR SALE.") makes him say STOP JOKING! and sets
the player's +0x1E flag: from then on every shop charges double (the second set of descriptions shows the doubled
prices). The flag clears when that player loses a life (0x3BA4C, the same routine that takes a quarter of the flowers).

Where it lives: buying routines per cell, 0x1FF90 -> shop tables 0x1FFA0 / 0x1FFCC / 0x1FFF8 / 0x20024 (each
routine `move.b #price,d0`, doubled by +0x1E); descriptions 0x20EF4 (8 tables of 8: shop 0-3, each normal then
doubled). Charged and shown prices agree in the hack (checked 2026-10-20).

### The original game

- Names: nectar = FLOWER HONEY, flippers = SWIM FIN, ice shoes = SPIKE, magic wand = ONE SONG, fern = SPRING,
  ocarina = "IT'S TOY.".
- Price mismatches `shop-prices` fixed: flippers in variants 1 and 2 were shown 15 but charged 25; ice shoes in
  variants 1-3 shown 75, charged 70; the light safe in variant 1 shown 25, charged 20.
