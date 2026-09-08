# Final model audit

The complete workshop exports 130,808 triangles, down from 163,010. This pass removed 32,202 triangles, a reduction of 19.8%. Exported vertices fell from 128,116 to 106,017, including normal, UV, and material splits.

The review scene includes duplicate preparation equipment, every character appearance, linked park furniture, and example cone stacks. These totals describe the model collection, not a required gameplay scene.

| Export | Before triangles | After triangles | Reduction |
| --- | ---: | ---: | ---: |
| Characters | 21,148 | 21,148 | 0.0% |
| IceCreamTruck | 60,022 | 44,872 | 25.2% |
| IceCreamPreparation | 38,212 | 27,494 | 28.0% |
| Neighborhood | 19,734 | 18,332 | 7.1% |
| RoadAndParkKit | 14,066 | 9,710 | 31.0% |
| RemainingProps | 9,828 | 9,252 | 5.9% |
| WorkshopModels | 163,010 | 130,808 | 19.8% |

## Changes

- Scoops: 1,600 to 650 triangles per scoop. The enlarged roof scoop shares the reduced geometry.
- Cone holders: 720 to 360 triangles each.
- Road tiles: 770–902 to 60–204 triangles, by removing flat subdivisions.
- Truck road wheels: 1,600 to 1,050 triangles each.
- Decorative tub meshes: 1,652 to 1,000 triangles each.
- Removed collapsed bevel faces, loose geometry created by cleanup, unused material slots, and a pre-existing junction in the shaker label.
- Preserved the authored surface normals after the first comparison exposed a shading change on the tub rims.

The six skinned character meshes and their weights are unchanged. The 80-vertex textured cone shell is unchanged. Static object names, parent relationships, transforms, visibility, material overrides, and placement anchors remain in place.

## Verification

Inspected 164 distinct saved meshes and checked 471 scene objects. No inspected mesh has non-finite coordinates, zero-area faces, loose vertices, or edges shared by more than two faces. Intentional open surfaces, such as flat decals, are retained.

The before/after surface-distance check uses nearest points on both meshes. The largest sampled distance is 14.9 mm on the enlarged roof scoop; the largest truck-wheel distance is 4.3 mm. This is a geometry comparison, not a pixel-error bound. Close-up renders confirm the prep equipment and cone stacks keep their appearance.

- Checked all 14 road connector edges at multiple points across each road and sidewalk.
- Exercised both floating hands on the player and first-person rigs; only the intended hand vertices moved.
- Checked normalized skin weights, shared customer mesh data, and unchanged character geometry.
- Verified one-, two-, and three-scoop assemblies, the packed flat cone texture, and left-hand drive.
- Imported the complete GLB into a fresh Blender scene. All 93 placement anchors survived within 0.00000024 meters, along with all six armatures and normalized skin weights.

The master, standalone prep and truck copies, intermediate truck source, and all seven GLB exports were updated. The full overview and before/after prep renders are current. No Unity frame-rate benchmark was run.

## Audit files

- `Source/BeforeFinalOptimization.blend` preserves the master before this pass.
- `Source/final-audit-budget-before.json` and `Source/model-budget.json` contain the exported counts.
- `Source/final-optimization-changes.json` lists mesh reductions.
- `Source/final-optimization-verification.json` contains saved-model checks.
- `Source/final-export-verification.json` contains the GLB round-trip results.
- `Source/optimize_workshop_geometry.py` is the final geometry pass. Run it on an appropriate preserved input after rebuilding older assets. It writes a candidate file for review.
- `Previews/Optimization_Before.png`, `Previews/Optimization_After.png`, and `Previews/Workshop_All_Models.png` show the visual checks.

## September 6 road revision

The cells are now 24 × 24 meters with 12-meter roads. This later layout change adds no triangles, so the totals above still apply. The preservation comparisons above describe the optimization pass before resizing. Current road measurements and turn-clearance checks are in `Source/larger-roads-verification.json`.
