# Ice cream truck class prototype

Press Play to open the main menu. Choose **Free drive** for the original system described here, or **Park route** for the automatic-route alternative documented in [ParkRoute.md](ParkRoute.md). Free drive starts inside the truck at 8 AM in a generated neighborhood. Drive near people or switch on the boombox to attract customers, prepare their orders, and meet the quota before 6 PM.

## Controls

| Input | Action |
| --- | --- |
| WASD | Walk, or accelerate/reverse/steer while driving |
| Mouse | Look around |
| Space | Jump while walking; brake while driving |
| E | Open/close the rear door or sit in the driver's seat. While seated and stopped, stand beside the seat. |
| Left click | Pick up, place, serve, or use kitchen equipment |
| Q | Toggle the boombox while carrying it or standing nearby |
| Hold click + move mouse up/down | Scoop ice cream or shake sprinkles |
| Right click | Return a tool; put the boombox on the ground when outside |
| Escape | Pause, resume, or restart the current day |

Put down carried items before driving. The truck stops against houses, trees, and the town boundary. Equipment and cones placed in holders or on the counter travel with it. Walk through the open rear door to enter or leave. There is no cabin teleport key. Customers keep waiting while you walk outside or sit in the parked truck. Driving away releases the queue so customers return home; their normal patience timer still runs while you are outside.

## Preparing and serving

Open the waffle maker, pick up batter, and hold click over the open iron to pour. Put the bottle down, close the lid, and wait for the ready sound. The ring above the waffle maker fills while pouring or cooking, turns green when ready, and turns red if the waffle burns. It faces the player as you move. Open it and click again to take the cone. Leaving it closed too long burns the waffle; open and click to clear it.

Place the cone in a holder. With the scooper, hold click over a tub and move the mouse up and down. The hand reaches that tub and follows a path across its surface. A ball of ice cream grows in the scoop as you work. Reverse direction when you reach either end of the path. Holding still does not add progress. Releasing early clears the partial scoop; finishing returns the loaded scoop to your hand. Click on the cone to add it. Cones support one through three scoops. With the sprinkle shaker, hold click over the cone and move the mouse up and down. All ingredients are infinite.

The front customer's floating bubble shows generated flavor pictures in order from bottom to top, a cone, and any sprinkles. The bubble faces the player. The bottom instruction box, control hints, held-item label, feedback text, duplicate HUD order, and cursor progress ring are hidden. Time and earnings appear in cream cards with clock and coin icons. A mint meter shows progress toward the daily goal. Pause help and day results use matching rounded cards and mint or coral buttons. Pick up the finished cone and click on the customer to serve. A matching order pays immediately. An incorrect order stays in your hand. Click on the bin to discard a cone or empty the scooper.

Residents wait around parks and houses until the parked truck or playing boombox is within range. They follow routes around obstacles to the serving window. Only the front customer can be served. Customers lose patience while waiting, then return home if they leave or receive an order. Parks favor children; residential areas favor adults. Children use a small step at the window.

## Days and quotas

The clock runs from 8 AM to 6 PM. The current interpretation of the requested timing is **12 real seconds per game minute**, making a day two real hours. Change `Seconds Per Game Minute` in the settings to shorten it. A value of 1 gives a ten-minute day.

The first quota is $100. Meeting it shows the results at 6 PM and automatically starts the next day after eight seconds. The next day starts at 8 AM with daily earnings reset and a quota increased by $25. The results button can start the next day sooner. Missing the quota shows a failure screen and requires retrying that day. Pause stops the clock; closing prevents further sales. The sun's direction and color change through the day.

## Tuning

Select `Assets/Settings/PrototypeSettings.asset`. Its Inspector exposes day timing, quotas, walking and jumping, head bob, camera settings, truck speed and braking, steering, attraction radii, NPC speeds and patience, customer return delay, prices, order probabilities, world size and seed, road loops, park frequency, population, and child probabilities.

Default world generation uses 24-meter tiles with 12-meter roads. A randomized connected road network includes straight roads, corners, junctions, and dead ends. Parks, houses, and trees fill the other cells. `Randomize World Seed` creates a different neighborhood each run/day; turn it off and set `World Seed` for a repeatable map. `Junctions Per Side` supports 3 or 5. The generated objects appear under `Generated neighborhood` during Play Mode.

The twelve `FlavorSO` assets in `Assets/Settings` define flavor names, colors, materials, and order pictures. Generated pictures live in `Assets/Art/OrderPictures`; their prompts are in `Docs/OrderPicturePrompts.json`. `CustomerManager` on `Prototype systems` holds the flavor pool, customer variants, and queue references. `WorldGenerator` holds the reusable environment prefabs. `Drivable truck` holds the driving settings, driver and standing points, rear door hinge, cabin bounds, collision bounds, and wheel references.

The driver seat requires a clear interaction ray and a distance of at most two meters from the player. The rear door rotates its existing model and collider around an authored pivot. The player can climb the rear step without jumping.

Tool offsets, holder sockets, colliders, waffle lid rotation, player height, hand poses, and UI remain editable in the scene or prefabs. Each tub has serialized `Scoop Top` and `Scoop Bottom` transforms and a `Stroke Mouse Distance` setting. Move those child transforms to change the hand path. `Waffle progress` is a world canvas under the waffle maker; customer prefabs own their picture bubbles. The HUD and customer picture bubbles are authored UI hierarchies. Each order bubble uses prefab layout components to fit one through three pictures. The HUD panels and icons use editable Unity UI objects and sprites in `Assets/Art/UI`. `Assets/Prefabs/IceCreamCone.prefab` contains the three scoop slots, toppings, and collision meshes for zero through three scoops. `Assets/Art/Workshop.fbx` supplies the models; the Blender workshop remains the master modeling file.

## Scope and verification

This is a single-player prototype with simple flat-ground driving and grid-based pedestrian routing. It does not include restocking, a delivery app, multiplayer, vehicle damage, or a saved campaign between game sessions. Sprinkles are the implemented topping.

`Tools/ExpansionPlaytest.cs` and `Tools/ExpansionFollowupPlaytest.cs` check driving, jumping, road connectivity and seeds, attraction, serving, picture orders, boombox placement, and day transitions. `Tools/PrototypePlaytest.cs` checks the preparation flow. `Tools/ConeTargetingPlaytest.cs` checks exposed tubs behind cones. The tests call the actual input-processing methods and scene raycasts, with scripted gestures and timer advances. Reports and inspected Game-view images are under `Library/CodexPlaytests`.
