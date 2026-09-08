# Remaining prototype models

The shared master is `Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend`. This pass adds 44 asset roots in collections G through J. Existing truck, preparation equipment, characters, houses, and trees stay in their previous positions. The small props sit on two review shelves in front of the characters. Shelves belong to the studio collection and are excluded from exports.

## Model inventory

| Collection | Models |
| --- | --- |
| G • Modular ground | Straight road, corner, T-junction, crossroads, dead end, crosswalk, grass cell, populated park cell, straight sidewalk, sidewalk corner, curb ramp |
| H • Park and street props | Bench, picnic table, trash bin, street lamp, picket fence, shrub, flower patch, mailbox, fire hydrant, street sign |
| I • Supplies and handheld props | Boombox, baseball bat, delivery cooler, supply crate, ingredient carton, restock box, serving cup, tasting spoon, napkin dispenser, topping jar, serving tray, bucket, rag, broom, mop, dustpan, trash bag, toolbox, wrench, traffic cone, spare tire |
| J • Delivery bike and stand | Delivery bicycle with cooler, pop-up ice cream stand |

## Ground layout

Road, grass, and park cells have a 24 × 24 meter footprint. Road openings are 12 meters wide, giving two six-meter lanes, with 1.5-meter sidewalks on each side. The road top is local Z = 0, sidewalk top is 0.12, and grass top is 0.06. Root origins are at cell centers. Small gaps separate the samples in the review scene; use 24-meter center spacing when assembling them.

Road roots store `grid_size_m`, `road_width_m`, and `road_ports`. Port letters use Blender axes: north is +Y, east +X, south -Y, west -X. Named `RoadPort` empties mark the centers of each opening. Rotate cells in 90-degree steps and match opposing ports. The corner uses N/E, the T-junction N/E/S, and the dead end S. These are authored meshes and connection anchors. World generation has not been implemented.

The park has four pedestrian path ends and 4.2-meter-wide paths. Its ground and prop spacing were enlarged while the furniture and trees retain their normal dimensions. Its furniture and tree copies share mesh data with their standalone assets. The grass cell is a simple solid tile. Loose sidewalk pieces and the ramp allow manual connections outside the square cells.

## Interaction preparation

Pickup props have named grip anchors. The cup and tray have placement anchors; the stand has cone and service anchors. The bike has a rider anchor, hand anchors, a cooler anchor, separate wheel axles, a pedal axle, and a steering pivot. It faces local -Y. Wheels and pedals rotate about local X; steering rotates about local Z.

The cooler is hollow and has a lid hinged at the rear. Local X rotation of -100 degrees opens it. The mailbox flag also has a separate pivot. These controls are model hierarchies, with no gameplay scripts or colliders yet.

Materials are shared and named by color or surface. Duplicate a material to recolor one asset without changing others. Fixed parts are consolidated per asset; moving parts stay separate. Small flowers use coarse meshes, and the boombox has simple speaker faces without modeled grille perforations.

## Files

- `Exports/RoadAndParkKit.glb` contains collections G and H.
- `Exports/RemainingProps.glb` contains collections I and J.
- `Exports/WorkshopModels.glb` contains the complete shared model set.
- `Previews/Workshop_All_Models.png` shows all models together.
- `Previews/Remaining_Props.png` and `Previews/Road_And_Park_Kit.png` show the additions more closely.
- `Source/BeforeRemainingModels.blend` preserves the master before this pass.

`Source/build_remaining_models.py` adds the kit to a saved workshop that does not already contain collections G through J. Preserve manual edits before running an additive builder. `Source/verify_larger_roads.py` checks the current tile dimensions, connector profiles, park prop scales, and a sampled truck turn through the corner. The earlier `verify_remaining_models.py` records the initial eight-meter kit. Measurements are in `Source/remaining-models-verification.json` and `MODEL_BUDGET.md`. No Unity performance benchmark was run.

The September 6 road revision adds no triangles. `Source/larger-roads-verification.json` records the current measurements. The closed truck is 7.82 meters long and 5.28 meters wide including mirrors. A sampled rectangle sweep through the corner at a 12-meter radius stays on the road, assuming adjoining straight tiles. This checks geometric clearance; vehicle physics have not been implemented. `Previews/Road_Truck_Scale.png` places the actual truck on a road for comparison, using a temporary render arrangement.
