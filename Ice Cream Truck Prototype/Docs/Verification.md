# Prototype verification

Verified September 6, 2026 in Unity 6000.3.12f1.

The saved scene is `Assets/Scenes/IceCreamPrototype.unity`. Compilation completed without errors. The final console contained zero errors.

The scripted Play Mode checks use the real interaction raycasts and the same input-processing methods as mouse input. Mouse motions are injected as frame inputs; cooking, patience, and day timers are advanced to test their boundaries without waiting for a full day. These are repeatable gameplay checks, not a performance benchmark or a multiplayer test.

## Observed results

- 102 checks passed across preparation, service, movement, and closing.
- Batter filled the iron, closing started cooking, and the cooked waffle became a held cone.
- Holding without mouse movement did not create a scoop.
- Cones accepted one, two, and three flavors. A fourth scoop was rejected without losing the loaded scoop.
- Sprinkles appeared after the shake gesture. The source's decorative sprinkles were removed from the plain scoop mesh.
- Incorrect orders kept the cone and paid nothing. Correct one-, two-, and three-scoop orders paid $5, $8, and $12 respectively.
- Three completed orders produced $25. One impatient customer left.
- The iron burned after its grace period and could be cleared for reuse.
- Walking moved the CharacterController. The observed camera bob range was about 0.037 meters. Turning head bob off returned the camera to its level position.
- The day stayed open immediately before 6 p.m., closed at 6 p.m., and refused subsequent payments.
- A separate day instance verified success when its editable quota was met.
- The actual results panel displayed 6:00 PM, $25 earned against a $100 quota, three orders served, and one customer lost.
- The Play Again button reset earnings, carried items, and the clock to a fresh 8:00 AM day.
- The Resume button received a pointer click through the HUD raycaster in the player loop and closed the pause panel.

The UI test must run during the player loop. Calling the GraphicRaycaster from an editor command can report the editor window's dimensions instead of the Game view's dimensions. `PrototypeUIPlaytest.ScheduleResume` accounts for that execution context.

Detailed reports and screenshots are under `Library/CodexPlaytests`. The test entry points are in `Tools/PrototypePlaytest.cs` and `Tools/PrototypeUIPlaytest.cs`.

After verification, Play Mode was stopped and the saved scene was left open with `PrototypeSettings.asset` selected. The final scene has twelve tubs, six holders, four customer variants, and no unsaved scene changes. Default settings remain 8 a.m. to 6 p.m., a ten-minute real-time day, a $100 quota, and head bob enabled.

## Cone targeting regression

The former cone collider was a 0.23 × 0.50 × 0.23 meter box. Its top reached 0.49 meters above the cone origin even with one scoop, whose visible top is about 0.296 meters. It also blocked rays beside the rounded silhouette.

`Tools/ConeTargetingPlaytest.cs` passed in Play Mode after replacing that box with shared surface meshes for zero through three scoops. It compares the original box and the new collider against the same camera ray through the actual scene. For every scoop count, a ray blocked by the original box now reaches an exposed tub, and injected click/hold/mouse movement loads that tub's flavor. Clicking the visible cone adds scoops and updates its collider. The test also verifies the three-scoop limit, sprinkles, pickup, and placement.

The four collision meshes contain 156, 726, 1,296, and 1,866 triangles. Instances share those assets; they add no rendered geometry. Placed cones use surface colliders without Rigidbodies, and held cones disable collision. Adding Rigidbody physics later will require revisiting that collider setup.

The report is `Library/CodexPlaytests/cone-targeting.txt`. Compilation passed. The console recorded one FMOD audio-output error on entering Play Mode and no script or collision errors. Play Mode was stopped after the check.

## Driving and neighborhood expansion

Verified September 6, 2026 in the expanded `IceCreamPrototype` scene. The earlier fixed-backdrop and ten-minute-day descriptions above document the original preparation build. Current behavior and controls are in `Docs/Prototype.md`.

