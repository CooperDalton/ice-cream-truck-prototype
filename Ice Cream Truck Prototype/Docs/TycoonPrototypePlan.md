Planning draft, revised September 9, 2026. Workers collect equipment and consumables from an assigned locker into their own eight-slot inventory, then physically prepare orders at grid-placed equipment and serving holders. Players also have an eight-slot inventory and hotbar. Lockers have four, eight, or 12 slots. Sales earn XP; day-end level rewards introduce required ingredients with free starter supplies. Flavors progress from two to four to eight to twelve, with six topping options introduced through levels. Ingredient access is never purchased. The improved scooper completes a portion in one mouse swipe. Each newly unlocked flavor increases both selling price and contribution after ingredients. One real second equals one in-game minute. Prices, XP thresholds, and action speeds remain initial tuning values; progression timing needs validation against worker movement and player-built layouts.

I recommend a first-person, single-player prototype that starts at a bowl stand and reaches two staffed locations plus one truck. The first employee should let the player leave for supplies while sales continue. That is the moment the player starts managing a business. Keep the first upgrade inside a minute and aim for a first employee around the end of day two. Withdraw the earlier 55-to-70-minute completion estimate until physical employee work, grid layouts, the inventory, and eight-minute days have been tested together.

The second stand and truck are both part of the intended prototype. They are alternative investments after the first location works. Test both purchase paths: investing in a second staffed stand first, or saving directly for the truck.

This is the original planning document. The implemented prototype and controls are described in [TycoonGame.md](TycoonGame.md), with observed checks in [TycoonValidation.md](TycoonValidation.md).

The current project gives us a substantial starting point.

| Existing work inspected | Use in the tycoon prototype |
| --- | --- |
| Physical scooping, waffle preparation, carrying, counter placement, serving, picture orders, and first-person hands | Preserve the tactile preparation loop; add bowls, equipment upgrades, and strict grid placement |
| Driveable truck, door, seat, installed kitchen, and neighborhood assets | Make the truck an earned purchase |
| Park route mode with finite ingredients and an automatic route | Reuse relevant stock and route behavior, with local inventories and employee operation |
| Bicycle, pop-up stand, serving cup, supply boxes, crates, carton, and cooler in the model inventory and saved previews | Adapt these assets before building replacements; their models do not establish working gameplay |
| Six house prefabs, trees, roads, parks, and character variants | Build a compact authored neighborhood from the existing kit |
| Original day manager and saved settings | Replace quota retries with persistent cash and ownership; the saved settings currently produce a 20-minute day |

Sources inspected include `Assets/Settings/PrototypeSettings.asset`, `Assets/Scripts/Managers/DayManager.cs`, `Assets/Scripts/Managers/CustomerManager.cs`, `Assets/Scripts/IceCreamTub.cs`, `Assets/Scripts/RouteStock.cs`, `Docs/ParkRoute.md`, `Art/REMAINING_MODELS.md`, `Art/MODEL_BUDGET.md`, and saved art and Game-view images. Some older prose predates the current implementation. For example, `Docs/Prototype.md` describes a two-hour day, while the saved settings use two seconds per game minute, giving 20 minutes. Neither existing mode saves a campaign to disk.

Unity status returned no connected Pipeline instance, and another thread held the repository Unity lock. Inspection used files and saved images, without launching, changing, or testing the live game.

The opening should teach one action at a time.

| Moment | Player experience |
| --- | --- |
| Start | Own a small stand, bicycle, basic scooper, 16 paper bowls, 12 vanilla portions, and 12 chocolate portions. Cash is $0. No waffle equipment or cones. |
| First customer | Walks up within five seconds of opening and requests one vanilla scoop in a bowl. Pays $6. |
| Second customer | Arrives three seconds after the first sale and requests one chocolate scoop in a bowl. Pays $6. |
| First upgrade | Spend the $12 on the improved scooper. The new tool appears in its holder, and the next scoop needs one deliberate stroke instead of three. |
| First supply trip | Close the sign and collect bowl and ingredient refills before the opening supplies run out. The bicycle has four cargo slots. |
| First day-end level reward | At 60 lifetime XP, receive strawberry, mint, one full 24-scoop tub of each, and a basic cooled two-well module. Delivery is free and the next day's required home menu contains four flavors. |
| Early day two | Buy the waffle station. A cone order visibly pays $4 more than its equivalent bowl. |
| Further level rewards | At 150 lifetime XP introduce sprinkles and chocolate sauce. At 300 XP add four flavors. Rewards can cross multiple levels at one day-end. |
| End of day two | Hire the first employee for the following morning. |
| Day three onward | Leave on a supply run while the employee uses their issued equipment and consumes supplies from their inventory and the stand. Return to increased cash and decreased stock. Aim for all twelve flavors to unlock around the end of day three or four, subject to measured earnings. |

The first six orders contain one scoop. Afterwards use 70% single scoops and 30% doubles at stands. Bowls can contain mixed flavors; flavor counts matter, placement order does not. Keep the existing picture orders, with a clear bowl or cone symbol and the total sale value. An incorrect serving remains in the player's hand for correction or disposal.

Normal scooping should feel deliberate immediately. The basic tool requires three short strokes. The $12 improved scooper completes one full portion in one continuous mouse swipe across the tub's scoop path. It requires no reversal, second pass, or minimum hold duration. A completed directional sweep produces the whole scoop even if the swipe takes less than one second; small back-and-forth jitter does not count as a completed sweep. Change the tool's appearance as well as its gesture effort. Do not deliberately make the starter interaction unpleasant to sell the upgrade. Measure full serving time during play instead of guaranteeing a total duration. A further scooper tier is deferred until the first upgrade has been tested.

Use these menu prices and purchase packs.

| Product | Customer price |
| --- | ---: |
| One basic scoop in a bowl | $6 |
| Two basic scoops in a bowl | $9 |
| Waffle cone instead of bowl | Add $4 |
| Each strawberry scoop | Add $1 |
| Each mint scoop | Add $2 |
| Later flavor scoops | Add the premium specified in the flavor table below |
| Requested topping | Add the price specified in the topping table below |
| Sale at the park stand | Add $1 per order |
| Truck order at a designated mobile stop | Add $3 per order |

The two location surcharges never stack. Prices stay fixed in this prototype so we can tune demand and production without adding price elasticity. A two-scoop basic cone costs $13 at the home stand and $16 at a truck stop.

| Supply | Pack price | Usable quantity | Cost per use |
| --- | ---: | ---: | ---: |
| Paper bowls | $6 | 30 bowls | $0.20 |
| Vanilla tub | $12 | 24 scoops | $0.50 |
| Chocolate tub | $12 | 24 scoops | $0.50 |
| Strawberry tub | $18 | 24 scoops | $0.75 |
| Mint tub | $24 | 24 scoops | $1.00 |
| Batter carton | $12 | 20 cones | $0.60 |

The starting tubs are half full. A fresh purchased tub always contains 24 scoops. Bowls include disposable spoons in their pack, so there is one packaging counter to manage. Every sellable item consumes supplies. Equipment lasts permanently. Do not add electricity, tool wear, or equipment repairs to this prototype.

A basic bowl contributes $5.30 after ingredients and packaging. A basic cone contributes $8.90, an extra $3.60 for the additional preparation. The generous margins deliberately put money into frequent upgrades. Payroll and expansion then give that money somewhere to go.

