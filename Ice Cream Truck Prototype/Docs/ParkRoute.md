# Park route prototype

The main menu offers **Free drive**, the existing game, and **Park route**, the alternative planning and runner system. Both are currently single-player prototypes. Networked co-op, player-to-player cash throws, and teammate handoffs are not implemented in this version.

## Play a day

1. Select Park route. The first day begins with $75 and fourteen leftover ingredient units.
2. Select crowds on the map to compare revenue, recipes, ingredient requirements, total labor, and availability windows. Later days introduce sports surges and premium picnics.
3. Click route points to cycle between pass, slow zone, and stop. Every day includes two stops and two slow zones. The map updates projected arrival and exit times.
4. Buy ingredients before departure. Use Inspect truck or M to close the map and prepare cones. The route does not start until you press Start route.
5. Prepare with the same waffle, scooping, and sprinkles interactions as Free drive. Click the serving tray while holding a cone to load it. The tray carries three cones.
6. Start the route. The truck drives itself. Prepare aboard, open the rear door with E, and walk or jump out to serve crowds. At a stop, nearby customers queue at the window and can be served from inside.
7. Outside sales go into carried cash. Walk back aboard to bank it. Money earned through the truck window is banked immediately.
8. At the park exit, anything carried outside is lost. The results show cash, cones, and packed ingredients lost. Ingredients and prepared cones left aboard carry into the next day.

## Controls

| Input | Action |
| --- | --- |
| WASD / mouse | Walk / look |
| E | Open/close the rear door |
| Left click | Pick up, place, load the tray, serve, or use kitchen equipment |
| Hold left mouse | Pour batter |
| Hold left mouse and move up/down | Scoop or shake sprinkles |
| Right mouse | Return a tool or tray to its truck storage position |
| Space | Jump |
| M | Open or close the route map and shop |
| R | Spend a rescue stop while the truck is moving |
| Escape | Pause |

The map stays live after departure. Escape pauses the route and customer clocks. The driver seat does not override the automatic route in Park route mode.

## Stock and deliveries

There are five ingredients: batter, vanilla, chocolate, strawberry, and sprinkles. One finished cone uses one batter unit, one unit per scoop, and one sprinkles unit if requested. Partial scooping does not spend a scoop unit. Pouring spends the batter unit when pouring begins, so abandoning or burning a waffle wastes it.

Truck storage holds 36 units. Single units can be purchased during planning. During the route, purchases become packs of six with a $3 delivery fee. Orders are ready after 45 seconds and arrive when the truck begins the first subsequent planned stop. If no suitable stop remains, the order is refused without charging. Emergency stops do not accept deliveries. Units that do not fit in storage are lost.

The supply bag can hold six units. Pack buttons move stock from the truck to the runner's bag; those units are unavailable to the kitchen until unloaded. Returning aboard unloads them, subject to storage capacity. Packed supplies left outside at the exit are lost.

## Timing and progression

The authored park route is 450 meters long. The truck cruises at 1.5 m/s and travels at 0.6 m/s within fourteen meters of a slow-zone point. Planned stops last forty seconds. Without controls the route takes five minutes; two full slow zones and two stops make it about seven minutes sixteen seconds, before rescue stops.

Every day includes one 25-second rescue stop. Banking the displayed daily target and returning aboard earns one additional rescue stop for the next day. This reserve is capped at one. The two-stop and two-slow-zone budgets do not increase with success. If the register falls below $40, the next day starts with a $40 recovery fund.

Day one has four opportunities using two crowd types. Day two has six opportunities and adds larger sports surges. Day three adds picnics with fewer, higher-paying, three-flavor orders. Birthday orders are identical for batching; playground children gather around nearby runners and wander; sports customers arrive during a short window; picnic customers stay farther from the road. Hotspot counts and recipes are deterministic for each day.

Labor estimates combine preparation, customer handling, and round-trip travel from the route. They are planning estimates, not guarantees about a player's completion time.

## Assets and tuning

- `Assets/Scenes/MainMenu.unity` is first in the build list and is the Editor Play entry scene.
- `Assets/Scenes/IceCreamPrototype.unity` remains the Free drive scene.
- `Assets/Scenes/ParkRoute.unity` contains the alternative, with its own settings, park, customer prefabs, serving tray, and authored UI.
- `RouteGameManager` on Prototype systems exposes route waypoints, control locations, speeds, stop durations, delivery timing, and budgets.
- `RouteStock` holds capacity, prices, and the three allowed flavor references.
- `Assets/Settings/ParkRouteSettings.asset` controls kitchen and player values for this mode.
- `Tools/BuildRouteMode.cs` records the scene-authoring work. It is a one-time authoring script, not a command to rebuild over manual edits.
- `Tools/RouteModePlaytest.cs` exercises menu navigation, planning, finite preparation, serving, deliveries, losses, moving kitchen work, and next-day carryover.

The park and control locations are fixed in this prototype. The day changes crowd composition and workload. Campaign state is kept while switching days and resets when starting a new Park route run from the menu; it is not saved to disk.
