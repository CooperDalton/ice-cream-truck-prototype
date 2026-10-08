# Zombie ice cream truck game: art style mockup brief (v2)

You are designing and modeling, in Blender via Python, one art style for a co-op first-person game: players defend
an ice cream truck from zombies by shooting ice cream out of guns. A first round of mockups used one generic
primitive-stacking character generator for every style and only swapped shaders. The user rejected that: every style
must now have its own character design and shape language, built with modeling methods that suit the style.

## Your deliverable

Write exactly one file: `/tmp/artstyle/v2/style_<KEY>.py`. Do not edit any other file (`common.py`, `render_v2.py`,
`v1_styles.py`, other agents' `style_*.py`), and do not touch the git repo or any `.blend` file. Other agents are working
in parallel on other styles.

Module interface (see `/tmp/artstyle/v2/style_example.py` for a minimal working example, and read
`/tmp/artstyle/v2/common.py` for the toolkit):

```python
from common import *          # Kit, hexc, hex_scale, star_mesh, SHADERS, bpy, bmesh, math, random, Vector, Matrix, Euler
KEY = "<KEY>"; LABEL = "<style name>"
SHADER = '<one of common.SHADERS>'   # default material look for kit.mat(); you may also build custom node materials
WORLD = "#rrggbb"; FLOOR = "#rrggbb"
def make_kit(col, seed): return Kit(col, SHADER, seed)
def build_player(kit, root): ...
def build_zombie(kit, root, hit=False): ...
def build_gun(kit, root): ...
def setup(scene, stage_collection): ...   # optional: extra lights or scene settings
def post(path): ...                       # optional: 2D post-process of each rendered PNG (ImageMagick `magick`)
```

Build every object as a descendant of `root` (parent=root or a pivot under it), except free-flying FX in the hit pose,
which may also be parented to root. The harness places the roots. All functions must be deterministic (use `kit.rand`).

## Conventions

- Z up, meters. Characters face **-Y**, feet at z=0 at the root origin, height 1.3-1.9 m depending on style.
  The character's right hand is on the **-X** side.
- Gun: real scale, about 0.25-0.35 m long, barrel along **-Y**, grip pointing down (-Z), origin near the body center.
  The gun camera looks from the +X side, so the side profile must read clearly.
- Budget: low poly or smooth poly, real-time friendly: roughly under 15k triangles per character after modifiers,
  under 5k for the gun.

## What to model

1. **Player**: an ice cream truck worker in a zombie apocalypse. Paper soda-jerk hat (or the style's equivalent),
   apron, cooler backpack with spare pints. Holds the Scoop Pistol in the right hand, arm raised and aiming forward
   (build it by calling `build_gun(kit, <pivot>)` at a suitable scale inside the hand).
2. **Zombie**: shambling, hunched, unmistakably a zombie (exposed brain, mismatched eyes, torn clothes, an ice cream
   splat on it, etc.). Every limb must be its own object on its own pivot: in the game limbs fly off.
   - `hit=True`: the same zombie recoiling from a hit, with its **left arm (+X side) detached and flying away**
     roughly 0.5 m out, up, and toward the camera's right (world +X, -Y, +Z), spinning. Add a big, over-the-top burst of
     blood and ice cream in **your style's own FX language** (fun and extra, not gross): drops, chunks, splats on the
     floor, and style-specific extras (smoke puffs, starbursts, confetti, shards, voxel debris, etc.).
3. **Gun (Scoop Pistol)**: waffle-cone flared muzzle, a pint-tub magazine on top with a chocolate scoop and sprinkles,
   grip, trigger and guard. Redesign it in your style's shape language, keeping those features recognizable.

Shape language matters most: silhouettes, proportions, how limbs connect, faces, and construction. Do not build the
whole design out of generic stacked spheres/boxes/cylinders. Use `kit.skin` (continuous skeleton bodies), `kit.cage`
(box-modeled cages, faceted when subsurf=0), `kit.mirror`, `kit.voxels`, bmesh, curves, image textures, or anything else
in Blender. Primitives are fine for small details.

## Rendering and iteration

```
cd /tmp/artstyle/v2 && blender -b --factory-startup --python render_v2.py -- <KEY>
```

This writes `out/<KEY>_characters.png`, `out/<KEY>_gun.png`, `out/<KEY>_impact.png` and `out/<KEY>_sheet.png`
(all three side by side). Append a comma-separated subset to render fewer shots, e.g. `-- <KEY> characters`.
Cameras and the two suns are fixed by the harness so all styles compare fairly; `setup()` may add lights. Errors print
as Python tracebacks; grep the output for `Traceback|Error|RENDER_DONE`.

Look at your renders with the Read tool every iteration and fix what you see: floating or intersecting parts, a gun
not in the hand, unreadable faces, a muddy silhouette, FX that look like noise. Iterate until it looks like a convincing
concept render for the style (expect 4-10 render passes). Several agents share one GPU: if a render fails with a GPU or
memory error, wait about 20 seconds and retry.

## Final report

When done, reply with 3-6 short lines: the design idea, how it is constructed, and any known weaknesses. Do not paste
code. The final sheet must be at `/tmp/artstyle/v2/out/<KEY>_sheet.png`.