Ingredient progression uses business XP, not cash purchases. Earn one XP per $1 of completed customer sales across the player and all employees. Count each sale once when paid, including its recipe and location premiums. Accumulate fractional XP from half-dollar prices rather than rounding each transaction. Buying supplies or paying wages does not remove XP. Grants, returned items, asset resale, and moving money do not award XP.

XP accumulates during the trading day. At closing, apply every level whose lifetime XP threshold has been reached and show the rewards in the day-end results. These thresholds are cumulative, not an additional amount required at each level. A player may gain several levels in one day. There is no guaranteed level simply for advancing the calendar, so skipping empty days cannot unlock ingredients.

| Business level | Total XP required | New required ingredients | Total unlocked flavors | Free starter delivery |
| --- | ---: | --- | ---: | --- |
| 1 | 0 | Vanilla and chocolate | 2 | Original opening stock |
| 2 | 60 | Strawberry and mint | 4 | One full 24-scoop tub per new flavor and one basic two-well cooled module |
| 3 | 150 | Rainbow sprinkles and chocolate sauce | 4 | Both working containers full at 15 portions each |
| 4 | 300 | Cookie cream, cherry, coffee, mango | 8 | One full tub per new flavor and two basic two-well cooled modules |
| 5 | 500 | Cookie crumbs and caramel sauce | 8 | Both working containers full at 15 portions each |
| 6 | 750 | Blueberry, peach, pistachio, blue moon | 12 | One full tub per new flavor and two basic two-well cooled modules |
| 7 | 1,100 | Chopped nuts and whipped cream | 12 | Both working containers full at 15 portions each |

Make the free level delivery available at the home business's marked receiving area before the next opening. It does not require a supply trip, a fee, an empty locker slot, or paying to claim it. Use a short delivery arrival presentation, then let the player unload the actual rewards. Packages remain at the receiving area if storage is full. Give each reward once per campaign, including after reload; save delivery and claim state. Later replacement tubs, refill packs, spare working containers, and equipment for additional workers must be purchased normally.

The free basic cooled modules are stable freestanding equipment that can also be supported by compatible counters. The player chooses their grid positions. Their thin entry-level form supplies the required new wells without forcing a countertop purchase merely to accept a level reward. The starting plot must fit a compact arrangement of the complete required home menu, one preparation area, the waffle option, and a reachable small locker; verify that layout before fixing plot dimensions. More spacious layouts, additional workers, and storage remain reasons to buy expansion. There is no four-flavor cap.

New ingredients join the primary stand's required menu on the next trading day, regardless of whether the player would prefer to hide them. They remain part of its demand pool after their starter stock runs out. The player can open with missing stock, but customers asking for unavailable recipes leave and count as lost sales; the game does not replace those requests with easier orders. This creates a reason to stock the whole required menu. Installing reward equipment and loading containers happens during the existing untimed preparation phase.

For this prototype, the primary stand carries the complete level-driven menu. The second stand and truck can serve smaller location menus suited to their installed capacity, selected from globally unlocked ingredients. This avoids requiring twelve tub wells in the starter truck. The single campaign starter delivery goes to the primary stand; opening another location does not duplicate past level rewards. The waffle iron remains a purchased physical appliance; cones enter a site's demand only when it has that appliance and holders. Required flavor and topping progression works in bowls, so it never depends on buying the optional cone workflow.

| Flavor | Selling premium per scoop | Tub price for 24 scoops | Single bowl price | Ingredient and bowl cost | Contribution per single bowl |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vanilla or chocolate | $0 | $12 | $6 | $0.70 | $5.30 |
| Strawberry | $1 | $18 | $7 | $0.95 | $6.05 |
| Mint | $2 | $24 | $8 | $1.20 | $6.80 |
| Cookie cream | $2.50 | $30 | $8.50 | $1.45 | $7.05 |
| Cherry | $3 | $36 | $9 | $1.70 | $7.30 |
| Coffee | $3.50 | $42 | $9.50 | $1.95 | $7.55 |
| Mango | $4 | $48 | $10 | $2.20 | $7.80 |
| Blueberry | $4.50 | $54 | $10.50 | $2.45 | $8.05 |
| Peach | $5 | $60 | $11 | $2.70 | $8.30 |
| Pistachio | $5.50 | $66 | $11.50 | $2.95 | $8.55 |
| Blue moon | $6 | $72 | $12 | $3.20 | $8.80 |

Apply premiums per scoop in mixed orders. A vanilla-and-mint double bowl costs $11; a double mint bowl costs $13. Label contribution before wages and overhead, not guaranteed daily profit. Higher flavor complexity comes from stocking another product, arranging its tub, and walking to it; it does not need an arbitrary extra preparation timer. Older advertised flavors remain in the order pool. Flavor and topping pictures must remain distinguishable as the menu expands; color alone is insufficient.

Add six toppings through three level rewards, using three distinct preparation motions. Toppings work on bowls and cones. Each requested topping adds its listed sale premium once per serving, consumes one measured portion, and adds the corresponding visible topping layer.

| Topping | Add to sale | Refill price | Portions | Contribution per application | Physical action |
| --- | ---: | ---: | ---: | ---: | --- |
| Rainbow sprinkles | $1.50 | $6 | 30 | $1.30 | Shake the dispenser over the serving |
| Chocolate sauce | $2 | $9 | 30 | $1.70 | Squeeze while moving across the scoops |
| Cookie crumbs | $2 | $9 | 30 | $1.70 | Shake the dispenser over the serving |
| Caramel sauce | $2.50 | $12 | 30 | $2.10 | Squeeze while moving across the scoops |
| Chopped nuts | $2.50 | $12 | 30 | $2.10 | Shake the dispenser over the serving |
| Whipped cream | $3 | $15 | 30 | $2.50 | Hold the nozzle over the serving and pipe a swirl |

Toppings unlock for free at levels three, five, and seven, in the pairs listed above. Each reward includes one reusable working container per new topping, filled with 15 portions. Once that supply is consumed, purchase the corresponding 30-portion refill at the price in the table. Refills do not make additional working containers. Extra empty working containers cost $4 each so the player can equip additional employees. There are no topping license or pack-unlock fees.

Use roughly one second of shaking, 1.5 seconds of drizzling, or 1.2 seconds of piping as initial reference motions at 100% employee finishing speed. Add finishing speed to the worker stats independently of scooping and pouring. Use 80%, 100%, and 125% for the example rookie, experienced, and expert profiles. For players, use a short shake gesture for dry toppings, a held squeeze and sweep for sauces, and a held nozzle for cream. No new precision-scoring minigame is needed. Debit the portion when application begins, preserve partial application state if interrupted, and complete the visible layer only when the action completes. Resuming that application must not consume a second portion or award an extra sale premium.

At level three, 40% of new home orders request one topping and 60% request none. From level five, use 45% with one, 25% with two, and 30% with none. Keep a maximum of two distinct toppings per serving, with no more than one dry topping and no more than one sauce; whipped cream can pair with either. Workers retrieve only the containers needed for the next order. Exact topping selection matters, but the application order does not. Generate requests from the required menu first, then check unreserved supply and accessible equipment. Missing a required topping loses that potential sale rather than converting it to an easier order. The same rules apply to toppings selected for a secondary location's menu.

