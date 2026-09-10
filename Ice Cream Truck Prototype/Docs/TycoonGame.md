# Ice cream tycoon prototype

Run `Builds/ScoopTycoon/ScoopTycoon.exe`, or open `Assets/Scenes/IceCreamTycoon.unity` in Unity and press Play. Keep the whole `ScoopTycoon` folder together when copying the Windows game. The older prototype scenes are still available.

The town now has residential blocks, a market street, town square, playground, gardens, street furniture, and walking residents. The hotbar uses illustrated rounded-square outlines with item pictures. Gameplay instructions and item labels are hidden; the controls below remain available outside the game.

Start with bowls, vanilla, chocolate, a basic scooper, and a bicycle. Press **N** to open. Place a bowl on the pink serving holder, select the scooper, hold the mouse button and swipe vertically through the tub, then click the holder to deposit the scoop. Press **E** to pick up the serving, select it, and click the serving counter. The first two orders pay $6 each. The pink business board sells the $12 improved scooper, which completes a scoop with one swipe.

| Control | Action |
| --- | --- |
| WASD / mouse | Walk and look |
| Shift / Space | Run / jump |
| 1 through 8 / wheel | Select a hotbar slot |
| Left click | Place, deposit, refill, serve, or operate equipment |
| Hold click and move vertically | Scoop ice cream |
| Hold click | Pour batter; move the mouse to apply dry toppings and sauces |
| E | Pick up, open storage, inspect an employee, enter or leave a vehicle |
| F at a vehicle | Open cargo storage |
| Tab / Q | Inventory / drop held item |
| B | Build mode; click furniture, R to rotate, click to place; WASD pans |
| M | Map; wheel zooms, right mouse drags; click a destination |
| N / F5 / Escape | Open the trading day / save / pause |

Preparation has no time limit. Trading runs from 10:00 to 18:00 at one real second per game minute. Workers get up to one extra minute to finish their current orders. The map, pause menu, build mode, and day results pause the simulation. Inventory, shopping, and business menus keep trading active.

Buy supplies at the wholesale building, collect them from the pickup shelf, and carry them home or load the bicycle. Refill packages can be unpacked through storage. Click a stored bowl package to take a working stack; select a matching working bottle before clicking its stored refill. To refill an installed tub, hold a matching refill tub and click it. Only the amount that fits moves. Empty installed tubs can change flavor during preparation.

Stock bars show green remaining and red used, without quantities. The ice cream surface also drops as it is consumed. Internal capacities are 12 bowls, four cones, 24 portions per tub, ten batter uses, and 15 topping uses. Bulk packages hold 30 bowls, 20 batter uses, or 30 topping uses. Tools, bottles, tubs, packages, and prepared servings each occupy their own slot. Player and employee inventories have eight slots; lockers have four, eight, or twelve.

Employees require a hiring fee and an affordable daily wage. Put their scooper, bowls, working batter bottle, and topping containers in their assigned locker. Put spare ice cream in cold storage. They walk to equipment, pour and cook waffles, use serving holders, scoop, apply toppings, and hand over orders. They collect refills when a tub runs low and return unused portions to cold storage. They do not buy supplies. Inspect an employee with E to see their speeds, inventory, status, and locker assignment. Equipment and locker assignment can be changed while off duty.

Sales earn one XP per dollar. At day-end, levels introduce four, eight, then twelve flavors and six toppings. Starter ingredients and empty cooled modules arrive beside the home plot once. Place the modules in build mode and fill them. The home menu uses every unlocked ingredient; secondary locations use up to four installed flavors. Later flavors earn more after ingredient costs.

The business board also sells furniture, a larger bicycle cargo box, a kiosk expansion, the park stand, and the truck. New furniture and expansion extras arrive beside the plot for placement. The truck requires an expanded home kiosk and an employee. Its kitchen travels with it. Drive to either marked selling stop, park, get out, and enter through the rear to prepare orders. A hired driver runs a two-stop route, with up to seven customers per stop. Truck operation costs $12 per day plus the driver's wage. Owning and staffing both stands and the truck completes the prototype's expansion milestone; you can continue trading.

Campaigns save at day transitions, when leaving build mode, with F5, and on quit. The pause menu has a new-campaign button that requires a second click before replacing the current campaign. The campaign file is `tycoon-campaign.json` in Unity's persistent data folder, normally `%USERPROFILE%/AppData/LocalLow/DefaultCompany/Ice Cream Truck Prototype/` on Windows.

This is the agreed prototype scope: two stands and one truck. Traffic, arbitrary wall construction, multiplayer, other dessert categories, and additional trucks are outside this build. Prices and progression pace are initial tuning values. The saved scene and prefabs are the editable source of the game layout; the authoring passes in `Tools/` were used to construct them and should not be rerun over a customized scene.