- Driving moved the truck 8.08 meters during the acceleration check and reached 8 meters per second. Braking stopped it, reverse moved it backward, steering changed its heading, and a solid test barrier stopped it before overlap. Leaving the seat while moving was rejected. Equipment and a placed cone retained their positions relative to the truck.
- Entry and exit worked. The grounded jump rose about 0.60 meters and landed. The existing preparation test also passed all 38 checks after the equipment was attached to the moving truck.
- Every road connection had a reciprocal neighbor, and all 19 road cells in the tested map belonged to one connected network. Seeds 4312 and 8123 produced different layouts; repeating 4312 reproduced its layout. The actual prefab road-port transforms matched the generated masks and lay on the tile edges.
- Park and residential hotspots spawned children and adults. Idle residents remained stationary. The boombox attracted residents at the initial stop, and the parked truck attracted them with music off after moving to another stop. Customers routed around the truck to the new serving window location.
- Clicking the front customer with a matching cone consumed it, paid the expected amount, and advanced the queue. The final service run paid $5. The picture card displayed three flavor colors in the correct order and requested sprinkles. Boombox pickup, outdoor placement, range, and return to the truck passed.
- The serving queue was moved clear of the ledge. The windshield material was changed to transparent and checked in the rendered driver view. Picture cards were checked in the Game view, including the child serving step.
- At 6 PM, an unmet quota closed service, refused further payments, and prevented advancement. A met quota showed results, waited for the configured delay, then loaded day two at 8 AM with earnings reset and the increased quota. The configured clock rate is 12 real seconds per game minute, or 7,200 seconds per day.
- The final cone-targeting regression passed for zero through three scoops, including scooping exposed tubs, adding scoops, sprinkles, pickup, and placement.

The final console contained zero errors. These checks use the real scene, physics queries, and input-processing methods with scripted inputs and timer advances. They are not a frame-rate benchmark or a claim of exhaustive testing across every world seed. Driving is a flat-ground prototype with swept collision bounds, and pedestrian routing uses a grid.

Reports are in `Library/CodexPlaytests/expansion-*.txt` and `cone-targeting.txt`. Inspected images include `drivers-seat-final.png` and `picture-order-final.png`. Repeatable test entry points are in `Tools/ExpansionPlaytest.cs` and `Tools/ExpansionFollowupPlaytest.cs`.


## Scooping, world indicators, and illustrated HUD

Verified September 6, 2026 in the saved `IceCreamPrototype` scene. The current UI replaces the older text panels described above.

147 scripted Play Mode checks passed across the new scoop/UI tests and the existing preparation regression:

- Holding the scoop still produced no progress. Ten short strokes produced 20% progress and a visible partial scoop with a 0.585 scale. The scoop bowl followed the tub path. All twelve tubs loaded the correct flavor after completed strokes; motion beyond an endpoint added no progress. Releasing, pausing, or putting down the tool cleared partial scoops and restored the hand pose.
- One-, two-, and three-scoop orders displayed the generated flavor pictures in bottom-to-top order. The authored bubble layout resized to its contents, displayed sprinkles only when requested, and followed the camera after its viewing angle changed.
- Hovering the empty waffle maker showed its floating click icon. Cooking advanced the ring, ready batter and waffles showed green, burned waffles showed red, and clearing the iron reset it. The canvas followed the camera after moving around the truck.
- A $25 recorded sale updated earnings and filled 25% of the daily goal meter. The day and clock remained visible. The old instruction box, duplicate order panel, and cursor progress ring remained hidden.
- Pausing stopped play and opened the new menu. Pointer rays reached both menu buttons, and invoking resume closed the panel and resumed play. Missed and met quotas displayed the corresponding results and reachable retry/next-day buttons.
- All 38 existing preparation checks passed: batter, cooking, cone creation, three scoops, rejection of a fourth scoop, sprinkles, and pickup.

