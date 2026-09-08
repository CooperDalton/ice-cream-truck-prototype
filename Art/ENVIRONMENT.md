# Houses and trees

The master file is `Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend`, relative to the repository root. Collections `E • Houses` and `F • Trees` hold the new models beside the truck, equipment, and characters.

## Houses

| Root | Appearance | Height | Current triangles |
| --- | --- | --- | --- |
| `House_Cottage_ROOT` | Peach cottage with gable roof and shutters | 4.83 m | 2,884 |
| `House_Townhouse_ROOT` | Mint two-story house with covered entry | 7.19 m | 4,384 |
| `House_Bungalow_ROOT` | Yellow bungalow with hip roof and veranda | 4.83 m | 3,376 |
| `House_Family_ROOT` | Lilac two-story house with attached garage | 6.69 m | 3,644 |

These are exterior models. Each house is one mesh with named material slots. The architectural pieces remain separate connected components inside that mesh. Each house faces local -Y, has a root at ground level, and fits within an 8 × 8 meter footprint. Wall, roof, and door colors have named materials for each variant. Ivory trim and window materials are shared across the set; duplicate a shared material before changing only one house.

## Trees

| Root | Shape | Height | Current triangles |
| --- | --- | --- | --- |
| `Tree_Broadoak_ROOT` | Broad branching crown | 5.67 m | 1,226 |
| `Tree_Slenderpoplar_ROOT` | Tall narrow crown with pale bark | 6.06 m | 912 |
| `Tree_Tieredpine_ROOT` | Four tapered foliage tiers | 5.18 m | 858 |
| `Tree_Roundmaple_ROOT` | Short rounded crown | 4.62 m | 1,048 |

Tree roots sit at ground level. Foliage and bark use separate materials. Each tree is one mesh, with the crowns and branches retained as connected components.

## Files and verification

`Exports/Neighborhood.glb` contains the eight assets and their materials. It excludes studio objects and the earlier models. The models have no gameplay code, colliders, wind animation, or interiors.

`Previews/Environment_01_Houses.png`, `Environment_02_Trees.png`, and `Environment_03_House_Detail.png` show the models. `Previews/Workshop_All_Models.png` shows the full shared scene.

Verified the saved Blender file and GLB: eight asset roots, closed meshes with outward normals, assigned materials, and house footprints under eight meters on both horizontal axes. Compared the earlier asset meshes and world transforms against `Source/BeforeEnvironmentWorkshop.blend`; all 288 existing objects matched. Measurements are recorded in `Source/environment-verification.json`. The export has not been tested in Unity.

`Source/build_environment.py` adds this set to a workshop that does not already contain it. It saves the master file before making temporary changes for the close-up renders. Preserve manual edits before rebuilding. `Source/BeforeEnvironmentWorkshop.blend` is the master snapshot from before these additions.

The truck and character revision also reduced environment bevels and combined static parts. See `MODEL_BUDGET.md` for current exported counts. The earlier environment previews show the original bevel density.

The final geometry audit removed collapsed bevels and flat subdivisions. The table above uses the current export counts; earlier environment renders predate this cleanup. See `FINAL_MODEL_AUDIT.md`.
