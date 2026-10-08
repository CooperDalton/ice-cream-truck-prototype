# Extra models brief (round 3)

The user narrowed the choice to two styles, E (1950s B-movie halftone) and H (PS1 bright), and wants to see more models
in each. Extend your existing `style_<KEY>.py`. Do not change how the existing player, zombie, and Scoop Pistol look:
they are already in the master scene. Add new functions and helpers only. Same rules as BRIEF.md otherwise (one file,
deterministic, low or smooth poly, every limb on its own pivot, your style's shape language and FX language).

`/tmp/artstyle/v2` now points at a persistent folder; paths are unchanged. `common.py`, `v1_styles.py` and
`render_v2.py` were restored after a reboot; `python3`-only helper files you had in scratch folders are gone.

## New functions

```python
def build_sprinter(kit, root, hit=False): ...  # fast, lean zombie: dies to any hit, climbs onto the truck
def build_bloater(kit, root, pop=False): ...   # huge swollen zombie (~1.9-2.1 m, very wide), takes 5 body hits
def build_truck(kit, root): ...                # the ice cream truck on a short stretch of road, with extras
def build_shotgun(kit, root): ...              # Sundae Shotgun
def build_props(kit, root): ...                # props table/ground arrangement
```

- **Sprinter**: lean, wiry, leaning forward mid-run, distinct silhouette from the walker. `hit=True`: blown apart by a
  single hit in your FX language (it dies to any hit), limbs flying.
- **Bloater**: obese and swollen with glowing pustules or a distended belly; slow, heavy stance. `pop=True`: the moment
  it bursts — a big over-the-top explosion of goo/ice cream (it kills zombies near it), body chunks flying, the biggest
  FX in the set. The harness places a walker (hit=True) and a sprinter (hit=True) on either side of it.
- **Truck** (root at ground level, truck faces -Y, about 5.5 m long, 2.3 m wide, 2.8-3.2 m tall incl. roof gear):
  a 1950s-style or 90s-style ice cream truck in your style, with a serving window on the +X side, a roof hatch with a
  ladder, a rooftop turret mount with the Soft Serve Minigun (multi-barrel, fed by a pint hopper), a big roof sign or
  giant cone, a front plow or bumper. Put it on a short road chunk (about 16 m along Y, 8-10 m wide: asphalt, lane
  markings, curb or dirt shoulder) with 2-4 roadside pieces (street lamp, road sign, wrecked car, fence, mailbox, ...).
  Add the player standing on the roof at the turret, a sprinter climbing the +X side, and 2-3 walkers on the road.
  Camera looks from front-right (+X, -Y) and above.
- **Sundae Shotgun**: about 0.75 m long, barrel along -Y, pump action, double barrel or wide muzzle shaped like a sundae
  boat, fed by pints; reads in side profile from +X (it is shown under the Scoop Pistol).
- **Props**: within about 2 m x 1.2 m around the root on the ground (z=0): a flavor tub, a filled pint, a milk crate
  with bottles, a sugar sack, a cocoa or mint flavoring bag, and a gun crate (lid open, a gun inside optional).

Budgets: sprinter/bloater under ~15k tris, truck under ~30k (road and roadside pieces extra, keep them light).

## Render

```
cd /tmp/artstyle/v2 && blender -b --factory-startup --python render_more.py -- <KEY> [lineup,pop,truck,arsenal,props]
```

Writes `out/<KEY>_more_<shot>.png` and, for a full run, `out/<KEY>_more_sheet.png`. The lineup shows player, walker,
sprinter, bloater side by side. Also re-run `render_v2.py -- <KEY>` at the end to confirm the original three shots are
unchanged. Iterate by looking at the renders. Final report: 3-6 short lines.
