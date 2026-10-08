# PS1 bright (style H): game asset production brief

The user picked style H ("PS1 bright") for the co-op zombie ice cream truck game. We are now building the models the
game needs. You own one batch. Read this whole brief, then `/tmp/artstyle/v2/style_H.py` (the style's library and the
existing models), `/tmp/artstyle/v2/render_assets.py` (the render harness) and `/tmp/artstyle/v2/h_example.py`.

## The game in one paragraph

1-4 players defend an ice cream truck driving down a procedurally generated road through a zombie apocalypse. One
drives, one shoots from the roof, one makes ammo in the kitchen in the back (churn milk + sugar + flavoring into a tub,
scoop scoops, fill pints = magazines; a single scoop is a throwable grenade), one runs out at supply stops (dairy farm,
gas station, garden) for ingredients and gun crates. Flavors are ammo types: vanilla (plain), chocolate (pays a tip:
extra money), strawberry (splash burst), mint (freezes zombies into ice blocks that shatter). Zombies: walker, sprinter,
bloater (explodes). Between areas the truck stops at a depot to buy upgrades and the revival item ("Second Scoop").
First person. Big over-the-top FX, limbs fly off.

## Deliverable

Write exactly one new file, `/tmp/artstyle/v2/h_<batch>.py`, starting with `from style_H import *`. Do not edit
`style_H.py`, `common.py`, the harnesses, other `h_*.py` files, the git repo or any `.blend`. Other agents work in
parallel. You may call anything in `style_H.py`; if you need a modified version of one of its functions, copy it into
your module under a new name.

Module contents:

```python
from style_H import *
ASSETS = [("Asset Name", build_fn), ...]   # build_fn(kit, root): build the asset as descendants of root
SPACING = 12                                # meters between asset roots in the harness (raise for big assets)
SCENES = [dict(name="...", build=fn, cam=((x, y, z), (tx, ty, tz), lens), res=(1600, 900))]  # optional
```

`SCENES` are composed shots (camera relative to the scene root) for things a single framed close-up cannot show:
a first-person view, a truck cutaway, a road chunk with props on it, etc.

Render: `cd /tmp/artstyle/v2 && blender -b --factory-startup --python render_assets.py -- h_<batch> [name,name]`.
It prints each asset's size and triangle count, writes close-ups to `out/assets/h_<batch>/` and a labeled contact sheet
to `out/assets/h_<batch>_sheet.png` (full runs only). Look at the images with the Read tool and iterate. Several agents
share one GPU: if a render fails with a GPU or memory error, wait ~20 s and retry.

## Style rules (match the existing H models exactly)

- Late-90s PlayStation low poly with a bright candy palette (use the palette constants in style_H.py) on the dark
  purple world. Hand-built low-poly geometry: `tube` lofts (6-8 sides), `tbox`, `lowball`, bmesh. No subdivision.
- Smooth (gouraud) shading on organic shapes, flat on hard surfaces. Detail lives in tiny pixel textures painted with
  `Canvas` (8-64 px, up to 128 px for buildings and road), sampled Closest, via `tex_mat`/`solid`. Text and logos use
  the pixel `FONT`/`text` helpers. Keep the existing emission baseline (~0.32) so colors stay punchy.
- Reuse the existing palette and motifs: frosting drips, candy stripes, sprinkles, waffle pattern, pastel pints.

## Game-readiness rules

- Meters, Z up, objects face **-Y**. Standing/placed things: root origin at ground level, centered. Handheld items and
  guns: same convention as the existing Scoop Pistol (barrel or front along -Y, grip down).
- Every moving part is its own object on a pivot at its hinge or axis: wheels, doors, lids, cranks, triggers, pumps,
  zombie limbs (limbs fly off), turret yaw/pitch, shutters, hatch.
- Add named empties as sockets where the game needs them, named `<Asset> socket <purpose>`: weapon `muzzle` and `grip`,
  truck `seat`, `turret`, `hatch`, `serving window`, item `hand`, station `use point`, etc.
- Budgets (triangles, as printed by the harness): handheld items and props 50-800, guns 300-1500, characters 600-2500,
  stations 300-1500, vehicles 3000-8000, buildings 800-4000, road chunks 1000-4000 including roadside dressing.
- Deterministic (use `kit.rand`). Names prefixed with the asset name.

## Done

Iterate until every asset reads clearly in its close-up and matches the existing H models. Final reply: 4-8 short
lines (what you built, socket and moving-part conventions you used, triangle totals, known weaknesses). No code.