The waffle process remains physical: pour for one second, close the iron, cook for six seconds, open and take the cone. Allow another ten seconds after cooking before burning. Opening the ready iron stops burning. A cone rack holds three finished empty cones, allowing preparation between customers. Measure additional handling time through the actual sequence; cooking can overlap other work. Start cone demand at 40% of new orders when the station is stocked and ready. The first purchase includes an empty working batter bottle, a 20-portion carton, and the three-slot rack. Empty additional batter bottles cost $4 each.

Moving empty bowls between a package, locker, and inventory changes their owner and stack counts without consuming them. Assign one real bowl to the serving when preparation starts; do not spend another bowl when placing or serving it. Debit a scoop when the scoop completes and batter when a pour begins. An unfinished scoop consumes nothing. Burning or discarding loses the ingredients already used. Tub surfaces and durability bars show remaining supply visually. Model labels identify ingredients without quantity numbers. Report a stock warning at six scoops, six bowls, four batter portions, or five topping portions.

Consumable items show remaining supply with the requested green/red bar. The green portion is remaining quantity divided by capacity; the red portion is the used quantity. A full container is all green, half full is half green and half red, and empty is all red. Do not print counts, fractions, percentages, or capacity numbers on models or beside durability bars. This represents remaining contents, not tool damage. Scoop tools, tables, and other permanent equipment do not wear out or need refilling.

Show bars beneath consumable item icons in the player hotbar, worker inventory, lockers, and cargo/storage inspection. Bowl stacks and sealed packages show remaining supply with a bar only. Empty consumable containers remain visibly empty rather than displaying a misleading full bar. Prepared servings show their recipe contents, not a durability meter. When looking at an installed tub or working bottle, show the same bar without numbers in its interaction UI. Do not cover the whole kitchen in permanently floating meters.

A working batter bottle holds ten portions. After five waffle pours its bar is half green and half red, with no numeric text. A carried refill tub and an installed serving tub each hold up to 24 scoop portions. Ice cream tubs are individual inventory items that occupy one of the player's or worker's eight slots; they do not stack. This supersedes the earlier bulky-only tub rule. They also fit cold storage and the bicycle or truck cargo slots. Quantities in the balancing tables and transfer examples are internal simulation values, not model labels or durability text.

To refill, select a carried tub and click an installed tub of the same flavor within reach. Transfer the smaller of the source quantity and the target's missing capacity. If the target has 7/24 and the source has 24/24, transfer 17 portions: the target becomes 24/24 and the source remains 7/24. If the target has 20/24 and the source has 3/24, the target becomes 23/24 and the source empties. A full target or mismatched flavor transfers nothing and gives a clear hint. Refilling never replaces the installed object, resets its flavor, duplicates stock, or discards leftover portions. An empty installed tub retains its flavor assignment; changing that assignment is a separate preparation/build action allowed only when empty.

Use one deliberate click followed by a short visible transfer motion. Player and employee refills use the same quantity rule; reserve the target for the transfer so two operators cannot fill it at once. If the interaction is interrupted before transfer completes, neither quantity changes. The example transfer motion can start around 0.8 real seconds, subject to animation testing. One click transfers what fits, rather than requiring a click per portion. An exhausted disposable refill tub disappears from its inventory slot; the permanent installed serving tub remains at zero when depleted. The inventory UI shows source and target supply bars while aiming, without numeric text.

Drive the installed ice cream surface height from its actual portion count. At 24/24 it is near the rim, at 12/24 halfway through the usable fill depth, and at 0/24 the tub interior is exposed with no scoopable surface. Keep the tub rim, exterior, and collider fixed while lowering the ice cream surface and its side volume. Clip or otherwise contain the fill within the tub's inner shape. Scooping hand targets follow the current surface rather than scooping empty air at the original full height. Animate the surface change briefly after a scoop or refill; the internal portion count is authoritative. Color, chunks, and flavor detail move with the fill. Use the same remaining-quantity model for carried refill tubs when their contents are visible.

One real second equals one in-game minute. Keeping opening at 10 AM and closing at 6 PM gives 480 real seconds, or an eight-minute trading day. If those opening hours change later, day duration follows the same fixed clock scale. Cooking, movement, gestures, and employee action durations remain specified in real seconds; a six-second waffle cooks for six displayed game minutes. Before opening, the player can take unlimited preparation time, shop, load supplies, set staff assignments, and choose what to sell. No customers arrive and no income accrues during preparation. The first tutorial skips the need to prepare. Pause stops every location, vehicle, customer, and wage timer together.

At closing, finish orders already being prepared, then release the remaining queue without a closing-time penalty. Show sales, supplies used, stock purchases, wages, upgrades, cash change, and lost sales separately. Profit and available cash are different because unopened supplies remain inventory. The player chooses when to begin the next day. There is no escalating quota failure or automatic campaign reset.

Save cash, lifetime XP, current business level, day number, purchases, ingredient unlocks, unclaimed level deliveries, employee contracts and locker assignments, all location stock, cargo, player and worker inventory slots, locker tier and contents, selected hotbar slot, placed layouts, partially prepared servings, and outstanding supplier purchases at day boundaries and on save-and-quit. For a mid-day save, preserve the trading clock and consumed ingredients; resuming must not award sales again, refill supplies, or repeat a claimed level reward. Keep the town layout fixed across days.

Use an eight-slot personal inventory shown as a hotbar. For the first pass, these eight slots are the entire personal inventory, with no additional backpack page. Select slots with keys 1 through 8 or the mouse wheel; Tab opens the same eight slots for rearranging and inspecting items. Inventory inspection during trading leaves the world running. Only the selected item is visibly held. Switching slots stows the previous item and equips the new one.

Use the same stack limits in player inventories, worker inventories, and lockers for every item those containers accept. Larger lockers add slots, not larger stacks. Distinguish the number of objects in a slot from the portions inside one container.

| Small item | Maximum objects per inventory slot | Contents of each object |
| --- | ---: | --- |
| Empty paper bowls | 12 | One empty bowl |
| Empty cooked waffle cones | 4 | One empty cone |
| Filled bowl | 1 | Its exact scoops, toppings, and preparation state |
| Filled cone | 1 | Its exact scoops, toppings, and preparation state |
| Basic or improved scooper | 1 | Empty, or one loaded scoop |
| Working batter bottle | 1 | Up to 10 cone portions |
| Ice cream refill tub, any unlocked flavor | 1 | Up to 24 scoop portions |
| Rainbow sprinkle dispenser | 1 | Up to 15 portions |
| Chocolate sauce bottle | 1 | Up to 15 portions |
| Cookie crumb dispenser | 1 | Up to 15 portions |
| Caramel sauce bottle | 1 | Up to 15 portions |
| Chopped nut dispenser | 1 | Up to 15 portions |
| Whipped cream can | 1 | Up to 15 portions |

Tools and bottles never stack, even when empty or filled to identical levels. Empty bowls and empty cooked cones stack only with identical items. Adding the first ingredient to one empty serving separates that item from its stack. Filled food stays unstackable even when two orders match. Stacking does not permit preparing food inside an inventory. Bottles retain their remaining contents, and a loaded scooper retains its portion when stowed. Switching items never refills, empties, duplicates, or serves them. Completed scoops consume stock at preparation, not again when switching slots. Switching during an incomplete scoop cancels that attempt without awarding a portion; it cannot evade ingredient already consumed during a pour.

