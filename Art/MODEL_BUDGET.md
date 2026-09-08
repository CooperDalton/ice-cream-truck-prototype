# Model budget

Current counts measured from the saved Blender master and GLB exports after the final optimization pass. Studio geometry and hidden alternate batter are excluded. Exported vertices include normal, UV, and material splits. See `FINAL_MODEL_AUDIT.md` for the before/after comparison and checks.

| Asset | Exported vertices | Triangles | Meshes | Material sections |
| --- | ---: | ---: | ---: | ---: |
| PreparationSet_ROOT | 20,146 | 27,494 | 49 | 112 |
| Tree_Broadoak_ROOT | 3,022 | 1,226 | 1 | 3 |
| Tree_Slenderpoplar_ROOT | 2,292 | 912 | 1 | 4 |
| Tree_Tieredpine_ROOT | 1,848 | 858 | 1 | 3 |
| Tree_Roundmaple_ROOT | 2,560 | 1,048 | 1 | 3 |
| House_Cottage_ROOT | 2,256 | 2,884 | 1 | 9 |
| House_Townhouse_ROOT | 3,434 | 4,384 | 1 | 8 |
| House_Bungalow_ROOT | 2,624 | 3,376 | 1 | 9 |
| House_Family_ROOT | 2,852 | 3,644 | 1 | 8 |
| IceCreamTruck_ROOT | 33,529 | 44,872 | 68 | 187 |
| Crew_ROOT | 2,531 | 4,052 | 1 | 8 |
| Adult_ROOT | 2,507 | 4,024 | 1 | 7 |
| AdultVariant_ROOT | 2,507 | 4,024 | 1 | 7 |
| Child_ROOT | 2,455 | 3,928 | 1 | 7 |
| ChildVariant_ROOT | 2,455 | 3,928 | 1 | 7 |
| FirstPersonHands_ROOT | 658 | 1,192 | 1 | 2 |
| Road_Straight_ROOT | 144 | 92 | 1 | 4 |
| Road_Corner_ROOT | 112 | 60 | 1 | 3 |
| Road_TJunction_ROOT | 228 | 148 | 1 | 4 |
| Road_Crossroads_ROOT | 312 | 204 | 1 | 4 |
| Road_DeadEnd_ROOT | 122 | 80 | 1 | 4 |
| Road_Crosswalk_ROOT | 242 | 176 | 1 | 5 |
| Grass_Cell_ROOT | 14 | 12 | 1 | 1 |
| Sidewalk_Straight_ROOT | 131 | 128 | 1 | 2 |
| Sidewalk_Corner_ROOT | 66 | 88 | 1 | 1 |
| Curb_Ramp_ROOT | 24 | 12 | 1 | 1 |
| Park_Cell_ROOT | 5,861 | 4,924 | 13 | 22 |
| Park_Bench_ROOT | 531 | 572 | 1 | 2 |
| Picnic_Table_ROOT | 464 | 528 | 1 | 2 |
| Park_TrashBin_ROOT | 216 | 360 | 1 | 2 |
| Street_Lamp_ROOT | 320 | 364 | 1 | 2 |
| Picket_Fence_ROOT | 360 | 438 | 1 | 1 |
| Shrub_Round_ROOT | 267 | 360 | 1 | 1 |
| Flower_Patch_ROOT | 474 | 420 | 1 | 4 |
| Mailbox_ROOT | 185 | 232 | 2 | 5 |
| Fire_Hydrant_ROOT | 389 | 384 | 1 | 3 |
| Street_Sign_ROOT | 144 | 128 | 1 | 3 |
| Boombox_ROOT | 867 | 996 | 1 | 5 |
| Baseball_Bat_ROOT | 96 | 188 | 1 | 1 |
| Delivery_Cooler_ROOT | 322 | 424 | 2 | 4 |
| Supply_Crate_ROOT | 369 | 444 | 1 | 1 |
| Ingredient_Carton_ROOT | 79 | 80 | 1 | 2 |
| Restock_Box_ROOT | 47 | 56 | 1 | 2 |
| Serving_Cup_ROOT | 64 | 124 | 1 | 1 |
| Tasting_Spoon_ROOT | 115 | 148 | 1 | 1 |
| Napkin_Dispenser_ROOT | 85 | 100 | 1 | 3 |
| Topping_Jar_ROOT | 158 | 148 | 1 | 3 |
| Serving_Tray_ROOT | 164 | 204 | 1 | 1 |
| Cleaning_Bucket_ROOT | 163 | 256 | 1 | 2 |
| Cleaning_Rag_ROOT | 68 | 88 | 1 | 1 |
| Broom_ROOT | 221 | 220 | 1 | 4 |
| Mop_ROOT | 282 | 336 | 1 | 4 |
| Dustpan_ROOT | 144 | 168 | 1 | 2 |
| Trash_Bag_ROOT | 212 | 268 | 1 | 1 |
| Toolbox_ROOT | 165 | 220 | 1 | 3 |
| Wrench_ROOT | 128 | 160 | 1 | 1 |
| Traffic_Cone_ROOT | 133 | 132 | 1 | 3 |
| Spare_Tire_ROOT | 291 | 392 | 1 | 3 |
| Delivery_Bicycle_ROOT | 2,582 | 2,896 | 7 | 19 |
| PopUp_Stand_ROOT | 980 | 1,204 | 1 | 5 |

The complete review set exports 106,017 vertices and 130,808 triangles, across 195 mesh nodes and 532 material sections. Shared meshes save geometry storage but each visible instance still contributes rendered triangles.

## Practical limits

These are asset counts, not an FPS measurement. The review layout includes the standalone and installed prep sets, multiple character appearances, both standalone and installed coolers, and a populated park built from the furniture kit. Use the individual assets when assembling gameplay. Lighting, shadows, visible NPC count, material sections, resolution, and target hardware still need measurement in Unity.

All character appearances retain their original skinned meshes. Adult and child variants share mesh data. Every cone shell uses 80 source vertices, 156 triangles, and the embedded 512 × 512 flat color texture. There is no physical spiral, normal map, or displacement on the cone.

## Reproduce the audit

`Source/audit_model_budget.py` measures the master and all seven exports. `Source/verify_final_optimization.py` checks the archived optimization candidate against the preserved pre-audit master. The current scene has a later road-layout revision; run `Source/verify_larger_roads.py` with the master loaded to check its dimensions and connections. `Source/verify_workshop_export.py` imports the GLB into a fresh Blender scene and checks its anchors, armatures, weights, and packed texture. Run these scripts through Blender in background mode.

Road cells were enlarged to 24 meters on September 6. This changed their dimensions and review layout without increasing the triangle counts in this table.
