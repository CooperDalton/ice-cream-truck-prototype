# Blender models

Use `Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend` as the master scene, relative to the repository root. It shows the truck beside the standalone preparation set, including the one-, two-, and three-scoop cones. It also contains the crew player, adult and child NPC appearances, and first-person hands. Four house variants and four tree variants sit alongside them in collections E and F. See `ENVIRONMENT.md` for the asset list, materials, and export. Continue modeling in this scene and keep new assets visible side by side. The separate truck and prep Blender files are synchronized asset copies. Earlier versions are preserved under `Art/Source`.

`Source/BeforeCombinedWorkshop.blend` preserves the live Blender session from before the merge.

## Preparation set

First art pass for review. The standalone asset copy is `Ice Cream Truck Prototype/Assets/IceCreamTruckSimulatorModels.blend`, relative to the repository root. `Exports/IceCreamPreparation.glb` contains the visible models and their materials, without the studio floor, camera, or lights.

The set includes a 2 × 6 tub counter, six cone holders, a waffle station and hinged waffle maker, batter bottle, raw batter, cooked waffle, hollow waffle cone, assembled strawberry cone, scooper, and sprinkle shaker. Material slots control the equipment colors and ice cream flavors.

The counter is 2.60 meters wide with a 0.96-meter work surface. The waffle station adds 0.74 meters of width. The scene uses meters.

Each pickup prop and removable tub has its own named root. The twelve ice cream fill meshes remain separate from their tubs. The waffle lid uses `Lid_HINGE`, with local X rotation of 0 degrees closed and -108 degrees open. Placement, pouring, and scooping sockets are named empties. These are modeling anchors; no gameplay behavior is implemented.

Raw batter is hidden for the presentation. Enable its mesh under `RawBatter_ROOT` and hide `CookedWaffle_ROOT` to inspect the uncooked state. Collection 99 holds the studio presentation objects and is excluded from the GLB export.

`Previews/` contains renders of the complete set, the waffle station, the counter, and the closed waffle maker. `Source/build_ice_cream_models.py` rebuilds this first pass with Blender's Python API. Running it replaces the modeled Blender file, so preserve any manual edits before rebuilding. `Source/OriginalBlenderScene.blend` preserves the initial scene.

Verified in Blender 5.1.1: 12 tubs, 12 independent fills, six holders, all preparation props, and the lid hierarchy. Inspected the rendered open and closed lid poses. This set has not been tested in Unity; it has no colliders or interaction scripts yet.

The cone supports one, two, or three scoops. `FinishedCone_ROOT`, `Cone_2Scoops_ROOT`, and `Cone_3Scoops_ROOT` show each state using the same cone geometry. Each scoop is a separate child with its own flavor material override. All three cones have attachment sockets at local Z positions 0.201, 0.321, and 0.441 meters. Toggle or attach scoop children to change the stack; no cone replacement is required. `Previews/05_One_Two_Three_Scoops.png` shows the three heights together.

## Current revision

The master now uses the roomier truck with an open serving window and the rounded bean characters. Truck and counter wordmarks have been removed. Decorative meshes have been simplified, and each house and tree is a single mesh. See `TRUCK.md`, `CHARACTERS.md`, and `MODEL_BUDGET.md`. `Source/revise_workshop.py` assembles this revision from the preserved inputs; do not run older builders against the current master.

The default review is the full workshop overview, with the prep set and characters in front of the truck, trees beside it, and houses directly behind. `Source/arrange_workshop.py` restores this layout and frames every asset in Blender. Use `Previews/Workshop_All_Models.png` when showing the complete collection.

Cone shells use the shared `Waffle cone • flat color texture` material and `Textures/WaffleCone_BaseColor.png`. The diamond pattern is base color only, with no spiral geometry, normal map, bump, or displacement. All empty and stacked cones, including the roof sign, share an 80-vertex, 156-triangle mesh. GLB exports contain 162 vertices after UV and normal splits, one material, and the embedded texture. Scoop meshes and the three placement sockets are unchanged. `Source/flat_waffle_cone.py` supplies this mesh to the builders.

## Remaining prototype kit

Collections G through J add 44 models: modular roads and ground, a populated park tile, street furniture, supply and handheld props, a delivery bicycle with cooler, and a pop-up stand. They sit beside the earlier models in the shared workshop. See `REMAINING_MODELS.md` for the inventory, road dimensions, interaction anchors, and exports. The current overview includes these additions; `Source/arrange_workshop.py` predates this expanded layout.

## Final geometry audit

The complete model export is now 130,808 triangles and 106,017 exported vertices, about 20% fewer triangles than before this pass. The saved master and all seven exports are updated. `FINAL_MODEL_AUDIT.md` records the reductions, preserved rig and interaction data, and round-trip export checks. `Optimization_After.png` and `Workshop_All_Models.png` are the current review renders. Older builders predate this final geometry pass; use `Source/optimize_workshop_geometry.py` on a preserved rebuild before producing replacement exports.

## Larger road cells

The road, grass, and park cells are now 24 × 24 meters. Roads are 12 meters wide with six-meter lanes and 1.5-meter sidewalks. The resize adds no triangles. All assets remain in the master workshop; the tile rows are spaced farther apart for their full-size footprints. `Road_Truck_Scale.png` shows the truck against the new road width. `Source/enlarge_road_tiles.py` also runs at the end of the remaining-model builder so regenerated cells keep this size.