| Bulk supply | Maximum packages per storage or cargo slot | Contents of each package | Allowed storage |
| --- | ---: | --- | --- |
| Bowl pack | 1 | 30 bowls | Locker, supply shelf, vehicle cargo |
| Batter carton | 1 | 20 cone portions | Locker, supply shelf, vehicle cargo |
| Topping refill, each of the six types | 1 | 30 portions of that topping | Locker, supply shelf, vehicle cargo |
| Ice cream refill tub, each of the twelve flavors | 1 | 24 scoops when full | Also fits one player/worker inventory slot; cold storage or vehicle cargo for reserve stock |

Only the original vanilla and chocolate opening tubs start half full at 12 portions each. Level-reward tubs and purchased replacement tubs both contain 24 scoops. Supply pack quantities and replacement prices are unchanged. A full batter carton fills a 10-portion bottle twice; a topping refill fills its 15-portion container twice. A 30-bowl package can supply stacks of 12, 12, and six. Workers withdraw only enough to bring their carried bowl stack to 12 and refill bottles to capacity. Any remainder stays in the source package, using its existing slot. A partly used package cannot stack with another package.

Bulk packages remain single storage objects while opened; withdrawing 12 bowls from a pack leaves one pack containing 18, not 18 loose bowls forced into the locker. Decanting into personal inventory still obeys the 12-bowl limit. An empty working bottle stays as a reusable item in its slot; an exhausted disposable supply package is removed without creating a mandatory trash task. Refill containers only from a matching supply package. Do not merge two partially filled working bottles through a drag operation.

When transferring a stack, move only the quantity that fits into compatible existing stacks and free slots. Leave overflow with its source, and animate the source and target supply bars. A full destination never consumes the source. Equipment and furniture remain individually owned build parts or bulky carried objects and cannot stack in a locker or personal inventory. For bike cargo, one owned furniture part occupies one cargo slot under the prototype's existing abstract cargo rule; it never becomes a stack of furniture.

Dedicated equipment capacities are separate from inventory stacking. The bowl dispenser holds 30 bowls. The three-position cone rack holds three cones total, one per position, even though four empty cones fit a personal inventory slot. A preparation holder contains one serving. An installed tub well contains one tub, never a stack of tubs. Track object counts separately from remaining uses internally. Display remaining contents with a bar without numeric text.

Sealed bowl packages, batter cartons, topping refill packages, and furniture remain bulky cargo carried one at a time with inventory items stowed. They do not fit in personal slots. Ice cream refill tubs are the explicit exception and occupy one personal slot each. Vehicle slots provide additional tub capacity without occupying tool and serving slots, as well as carrying the bulk packages. Working bottles are also portable. Build mode places parts already owned and present at the current business, rather than teleporting another site's furniture through the hotbar.

Picking up a small item transfers that same item into a compatible stack or free slot. If the inventory is full, it remains in the world with a clear message. Dropping the selected item removes it from its slot and makes it a loose physics object. Deliberate placement moves it into the world, but no longer makes an arbitrary countertop tool available to staff. Transfer staff supplies into their assigned locker. Workers cannot use anything in the player's inventory, including stowed tools. Show a missing-tool status if the only scooper is in the player's pocket. Keep the eight slots, selected outline, flavor pictures, and remaining-supply bars readable on the hotbar. Do not add quantity numbers.

Physical restocking should ask where to put stock and how much to carry.

Place one supplier about 120 meters along the road from the home stand. The bicycle travels at roughly six meters per second on a straight section. With turns and handling, target a complete supply run of 60 to 75 seconds, including roughly 20 to 25 seconds of riding each way. Use simple stable riding, automatic balance, and a parking interaction. No falling over or physics punishment.

Select packs at the supplier terminal, pay, then collect the labeled packages from its pickup shelf. Each tub, bowl pack, or batter carton occupies one cargo slot. Carry one package by hand. The starting bicycle has four slots; its $48 cargo rack upgrade raises this to eight. Packages snap into visible slots. Uncollected paid purchases remain on the shelf, and a full rack refuses another package instead of deleting it.

Unload each package into a visible storage slot or active container at the correct stand. The initial stand stores four reserve packages, besides its open tubs, bowl stack, and batter. The kiosk holds eight reserve packages. Packages retain partial quantities when moved. All designated storage and bike cooler slots preserve ice cream for the prototype; melting and spoilage can wait.

Employees replenish their carried bowls, batter, and topping containers from the assigned locker. They can reload those working containers from matching refill packages stored there. The inventory transfer preserves quantities and does not create supplies. Installed serving tubs remain in the cooled counter. Between orders, when a tub falls to six portions or fewer, a worker may collect a matching refill tub from the explicitly assigned cold-storage rack into a free inventory slot, walk to the installed tub, and top it up using the same partial-transfer rule as the player. They return any partly full source to an available cold-storage slot; if no slot is free it remains in their inventory. They do not change the serving tub's flavor. If no refill exists, keep using the remaining portions and report low stock. They cannot buy supplies, collect supplier purchases, or transfer stock between businesses. This keeps the player responsible for stocking the locker and cold storage while allowing employees to operate during a supply run.

Before staff, closing the sign for a supplier visit sacrifices a few sales. It does not create a permanent reputation penalty. After staff, the same journey keeps the business earning. The business overview displays each location's cash earned today, supply bars, queue, and any missing ingredient. Opening it during trade does not pause the world.

If the player has no money and cannot make any bowl, offer a supplier recovery job: move three nearby crates, then receive six bowls and six vanilla portions. Reuse the same carrying interaction, taking about 30 seconds. This keeps a mistaken purchase from ending the run and earns less than normal trading.

Give the player both a full map and a live minimap from the beginning. The purpose is to locate the supplier, return to their business, and discover expansion sites without memorizing the neighborhood.

Place a north-up minimap in the upper-right corner, initially showing a roughly 120-meter-wide area centered on the player. Rotate the player arrow with facing direction. Show nearby roads, paths, owned businesses, the parked bicycle or truck, and the selected destination. Put an edge arrow and distance on destinations outside the visible area. Keep individual customer markers off by default to avoid clutter. The minimap stays live while walking and driving.

Press M for a full north-up map with pan, zoom, a legend, and clickable destination markers. In this single-player prototype, the full map pauses the whole simulation, including employee sales and vehicle movement, and closing it restores the previous running or paused state. This map behavior does not change the live inventory or business-overview behavior. Show the supplier, home business, available park plot, owned secondary stand, home delivery receiving area, and the two designated truck selling stops from the start. Unavailable locations remain visible with their purchase price or requirement rather than being hidden.

Selecting the supplier shows the types of stock sold there and a Set waypoint button. Selecting an available business plot shows its purchase price and a waypoint; map selection does not buy it. Owned-business markers show its name and any stockout alert. A pending free level delivery adds a package badge at home. The first supply task automatically sets the supplier waypoint, and the player can replace or clear it.

The selected waypoint draws a route along usable roads or pedestrian paths, with a matching line on the minimap and a distance in meters. Use the appropriate route for walking, cycling, or driving, and update it after movement or changing transport. It must not draw a straight shortcut through a house or across an impassable boundary. Store the selected destination in the save. Markers correspond to actual scene locations and owned businesses so a moved vehicle or purchased plot cannot leave a stale map marker. The initial map is authored from this compact neighborhood; it does not need a general-purpose map editor.

