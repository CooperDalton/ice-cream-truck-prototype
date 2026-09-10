# Tycoon validation

Checks use the production game objects and methods in Play Mode. Larger progression and employee checks use explicitly seeded cash, stock, XP, and orders so individual behaviors can be measured. They do not establish the time needed to finish a campaign without test setup.

| Check | Observed result |
| --- | --- |
| Opening bowls | Two recipes consumed one bowl and scoop each and paid $6 each. The $12 purchase delivered the improved scooper. |
| Improved scoop | One 150-pixel input with a 0.01-second duration completed one portion. A separate native mouse drag passed through the actual aiming and input loop and changed stock from 12 to 11. |
| Partial refill and overflow | A full tub transferred only 17 portions into a tub containing seven. A full inventory retained the three bowls that could not fit. |
| Home employee | A rookie walked to the locker, iron, tubs, holder, and serving counter to complete a two-flavor cone with two toppings. Revenue was $16.50, with the expected stock consumption. |
| Supplier and bicycle | The vehicle drove to the supplier and back. Physical purchases were collected, loaded, unloaded, and used to refill home stock. |
| Park employee | An experienced employee filled two tubs from six to 24, used one portion from each, and returned two six-portion refills to cold storage. A bowl with nuts and whipped cream paid $15.50. |
| Truck driver | The driver traveled with the fitted truck, completed a $19.50 cone at the playground and an $18.50 bowl at the residential stop, then ended the route. All four tubs, batter, and topping counts matched the recipes. |
| Building | Outside-plot and occupied placements were rejected. A cooled module was installed on a free grid cell. Rotating a table carried its holder and access point with it. |
| Levels and reload | Crossing all thresholds delivered ten new flavor tubs and six toppings exactly once. Reload preserved the deliveries, placed and unplaced modules, partial refill, supplier package, and bicycle position. |
| Combined business and moving save | The expanded home kiosk, park stand, and fitted truck all passed employee access checks. Opening charged $138 for three employees and truck operation. A save made during the driver's trip restored all staff and attached truck equipment, finished the route, and awarded the expansion milestone at day-end. |
| UI input | Native mouse clicks exercised the new-campaign confirmation and reset. Queued keyboard device events exercised the pause and opening controls. Native mouse movement exercised scooping. |
| Windows player | The 64-bit build succeeded with zero errors. The standalone app restored the combined campaign, displayed complete day results, and accepted two native mouse clicks to confirm a new campaign. The fresh game showed day one, level one, $0, the basic scooper, bowls, and all eight hotbar slots. The 1440 by 900 window kept the HUD and minimap within its bounds. |

Evidence and screenshots are in `Library/CodexPlaytests/Tycoon*.txt`, `.json`, and `.png`. The corresponding `Tools/Tycoon*Playtest.cs`, `*Setup.cs`, `*Verify.cs`, and observation scripts can be run through Unity Pipeline's `eval_file` command in the expected scene and phase. Employee tests must be allowed to run over real frames between setup and verification.

The root-cause checks found and fixed an interaction ray hitting the player's own capsule, a worker accepting a navigation endpoint short of the requested station, prefab changes resetting opening stock, and same-frame save timing around physical deliveries and pickups.

The final editor error log was empty. The standalone player log contained no gameplay exceptions or navigation errors during launch, restore, and reset. The build reported two warnings: Pipeline is disabled in the player, and Unity's bundled DebugOccluder shader reports a vector truncation. The build report is `Library/CodexPlaytests/TycoonWindowsBuild.json`; standalone screenshots and the player log use the `TycoonStandalone` prefix.

No end-to-end campaign pacing claim is made. Reaching every upgrade without seeded resources remains a play-balancing pass. The game is a prototype, with shared character appearances and simple vehicle handling.

The town pass added 27 model types, 773 scenery instances, building footprints on both maps, twelve walking residents, and the illustrated rounded-square inventory frames. Equipment at both stands and all eight customer entries passed navigation checks. The bicycle completed a street route to the supplier pickup and back, and the truck route's swept volume was clear of the new scenery. The final Windows build succeeded with zero errors. Fresh and restored standalone campaigns produced no gameplay or navigation errors. The resident startup check led to delayed agent activation after navigation restoration, and the baked town navigation now has a persistent asset. Evidence uses the `Town` prefix in `Library/CodexPlaytests/`.
