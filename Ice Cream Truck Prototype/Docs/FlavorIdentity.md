# Flavor appearance

Each flavor uses the same color and chunk treatment in its tub, scoop, and order picture. Chunky scoops retain their appearance when loaded into the scooper, placed on a cone, or restored in Park route.

| Flavor | Appearance |
| --- | --- |
| Vanilla | Cream, plain |
| Cookie cream | Cream with dark cookie chunks |
| Strawberry | Pink, plain |
| Cherry | Pink with deep red fruit pieces |
| Pistachio | Pale green, plain |
| Mint | Mint green with dark chocolate chunks |
| Coffee | Light brown, plain |
| Chocolate | Brown with dark chocolate chunks |
| Mango | Yellow, plain |
| Peach | Peach with orange fruit pieces |
| Blueberry | Lavender, plain |
| Blue moon | Light blue, plain |

`FlavorSO` owns the scoop mesh, base material, chunk material, and order picture. The five chunky flavors share `Assets/Art/FlavorVisuals/ChunkyScoop.asset`; each tub uses the same chunk material as its flavor. Plain flavors use `Assets/Art/PlainScoop.asset`.

Five order pictures were edited with the built-in image tool. Vanilla, strawberry, blueberry, and pistachio had their flecks removed. Chocolate received dark chunks. The prompts and output paths are recorded in `FlavorIconEdits.json`. Existing PNG metadata was preserved.

# Object grips

Both gameplay scenes and the cone prefab contain editable `Hand grip` transforms. Each grip describes where and how the right hand holds that object. `FloatingHands` follows that transform during carrying and gestures. Handle, bottle, and cone meshes provide closed fingers sized for the object; the tray retains the open supporting palm.

The scooper has an angled carry pose. Scooping aligns its bowl with the tub path while the hand follows its handle. The original imported open-hand mesh remains available for empty hands.

The authoring scripts in `Tools` record the scene and mesh changes. Their `Build` methods are one-time authoring operations, not startup code. Do not rerun them over the finished scenes. `Refine` and `RefineChunks` update their existing mesh assets while preserving references.