Customer demand should be predictable enough to plan around, with visible pedestrians making it feel natural.

| Location | Mean interval between potential customers | Queue capacity |
| --- | ---: | ---: |
| Initial home stand | 14 seconds | Four, including the customer being served |
| Expanded home kiosk | 10 seconds | Six |
| Second stand at park | 16 seconds | Four |

Vary each interval by up to 20%. Do not shorten it secretly because a player just bought a faster tool. The kiosk's larger frontage and sign visibly explain its extra demand. Across eight trading minutes the nominal arrival budgets are about 34 at home, 48 at the kiosk, and 30 at the park before tutorial overrides. These are potential arrivals, not completed sales. Physical service, stock, layout, queues, and time away determine how many actually buy. Measure those counts before deciding upgrade purchase days.

Use eight authored pedestrian entry points at house doors, park paths, and road corners. Spawn outside the player's view or beyond an occluding corner, then walk to the business. If an entry is visible, delay that spawn. Do not create people beside the counter. Ambient pedestrians can also become customers, but replacing a scheduled arrival must not double demand.

A potential customer walks past if the queue is full. Waiting patience is 90 seconds, extended to 120 for the first six customers. A served customer walks away to an exit before being recycled. Prevent an immediately recognizable repeat appearance for two real minutes. Cap visible active pedestrians at 24 initially. This is a starting performance budget to measure, not a proven limit.

Generate a potential customer's requested recipe from that location's menu before checking stock. At the primary stand this includes every ingredient required by the current business level. If supplies or equipment cannot support the recipe, show the missing item, let the customer leave, and count the lost sale. Do not reroll an available recipe instead. If support exists, reserve the quantities and let the customer join the queue, then consume ingredients through preparation. If a preparation mistake exhausts stock needed by an accepted order, allow cancellation without a cash fine and count an unfulfilled sale. A new level never changes an existing order, because ingredient requirements advance between days.

Start with vanilla and chocolate, then introduce two new flavors at level two and four each at levels four and six. Choose uniformly among the primary stand's required flavors for the first balancing pass, applying topping probabilities separately. Two-scoop orders can mix any two required flavors. Scope includes all twelve flavors and six toppings; defer three-scoop towers and additional dessert types until this expanded ice cream menu is working. An unattended staffed site checks whether its assigned workers can fulfil the requested recipe with their own inventories, locker stock, and reachable equipment. Stock in one worker's pocket is not also available to another worker. A missing supply creates a lost sale instead of removing a required ingredient from future demand.

Workers have their own eight-slot inventory and collect small items only from one explicitly assigned supply locker at their business. This replaces the earlier plan for workers to fetch scooper and batter objects from arbitrary counter positions. Place a locker on the floor grid, stock it, assign employees to it, and inspect both stored items and items checked out by each worker.

Start lockers at four slots and offer two capacity upgrades. The larger versions use more vertical compartments within the same one-meter-wide by half-meter-deep floor footprint. They accept the same item types and stack sizes.

| Locker tier | Slots | New purchase price | Upgrade from previous tier | Intended use |
| --- | ---: | ---: | ---: | --- |
| Small locker | 4 | $24 | Starting tier | Issue one worker a basic kit and keep limited reserve stock |
| Standard locker | 8 | $72 | $48 | Store several ingredients and refills for a wider menu |
| Large locker | 12 | $160 | $88 | Support the full topping range, spare equipment, and more reserve stock |

Upgrading in place costs the difference in purchase price, preserves contents and assignments, and changes the model's compartments. It never refills supplies. The first worker's hiring fee does not include a free locker. A useful initial four-slot load is one scooper, 12 bowls, one batter bottle with ten portions, and one topping dispenser with 15 portions. When the worker collects those supplies, the vacated locker slots can hold their next refills. It is a supply point, not a second copy of their personal inventory.

A locker can accept a bowl package, batter carton, or topping refill directly from hand-carried cargo even though those packages do not fit the personal hotbar. Ice cream tubs use cold storage rather than the locker. A locker can serve multiple workers, but physical tools and working containers are finite: two simultaneous workers need two scoopers. A business may own several lockers; each worker has exactly one explicit locker assignment and does not pool all locker contents automatically. Two small lockers cost less than one standard locker but occupy twice the floor space and divide their supplies. Upgrading provides more accessible stock at the worker's assigned supply point. The large locker tops out at 12 slots for this prototype; there is no initial 16-slot locker.

Before the first order, the worker walks to the locker, opens it, and collects their assigned scooper, a working batter bottle if needed, a stack of up to 12 bowls, and any topping containers needed for the next order. The selected scooper is shown on the employee card. Their default working inventory holds one scooper, one batter bottle, one bowl stack, and at most two topping containers, leaving three slots for transfers or servings. A bowl-only worker needs less. Do not fill every slot with the entire topping menu; return unused topping containers when changing recipes. Check the next recipe against carried quantities before starting. Replenish between orders when bowls fall to three, batter to two, or a carried topping to three portions, provided that order type remains advertised and the matching locker supply exists. Remaining stock can still be used if no refill is available.

The worker retains issued tools between orders and shifts. They visibly equip the relevant item from their inventory, use it, and stow it to free their hand. They return to the locker when low on supplies, changing a required topping, or collecting replacement equipment. Scoop, batter, and topping quantities move between owners without duplication. The worker panel shows remaining-supply bars without numbers and the actual scooper tier, so equipment carried off the premises is still accounted for.

The player can select a replacement scooper from stock in the assigned locker and request an equipment change. Between orders, the worker walks back, returns the old tool, and takes the new one. No remote stat upgrade occurs while the new tool is still in storage. Every additional improved scooper costs $12. The player handing their only improved scooper to a worker gives up personal access to that same tool. Worker scooping speed and the held tool's stroke requirement both affect the actual action. The improved tool means one animated stroke, while the basic tool requires three.

Locker transfers happen when the worker reaches the locker, not when they decide to go there. A specific reserved item cannot be issued twice. If the player removes it before collection, the worker selects another permitted item or reports the missing supply. A full locker refuses another deposit without destroying it. Return replaced or dismissed workers' equipment to storage before removing them; if storage is full, keep their inventory accessible until it has been unloaded. Persist worker and locker inventories through save/load.

Prepared servings must occupy a real reachable work position while ingredients are added. Cones require a cone holder; bowls require a clear bowl preparation spot. Each worker claims one spot for their active order, places the serving, equips the scooper, moves to a tub, scoops, returns, and deposits into that serving. They stow the scooper, equip a required topping container, and apply it while the serving stays in place. They finally pick it up and carry it to the customer. No assembling a serving invisibly inside an inventory slot or holding both the cone and scooper in one hand. The player follows the same preparation rule and can stow a prepared serving for transport after taking it from the work position.

Workers need useful differences the player can understand before hiring. They have individual action speeds, never a fixed bowl or cone completion timer.