The checks use the real scene, interaction raycasts, and scripted frame inputs. Screenshots were inspected for partial scooping, one- and three-scoop orders, the waffle indicator, pause, and results. Compilation succeeded and the final console contained zero errors. Play Mode was stopped after verification.

Repeatable checks are in `Tools/ScoopWorldUIPlaytest.cs`, `Tools/HUDStylePlaytest.cs`, and `Tools/PrototypePlaytest.cs`. Reports and screenshots are in `Library/CodexPlaytests/scoop-*` and `Library/CodexPlaytests/illustrated-*`. The generated picture prompts are recorded in `Docs/OrderPicturePrompts.json`.


## E interaction and walkable rear door

Verified September 6, 2026. Before the fix, entering the driver seat reduced a four-person queue to zero with truck speed still zero. The queue release now happens when the truck actually moves.

66 checks passed across `Tools/TruckInteractionPlaytest.cs` and the existing preparation flow. These include real Input System E/F events, scene raycasts, scripted walking inputs, and mouse gestures.

- The closed rear door blocked the player at x = -3.28. E opened its existing hinge by 105 degrees without changing the player's position. Forward walking crossed the opening to x = -6.28 outside; walking back climbed the rear step and reached x = -2.38 inside. Parent/inside state followed the physical position. The step offset is now 0.45 meters to clear the existing rear step.
- The same customers remained queued when the player walked outside, returned, sat in the parked truck, and stood up. Driving reached 3.2 meters per second and dismissed the queue. Patience still expires normally.
- E while looking away or standing too far from the driver seat did not start driving. Nearby E on the seat sat the player down. E stood them beside the seat after stopping and was rejected while moving.
- A queued F event no longer teleported or seated the player. A queued E event passed through `PlayerInteraction.Update` and picked up the targeted scooper.
- Mouse hold started scooping without an E press. The waffle indicator showed an E key for ordinary use and the mouse icon for pouring.
- All 38 preparation checks passed with E use inputs, including batter, cooking, cone creation, three scoops, fourth-scoop rejection, sprinkles, and pickup.

Inspected images are `Library/CodexPlaytests/rear-door-open.png` and `waffle-e-interaction.png`. Text reports are `truck-interactions.txt`, `truck-keyboard.txt`, and `truck-gesture-indicator.txt` in the same directory. Compilation passed, the final console contained zero errors, and Play Mode was stopped. The saved scene includes the door, driver seat target, standing point, step offset, E indicator, and updated pause instructions.


## Main menu and park route alternative

Verified September 7, 2026 in Unity 6000.3.12f1. The main menu is now the build and Editor Play entry point. Free drive opens the existing scene; Park route opens the separate alternative scene.

197 scripted Play Mode checks passed: 139 route checks, 38 original preparation checks, and 20 original door/driving checks. Inputs use the real interaction raycasts, CharacterController movement, mouse-gesture methods, and UI pointer raycasts. Route and kitchen clocks are advanced in small steps. The success-reward and full-storage checks create known fixtures; they do not claim a naturally earned full-day score.

- Both main-menu buttons received pointer clicks and loaded their respective scenes. Free drive retained twelve tubs, unlimited ingredients, manual driving, and the existing customer manager.
- Planning purchases charged $3 for one strawberry and one sprinkles unit. Two stops and two slow zones filled the control budget and predicted a 07:16 exit. Selecting crowds showed recipes, stock requirements, labor, and availability.
- Three strawberry cones with sprinkles consumed exactly three batter, three strawberry, and three sprinkles units. The serving tray held all three. Exhausted strawberry stock blocked another scoop.
- Pouring, cooking, and scooping also completed while the truck moved more than ten meters and the CharacterController remained grounded aboard. The work spent one batter and one vanilla unit.
- Stop A began at 42 meters. Nearby customers queued at the truck. A window sale banked $9 immediately. Walking out and serving another customer created $9 carried cash without changing the register; walking back aboard banked it.
- A running-route purchase charged $9 for six vanilla units and assigned delivery to stop E after the 45-second readiness time. At E, two units fitted and four overflow units were lost. An order with no later eligible stop was refused without charging.
- The emergency stop lasted 25 seconds and could not be reused after spending the daily allowance. The map left the route clock running; Escape pause froze it. Route placements locked after departure.
- Exiting with the runner outside lost $7, two tray cones, and three packed ingredients. Banked money remained unchanged. Next day preserved stock and the cone left aboard. A separate full-load check preserved six holder cones, three tray cones, and the handheld cone, including their recipes and sprinkles.
- Day two added sports crowds; day three added premium picnics. Poor results retained baseline route controls. Successful results earned one additional rescue stop, and consecutive success never increased that reserve beyond one.
- Free drive passed its 38-check preparation regression and 20-check door/driving regression. Walking out and sitting in the parked driver seat preserved waiting customers; driving dismissed the queue.

