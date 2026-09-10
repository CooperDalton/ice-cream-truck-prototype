# Toon model kit

The selected direction is Cel cartoon. New models use mint, strawberry pink, warm cream, plum shadows, stepped shading, and rounded edges.

[Open the overview](Previews/ToonKit/ToonKitOverview.png). All 91 models and variants are in [IceCreamTruckWorkshop.blend](../Ice%20Cream%20Truck%20Prototype/Assets/IceCreamTruckWorkshop.blend), collection `N - Toon tycoon model kit`. The original models and both comparison rounds remain in the workshop.

The Blender scene `Toon kit - start here` shows twelve representative pieces. The other `Toon kit - ...` scenes separate the kit into review pages. Source collections keep meter scale; review instances enlarge each item independently.

| Review sheet | Contents |
| --- | --- |
| [Serving](Previews/ToonKit/Serving.png) | 16 assets: empty and filled bowls, bowl stacks, cones, flat waffle, holders, preparation mat, tool rest, dispenser, both scoopers, hinged waffle iron |
| [Flavors](Previews/ToonKit/Flavors.png) | 12 labeled tubs and 12 matching scoop models |
| [Toppings](Previews/ToonKit/Toppings.png) | Six working containers, six refill packs, and six separate serving layers |
| [Supplies](Previews/ToonKit/Supplies.png) | Tub lid, batter bottle, batter carton, bowl supply pack |
| [Furniture](Previews/ToonKit/Furniture.png) | 4/8/12-slot lockers, preparation table, counter, one/two-well cooled modules, 4/8-slot cold racks, open/closed sign, supplier terminal, pickup shelf |
| [Buildings](Previews/ToonKit/Buildings.png) | Floor tile, canopy, stand, kiosk shell, supplier storefront, loading pad, two cottage colors, maple tree |
| [Vehicles](Previews/ToonKit/Vehicles.png) | Four-slot bike, eight-slot bike with two cargo levels, hinged cooler, matching truck |
| [Staff](Previews/ToonKit/Staff.png) | Three apron/cap palettes and first-person hands, retaining the existing rigs |

Each flavor tub holds 24 portions in its model metadata. Its independent fill mesh has an `Empty` shape key: zero is full, 0.5 is half, and one is empty. The twelve surfaces were checked at all three values. Cooled modules have open wells, so their housings do not cover the depleted surface.

Locker bodies share a one-meter by half-meter footprint. Their 24 compartment doors have separate hinges and hand targets. The kit includes stock, grip, serving, cargo, and access anchors for later implementation. These anchors do not provide gameplay behavior.

Model labels show ingredient names without quantity numbers. Numeric package, bottle, locker, and shelf labels have been cleared. Remaining supply will use green/red bars without counts or percentages. Internal capacities are unchanged. The basic scooper has a cream grip; the improved tool has a mint grip, pink thumb pad, and gold collar.

[Compare the new people](Previews/PeopleStudy/PeopleComparison.png): four character shapes, each with a worker and customer version. They are in collection `O - Toon people alternatives` and scene `People - compare silhouettes`. The earlier staff models remain available for comparison.

The waffle iron needs a 0.5 by 0.75-meter tabletop footprint to accommodate its handle, plus lid clearance. That replaces the plan's initial half-meter-square estimate for this model. Tables remain two by one meters, cooled wells use half-meter modules, and the cone rack has three real support positions.

This pass stops at Blender assets. Unity shaders, post-processing, gameplay scripts, UI, worker behavior, animation clips, and scene integration remain for the next pass. The Blender materials use the same fixed shading direction as the approved study. Game export and optimization still need their own check; the kit's raw mesh count includes separate outline shells and all variants.

`Previews/ToonKit/inventory.json` lists every root, collection, dimension bound, display scale, and preview. The saved master passed the model checks and preserved all 1,292 existing objects' geometry, transforms, parents, and material assignments. `saved-master-audit.json` records those results. The live workshop was copied to `Source/BeforeToonKit_Append.blend` immediately before appending.

The authoring sequence is `build_toon_kit.py`, `finish_toon_kit.py`, `polish_toon_kit.py`, then `frame_toon_pages.py`, all under `Art/Source`. Run the builder against the live backup in a background Blender process. The later passes use `ToonKit_Additions.blend`. The framing pass runs once after polishing. `append_toon_kit.py` runs in the live Blender session after review. `verify_toon_kit.py --master` reopens the saved workshop and compares it with the pre-append backup.