| Example employee | Hiring fee | Daily wage | Walking speed | Scooping speed | Pouring speed | Finishing speed | Handling speed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rookie | $60 | $24 | 1.3 m/s | 80% | 80% | 80% | 90% |
| Experienced | $90 | $42 | 1.5 m/s | 100% | 100% | 100% | 100% |
| Expert | $140 | $66 | 1.7 m/s | 130% | 120% | 125% | 115% |

These are starting example profiles. Individual applicants can mix strengths, such as fast scooping with slower walking, so hiring is not limited to three uniform tiers. Show these stats alongside the name, portrait, and wage. Prices remain provisional until the full work sequence is measured.

For employee animations, action duration equals the tool's base animation duration divided by the corresponding speed multiplier. Start the worker's basic three-stroke scoop animation at three seconds: 3.75 seconds at 80% scooping speed, three seconds at 100%, or about 2.31 seconds at 130%. Start the worker's improved one-stroke animation at one second: 1.25, one, and about 0.77 seconds respectively. The employee completes the actual stroke; these animation durations do not impose a minimum time on the player's one-swipe gesture. A one-second pour takes 1.25 seconds at 80% or about 0.83 seconds at 120%.

Handling speed affects reaching, picking up, putting down, and opening or closing equipment. Start a pickup or placement at 0.6 seconds and a lid action at 0.5 seconds for a 100% worker, then match and tune the animations. It does not accelerate cooking. The initial waffle iron always cooks for six seconds. A future better iron could change that equipment property independently.

The worker's elapsed order time is the actual walking time, handling, pouring, scooping, cooking waits, and waits for shared equipment, with any work overlap accounted for. Record completed orders and elapsed work during play. Do not advertise a predicted orders-per-day value before the current layout and full action sequence can support the estimate. Previous fixed bowl/cone times and their derived employee throughput estimates are withdrawn.

A rookie may train to experienced for $30 after one paid shift, taking effect the next morning. The example profile's next wage becomes $42. Random failure chances, hunger, and hidden quality penalties would make automation harder to trust, so leave them out.

A worker making a fresh cone must claim an order and a reachable cone holder, check their personal supplies, and visit the locker for anything missing. They walk to the iron, open it if needed, equip their batter bottle, pour, stow the bottle, close the lid, wait for cooking, open it, take the cone, and place it in the claimed holder. They equip their own scooper, walk to each required tub, scoop, return to the holder, and deposit each portion. They then equip and use each requested topping container, stow it, pick up the finished cone, walk to the serving position, and hand it over. Visible objects, inventory quantities, and equipment states change as those actions occur. Equipping an item uses a brief visible draw or reach animation. It does not skip the preparation action.

Cooking may overlap useful setup work, such as collecting a needed topping from the locker, provided the worker can return before burning. Initially each worker owns one active order. Allow a worker to use a pre-baked cone from the actual rack; consuming it removes that cone. Autonomous batch preparation and juggling multiple orders can follow after one complete order works reliably.

A player can claim another ticket if a second preparation space is free. Claimed tickets show their owner. Workers retain their own tools, reserve the preparation space for the order, and claim shared appliances when needed. A worker starts a waffle only with a reserved reachable holder and the required inventory capacity to transfer it. Once the cone leaves the iron, release that appliance before using tubs or toppings. If two workers need the same iron or tub access position, one visibly waits at a clear position without blocking the operator's exit. Buying another iron or separating work areas can improve throughput. Workers never create free products or earn money from an empty stand.

Assignments and wages are confirmed before opening. Deduct the daily wage when that shift starts. Hiring during trade schedules the first shift for the next day. If the player cannot afford a shift, the worker stays off duty and the player can serve personally. No compounding wage debt. Reassignment happens during preparation; one employee cannot cover two businesses simultaneously.

The same worker should complete fewer orders in a layout with long walks or shared-equipment delays. Layout improvements, tool purchases, and hiring then address different causes of slow service. Measure those causes separately before tuning wages or customer demand. Hiring should not require constant rescuing from deliberately bad AI.

Strict grid building is part of this prototype. Furniture and equipment positions are chosen by the player.

Use a 0.5-meter floor grid for tables, freezer bases, shelves, and counters. Use a 0.25-meter local surface grid on compatible tabletops for waffle irons, tub modules, dispensers, tool rests, and preparation spaces. Both grids allow only 90-degree rotation. The surface grid moves with its supporting table; items keep their local positions. Confirm final footprints against the actual models and resize the model or its footprint before authoring the build catalog.

Initial target footprints are a two-by-one-meter table, a half-meter-square waffle iron, a half-meter-square tub module, a half-meter-square preparation area, and a quarter-meter-square tool rest. A half-meter-square appliance occupies two-by-two tabletop cells. An ice cream tub requires a compatible cooled surface or freezer module. A tool rest accepts a scooper or bottle without consuming an entire appliance footprint.

The player selects a purchased part, sees its occupied cells and operating side, rotates it, and confirms placement. Furniture must fit the owned plot; equipment must fit a compatible supporting surface. Reject overlap and unsupported placement. Show worker access warnings when a proposed arrangement blocks an operating position or its route to the serving counter. A staffed site cannot open until it has a complete reachable preparation chain. An unfinished layout can remain saved during preparation.

Reserve at least a one-meter-wide aisle for a worker, with 1.5 meters recommended where workers share an aisle. Each appliance exposes one or more authored standing positions and hand targets. The selected accessible operating side determines where the worker stands. Workers route around tables to that position, face the equipment, and reach to the item's actual placed position. They cannot reach through a counter, wall, or another appliance. The exact reach envelope must be checked on the character rig in the layout test.

Allow furniture and appliance rearrangement during preparation or in a paused build mode, with all businesses paused together. This avoids moving a table halfway through an employee's pour. Small items can still be picked up, placed, and dropped during trading. Once a moved table is confirmed, recompute access to its equipment before resuming. Moving furniture preserves its supported contents; putting it into storage requires those contents to be cleared first. Fuel, ingredients, upgrades, and ownership do not reset when an item is moved.

The starting stand is an immediately usable layout made from movable parts, with the first customer waiting until the player opens. Expansion gives the player more buildable floor area and additional loose building parts to arrange. It does not replace their arrangement with a fixed kitchen. Use the same surface-grid rules inside the parked truck while respecting its fixed shell, door, and driver's area.

Retain purchase bundles for the opening economy, but also sell individual parts: an extra table for $20, an empty two-well freezer module for $40, a four-package storage shelf for $24, a bowl dispenser for $6, and a tool rest for $4. These are provisional prices; contents are separate. A purchase grants that physical part once. Moving or storing it is free and does not duplicate it. The bundle's included parts do not incur those prices a second time.

The locker defines which portable items staff may collect. Grid placement defines where fixed equipment can be operated. These are separate rules.

| Item or location | Worker behavior |
| --- | --- |
| Loose or counter-placed scooper, bottle, or topping dispenser | Ignore; the player must put it in the assigned locker to issue it |
| Assigned locker | Walk here to collect and return portable equipment or replenish carried supplies |
| Worker's own inventory | Equip the actual carried item, use it, and stow it |
| Another worker's or the player's inventory | Unavailable; no borrowing or remote transfer |
| Installed iron, cooled tub, or serving holder | Use from its reachable operating position while respecting another operator's claim |
| Explicit cold-storage rack | Collect a matching refill tub, transfer what fits into the installed serving tub, and return any remaining supply |
| Serving in the worker's claimed holder or preparation spot | Add scoops and toppings, then collect for delivery |