Compilation passed and the final console contained zero errors. Inspected screenshots include `mode-main-menu.png`, `route-planning.png`, `route-runner-cash.png`, and `route-left-behind.png` under `Library/CodexPlaytests`. Route reports are `route-*.txt`; the repeatable entries are in `Tools/RouteModePlaytest.cs`. Play Mode was stopped with the saved MainMenu scene open.

This verifies a single-player prototype. Networked co-op, teammate cash transfers, disk saves, performance under multiplayer load, and balance over long campaigns are not implemented or tested.


## Click interactions restored

Verified September 7, 2026. E now applies only to the rear door and driver seat. Left click handles other object interactions; holding the mouse still controls preparation gestures. Both scenes' help and the waffle indicator reflect these controls.

55 focused checks passed. Thirteen used real Input System keyboard and mouse events through Update: E did not pick up the scooper, left click did, clicking did not operate the door or seat, and E opened/closed the door and entered/exited the stopped seat. Five checks verified the mouse indicator and scoop gesture. Thirty-seven preparation checks passed with the iron already open, including cone placement, three scoops, sprinkles, and pickup. Compilation passed and the console contained zero errors. Play Mode was stopped afterward.

## Flavor appearance and object grips

Verified September 7, 2026 in Unity 6000.3.12f1. Both gameplay scenes now use consistent plain or chunky flavors and explicit grips for pickup objects. The cone prefab has its own grip and flavor mesh references.

127 focused checks passed. The 60 flavor checks covered all twelve flavors' tub chunks, partial scoops, loaded scoops, restored cones, and order-picture references. The 27 hand checks picked up the scooper, batter bottle, shaker, cone, and boombox, checked position within 1 mm and rotation within 0.1 degrees, then verified release. Mouse strokes started a mint scoop, moved the hand more than 10 cm, and kept the hand attached while the bowl followed the tub path. Two tray checks confirmed the open supporting pose with three loaded cones. The 38-check preparation regression poured and cooked batter, made a cone, loaded three different flavors, rejected a fourth scoop without losing it, added sprinkles, and picked up the finished cone.

Inspected Game-view screenshots include `grip-scooper.png`, `grip-batter.png`, `grip-sprinkles.png`, `grip-cone.png`, `grip-boombox.png`, `grip-scooping.png`, `grip-tray.png`, and `flavor-cues-game.png` in `Library/CodexPlaytests`. The cream, pink, and green flavor pairs show plain versus chunky scoops side by side. Five revised order pictures were inspected separately. The icons are illustrations, so their chunk locations do not match the mesh vertex positions; their colors and plain/chunky identity agree.

Compilation passed. The final console contained zero errors. Play Mode was stopped with MainMenu open. Repeatable checks are in `Tools/VisualConsistencyPlaytest.cs` and `Tools/PrototypePlaytest.cs`; reports are in `Library/CodexPlaytests`.


## Route map text cleanup

Removed the planning slogan, map instructions, crowd advice, delivery tutorial, and footer rules. The detail panel now shows price, customers, timing, recipe, and missing stock. Shortened labels and compacted the layout.