Placed equipment and servings are stable, with loose-body physics disabled. Held items follow controlled hand poses and animation. The locker approach removes arbitrary handheld pickup positions from the worker's search, while preserving walking, opening, pouring, scooping, topping, and serving. The player can still drop objects and use them manually. A scooper settling on a counter does not silently enter an employee's equipment pool.

Use an inspection hint such as "Put in the staff locker" for a portable supply intended for employees, and "No worker access" for unreachable installed equipment. Keep indicators in placement and inspection views. If the player takes a serving from a worker's claimed holder, the worker pauses that ticket with a missing-serving status instead of producing a duplicate; returning the same serving lets them continue. Objects currently in an employee's hand or appliance mid-operation cannot be grabbed. Loose cargo blocking an aisle should make the worker pause and report the obstruction rather than walk through it.

The existing `PickupItem` already has a loose rigidbody mode and a `StopPhysics` path; `PlayerInteraction` has supported counter placement checks. These provide a starting point. The proposed inventories, lockers, strict grids, operating positions, and employee action sequences still need to be built and tested together. Locker, work-area, and cold-storage assignments use explicit business-owned references rather than object-name discovery.

Use the following purchases. These are functional improvements with visible changes in the scene.

| Purchase | Price | Result |
| --- | ---: | --- |
| Improved scooper | $12 | Three strokes become one; distinct handle and scoop shape |
| Small staff locker | $24 | Four storage slots; starts empty |
| Standard staff locker | $72 new, or $48 upgrade | Eight storage slots in the same floor footprint |
| Large staff locker | $160 new, or $88 upgrade | 12 storage slots in the same floor footprint |
| Waffle station | $90 | Placeable iron, side table, three-cone rack, empty working batter bottle, first batter carton |
| Bicycle cargo rack | $48 | Four cargo slots become eight |
| Expanded kiosk | $160 | Larger buildable plot and frontage, canopy, additional table and preparation area, four additional reserve slots, queue of six, higher footfall; tub capacity comes from placed flavor modules |
| Second pop-up stand | $250 | Park permit and two-flavor bowl stand with improved scooper; supplies and employee purchased separately |
| Ice cream truck | $600 | Driveable fitted truck, four wells, improved scooper, waffle station, and 12 cargo slots; starts without supplies |
| Driver-server contract | $120 | Employee who drives and serves one preset truck route for $60 per day |

The opening stand occupies a roughly three-by-two-meter area within its owned plot. Set the final plot dimensions only after verifying the compact required-menu layout described above. The $160 kiosk expansion adds a further two-meter-wide building strip beside the existing plot, plus the listed furniture, storage, and canopy parts. Show the added cells and bundled parts before purchase. The player places the additional counter, storage, and equipment while retaining or rearranging the original kitchen. Canopy and shell pieces can use authored attachment points; furnishing and equipment placement remain player-controlled. General wall drawing is a separate feature from the required grid furnishing system.

The park stand is a repeatable version of the starting business, with the park surcharge reflecting its location. Put it about 90 meters from the home site on a separate pedestrian catchment. Opening it should not steal all home customers. A player can operate it while a worker runs home, then hire someone for the park too. Cap owned fixed sites at two for this prototype. A staffed stand is fixed to its pad; folding and towing occupied businesses would introduce moving-stock and worker problems before we know it is enjoyable.

Offer the truck after owning the kiosk and having at least one contracted employee. Give it two marked selling stops, one by the playground and one on a residential loop. Each advertises seven potential customers per day. Orders contain two scoops; 60% request cones when stocked. Measure how much of the eight-minute day driving, physical preparation, and serving both stops actually require. Customers pay the $3 mobile surcharge only at those stops. They are a distinct daily demand pool from the fixed stands, not unlimited respawns.

The player prepares and serves from the parked truck. Do not require running alongside a moving vehicle in this mode. Stops remain available throughout trading hours for the first pass; timed events can come later. The player sees the available orders before committing to a route and packs accordingly.

The driver-server follows one preset route and physically handles production at its stops. Actual actions, travel, available equipment, inventory, and stop demand determine completed orders. Do not impose an artificial lower employee sales quota. Charge $12 per operating day for the truck in addition to the driver's $60 wage, including on player-operated days. Staffed locations continue consuming actual stock when out of sight. The overview reports completed sales, never a flat income-per-minute bonus.

With all businesses staffed, the player's remaining work is supplying three inventories and choosing investments. At that point the prototype has demonstrated the intended transition. Include an optional continue button after the first fully staffed day, but do not build an unlimited fleet, employee transport system, or a full city for this pass.

The earlier nine-day cash-flow example is withdrawn. Its six-minute days, paid ingredient unlocks, equal strawberry/mint premiums, assumed service rates, and fixed kitchen layouts no longer describe this design. The $12 upgrade after two $6 sales and the per-product contribution figures remain arithmetically valid. Rebuild progression from measured physical orders, XP thresholds, free starter deliveries, partial refills, stock journeys, eight-minute days, hotbar use, and shared appliances. Include replacement stock purchases, furniture spending, locker upgrades, wages, and leftover stock. Until then, the day-two employee and day-three-to-four full flavor menu are pacing targets, and no truck purchase day is forecast.

The asset work is concentrated around assets the player handles or upgrades.

| Work | Proposed assets |
| --- | --- |
| Adapt existing models | Bicycle and cooler with visible cargo sockets; functional pop-up stand; supply packages with ingredient labels; existing truck as purchasable vehicle |
| New serving assets | Wide paper bowl with a thick rolled rim, nested bowl stack, one- and two-scoop bowl layouts, improved one-swipe scooper |
| Inventory UI | Eight-slot player hotbar, eight-slot worker inventory, four/eight/12-slot locker transfer views, selected equipment, item and flavor icons, supply bars without numeric text; authored editable UI |
| Navigation and progression UI | Full map, live minimap, destination and route markers, XP meter, day-end level rewards, home delivery notification |
| Stock feedback | Green/red remaining-supply bars without numeric text, separate tub fill meshes with changing height, refill source/target preview |
| Locker and toppings | Three grid-sized locker tiers with more vertical compartments, opening doors and hand target, dry dispensers, sauce bottles, whipped-cream can, bulk refills, distinct topping layers and order icons |
| Store expansion kit | Grid-sized tables and counters, cooled tub modules, equipment holders, prep spaces, floor pad, canopy, kiosk shell, sign, reserve storage rack; authored access sides and hand targets |
| Supplier | Small warehouse or wholesale storefront, terminal, pickup shelf, marked loading area |
| Staff | Apron and hat variants on existing characters; visible preparation, carrying, idle, and serving motions |
| Neighborhood | Assemble existing houses and trees first; add two house facade variants after choosing the art direction if repetition remains noticeable |

New Blender assets and visual alternatives belong in `Assets/IceCreamTruckWorkshop.blend`, with unsaved user edits preserved first. Keep variants in labeled collections, arranged side by side. Compare them in a separate Unity review scene before replacing existing scene references.

The art issue deserves an early, bounded comparison. In the inspected Game-view capture, trees and rocks have angular silhouettes, shadows mute the palette, and large surfaces have little variation. The saved kitchen render has softer shading and clearer material separation. My interpretation is that shape, lighting, and motion all contribute to the rigid impression. Bloom alone cannot change a straight roofline or make a faceted tree round.

Compare the existing cottage, tree, and ice cream tub in three directions, alongside the unchanged originals. That is nine asset variants, using the same camera and layout.

| Direction | Shape and material treatment | Lighting and motion |
| --- | --- | --- |
| Soft toy town, recommended first | Rounder tree clusters, roof overhang about 20% larger, thicker trim, broad bevels, gently irregular ice cream, clearer pastel color separation | Warm key light, cool soft shadows, broad highlights, subtle foliage sway |
| Cel cartoon | Exaggerated silhouettes, simplified surface detail, two or three light bands, restrained colored outline around major forms | Graphic shadow shapes, minimal bloom, slightly snappier movements |
| Painted storybook | Slightly crooked roofs, uneven tree masses, large painted color patches, gentle material gradients | Soft light, little gloss, warm highlights with cool shadows |

First compare shape variants under identical neutral lighting. Then compare the same chosen geometry with each shading treatment in Unity. Use noon, late afternoon, and the shadowed preparation counter. Capture first-person serving distance as well as the street view. This distinguishes appealing studio renders from assets that work during play.

For the soft direction, start a review profile around +8 saturation, +5 contrast, bloom intensity 0.1 with threshold 1.2, and restrained contact shadows. These are experiment values. Keep motion blur, film grain, chromatic aberration, and depth of field off in the comparison so the food and order pictures remain readable. URP already includes volume-based post-processing and bloom, so this does not require a separate post-processing package. See [Unity's URP post-processing documentation](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/integration-with-post-processing.html) and [bloom reference](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/post-processing-bloom.html).

Try a 1.5-pixel outline at 1080p in the cel variant, but judge silhouettes and small tools before extending it across the scene. A small scoop settling motion over 0.15 seconds, a readable waffle steam cue, moving wheels and pedals, and worker anticipation can also make the world feel less rigid. Capture those in motion, with an option to reduce motion. Measure the chosen treatment at 1080p against the same scene before adopting it; the existing rendering work should not be discarded on the strength of a still image.

Build in this order, with a playable checkpoint after each step.

1. In a separate tycoon scene, build the shared eight-slot inventory behavior, staff locker, floor and tabletop grids, movable equipment, operating sides, and serving holders. Prove one employee can walk to the assigned locker, collect a scooper and bowls into their inventory, equip the tool, walk to a moved tub, scoop, deposit into a bowl on a preparation spot, and serve. Repeat with the table rotated, an unreachable layout, and an improved scooper issued through the locker.
2. Add the opening stand, two flavors, cash, finite stock, the eight-slot inventory and hotbar, improved one-swipe scooper, one-second-per-minute clock, and saving of layouts and inventory. Verify the first two sales buy a tool that completes a scoop with one swipe, including a swipe shorter than one second. Make the small art comparison before producing new modular assets in bulk, and choose a working direction from in-game views.
3. Add the complete physical employee waffle sequence, cone-holder use, action-speed stats, appliance claims, and sharing with a player or second employee. Measure two layouts and both basic and improved tools. Add the supplier, bicycle, cargo, full map, minimap, assigned cold storage, inventory tub refilling, quantity bars, and changing ice cream fill height. Add XP, day-end leveling, and the first free ingredient deliveries. Verify the supplier route, a complete paid refill journey, one-time free rewards, visible shake and drizzle actions, and correct ingredient loss on waste.
4. Add hiring, wages, locker tiers and upgrades, locker replenishment, physical same-flavor partial tub refills, and grid-based kiosk expansion. Complete the level reward sequence through all twelve flavors and six toppings, including mixed doubles and two-topping orders. Check the home menu advances automatically between days and missing supplies produce lost sales. Verify the stand continues selling during a supply run and stops when an essential supply runs out. Recalculate the economy and XP thresholds from observed preparation, walking, inventory changes, restocking, and waiting times.
5. Add the second location, separate inventory, park demand, another employee, and the business overview. Verify moving a crate changes only the receiving site's stock.
6. Add truck purchase, manual stop trading, the preset employee route, vehicle costs, and campaign completion. Verify the same truck cannot operate under both player and employee control at once.
7. Play through the whole economy, tune prices and pacing, apply the chosen art treatment to the most visible assets, then make any additional houses that the compact map actually needs.

For evaluation, observe a fresh player reaching the first upgrade in 45 to 75 seconds, the first flavor reward at the end of day one, and the first staffed supply run around 18 to 25 minutes including preparation. These are targets with room for learning. Record actual service time before and after the scooper upgrade. Verify one complete swipe yields one portion without a minimum hold time. Test inventory stack limits, partial transfers, loaded tools, filled servings, locker upgrades preserving contents, and save/load. Verify 60 unpaused real seconds advance the trading clock by one hour. Check every later flavor has strictly higher sale price and contribution per scoop. Verify XP comes only from completed sales, spending does not remove XP, multiple levels can be earned at closing, and a reward cannot be claimed twice. Do not equate a lower tool timer with a better interaction.

Verify a 5/10 bottle shows equal green and red, a 12/24 tub shows half of its usable fill height, and an empty serving tub exposes its interior. Check refilling 7/24 from a full tub ends at target 24/24 and source 7/24, and refilling 20/24 from three portions ends at 23/24 and zero. Full, mismatched, interrupted, and simultaneous refill attempts must preserve total stock. Check scoop hand targets follow the lowered surface. Test the full map pause and resume state, waypoint routing to the supplier, returning to home, vehicle markers, plot purchase state, and the minimap edge arrow for a distant destination.

The first staffing test must report departure cash, installed stock, locker contents, worker inventory, the player's supplier purchase, completed sales during the absence, return cash and stock, and the console result. Observe every physical step of a fresh cone with two toppings. Compare the same worker with an issued basic and improved scooper, then compare compact and spread-out layouts. Changing pouring speed must affect the pour while cooking remains six seconds. Test a loose or counter-placed bottle being ignored, depositing it in the assigned locker making it collectable, two workers requesting the only scooper, finite refill quantities, a full locker, a player removing an item before worker collection, a missing serving, and equipment returned after reassignment. Verify no consumption or duplication from inventory switching or save/load. Test two employees sharing an iron without deadlock, table movement preserving contents, invalid access, depleted supplies, a burned reserved waffle, full bike cargo, insufficient wages, and reopening a saved multi-location game. Gameplay tests should use the actual feature paths and visible input where relevant.

The main design risks are long errands, idle time after automation, cone work paying too little for its handling, and large queues hiding the benefit of a faster tool. Change travel distance or cargo capacity if restocking takes more than roughly a quarter of an established trading day. If all locations are stocked and staffed and there is nothing interesting left to do, end the prototype there. More mandatory chores would obscure whether expansion and logistics are enjoyable.

Keep additional dessert categories, arbitrary wall construction, freeform worker retrieval of loose physics objects, spoilage, random worker mistakes, traffic simulation, weekly payroll, multiplayer, and unlimited trucks beyond this prototype. The proposed build includes twelve flavors, six toppings, strict grid furnishing, player and employee inventories, staff lockers, physical preparation at holders and equipment, finite stock, a rideable supply vehicle, earned tools, action-based employee stats, an expandable store, a second location, manual truck trading, and one automated truck route.