Compilation passed with zero console errors. Inspected the rendered Editor preview at `Library/CodexPlaytests/route-map-trimmed.png`. Preview-only camera and data changes were discarded afterward. This was a text and layout check, not a gameplay test.

## Orders on the route map

Each crowd location now displays its recipe icons, number of cones, and price per cone. Sprinkles have a separate symbol. The map fills the former side-panel space. Clicking a crowd opens a nearby popup with its time window, arrival time, and missing ingredients. The close button, map background, or same crowd dismisses it.

76 focused Play Mode checks passed using UI pointer raycasts. All A–F buttons remained clickable with four and six crowd cards visible. Changing A to slow changed the popup arrival from 00:30 to 00:47. Buying one strawberry reduced the shortage from three to two. A six-order fixture with three flavors and sprinkles verified all four symbols and a full five-ingredient shortage list. The running route displayed remaining orders. Compilation passed, and both final verification runs produced zero console errors.

Inspected `map-order-cards.png`, `map-order-popup.png`, `map-order-cards-six.png`, and `map-order-popup-full.png` under `Library/CodexPlaytests`. The six-location pictures use a UI fixture, not a played-through later day. The repeatable check is `RouteModePlaytest.MapCards`. Play Mode was stopped at MainMenu. `Tools/AuthorMapOrders.cs` records the one-time scene authoring; do not rerun its `Apply` method over the completed layout.

## Unlimited sprint

Either Shift key now increases movement from 3 to 4.95 m/s. FOV eases from 75 to 80 degrees while moving with Shift and returns when sprinting ends. Both mode settings use a 1.65 speed multiplier and a 5-degree FOV increase. Sprint has no stamina or duration limit.

Verified through the CharacterController on a temporary flat floor and through real Input System keyboard events. Left and right Shift each measured 4.95 m/s; releasing Shift measured 3 m/s. After five simulated minutes of uninterrupted sprint input, speed remained 4.95 m/s. The first 20 ms FOV step reached 76.07 degrees, then approached 80. Standing still with Shift, pausing, and opening the route map returned FOV to 75 without moving the player. Both modes passed. Measurements are in `Library/CodexPlaytests/sprint-verification.json`. Compilation passed with zero console errors; Play Mode was stopped afterward.

## Mixed orders within each crowd

Every location now offers two recipes on day one and three from day two onward. Each recipe has its own quantity, price, flavor sequence, and sprinkles choice. Customers receive one of those orders. Map rows, customer bubbles, serving checks, tray selection, and payouts use that same order. Ingredient totals add the recipes together; during the route, they count only unserved orders.

166 focused Play Mode checks passed. The first birthday party requested three strawberry cones with sprinkles at $9 and two vanilla cones at $7. Its totals were five batter, two vanilla, three strawberry, and three sprinkles, worth $41. The test cooked one of each through normal preparation inputs and confirmed exact ingredient consumption. A vanilla customer rejected the strawberry cone. The tray then selected the vanilla cone for $7 and the strawberry cone for $9. The map changed those quantities from three/two to two/one, and remaining ingredient demand decreased accordingly.

Day transitions verified three distinct recipes per location, the correct customer totals, and later double- and triple-scoop orders. UI raycasts reached A–F with all six locations visible. Inspected `mixed-orders-map.png`, `mixed-orders-after-service.png`, and `mixed-orders-day-three.png` in `Library/CodexPlaytests`. These day transitions ended routes directly; this was not a full campaign playthrough. The checks are in `RouteModePlaytest.MixedOrders` and the report is `mixed-orders.txt`.

Compilation passed and the final console contained zero errors. The Game view was temporarily maximized to prevent another Editor view's dimensions from interfering with pointer raycasts, then restored. Play Mode was stopped at MainMenu. `AuthorMixedMapOrders.Apply` records the one-time layout change and supersedes the earlier single-order layout; do not rerun it over the finished scene.
