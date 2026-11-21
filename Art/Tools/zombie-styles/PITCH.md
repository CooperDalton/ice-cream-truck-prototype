# Heist pitch models brief (round 4)

The game is being re-pitched. Zombies are out. The new story: a crew stole a giant diamond, hid it in a tub of rocky
road in the ice cream truck, and is fleeing town to town to the coast. Nobody can buy the diamond whole and it can't be
split, so the crew sells ice cream to kids to pay Kevin, a forger, for fake plates and papers at each town line (his
price is the town's quota). Cops chase them: plainclothes detectives at the serving window, patrol cars on the road,
officers who board the truck to search it. The run ends at a harbor dock where a buyer's yacht waits.

We need new models in the existing PS1 style (style H) so we can compose in-engine Unity screenshots of the pitch.
Every model is exported to Unity with `export_unity.py`, so it must follow the same conventions as the existing
`h_*.py` batches.

## Read first

- `style_H.py`: the style and its toolkit (`tex_mat`, `solid`, `tube`, `tbox`, `lowball`, `player_arm`, `Canvas`
  pixel textures, palette constants `PINK BLUE MINT YEL SKIN WHITE INK RED PANTS HAIR ...`, `LAV STEEL GLASS ASPH`,
  the 5x5 pixel `FONT` / `text()`).
- `common.py`: `Kit` (`kit.empty`, `kit.prim`, `kit.mesh_from_bmesh`, `kit.rand`, ...).
- The batch closest to your job (named in your section) for construction, texture and naming patterns.
- `h_shop.py` `build_kevin` is a good example of a posed NPC on pivots; `h_characters.py` `build_team_player` is the
  player crew member.

## Conventions (same as every h_*.py batch)

- Module interface: `ASSETS = [(name, build_fn(kit, root))]`, `SPACING = <m between asset roots>`, optional
  `SCENES` (see `render_assets.py`). Asset names below are exact: the Unity side loads them by name.
- Z up, meters. Assets face **-Y**. Root on the floor (z=0) at the footprint center, unless stated.
- Every descendant name starts with the asset name exactly once (use the `named`/`prefixed` wrapper pattern from
  `h_characters.py` / `h_shop.py`). Sockets are empties named `<Asset> socket <purpose>`.
- Deterministic: only `kit.rand` for randomness. Textures are small pixel `Canvas` images (16-128 px), flat bright
  palette, nearest filtering, chunky low-poly geometry with faceted silhouettes, like the existing assets. Text on signs
  is pixel text drawn into the texture.
- Characters: every limb on its own pivot empty (head, arms, legs) so poses can change later. Player crew are about
  1.76 m tall, kids 1.0-1.2 m. Budget about 3-6k tris per character, under 12k per vehicle, scenery pieces under 15k.
- Emissive parts (police lights, diamond glow): use `solid(kit, name, col, emit=<higher>)` like existing glowing parts.
  Glass/transparent materials follow the `__blend` / `__clip` material-name tags described in `export_unity.py`.
- Only Blender 5.2 Python, run headless. Do not edit any file other than your own module, and do not run
  `export_unity.py`, touch the git repo, the `.blend` master file, or the Unity project. Other agents are working in
  parallel on the other modules.

## Render and iterate

```
cd /tmp/artstyle/v2 && blender -b --factory-startup --python render_assets.py -- <module> ["Asset Name,Asset Name"]
```

(`/tmp/artstyle/v2` is a symlink to this folder.) Renders land in `out/assets/<module>/`, a full run also writes
`out/assets/<module>_sheet.png`; the log prints `ASSET <name>: size, tris`. Grep for `Traceback|Error|ASSET|RENDER_DONE`.
Look at every render with the Read tool and fix what you see (floating or intersecting parts, unreadable faces or
text, muddy silhouettes, wrong scale). Compare against existing renders, e.g. render `h_characters "Player Pink"` or
`h_shop "Shopkeeper Kevin"` once for reference. Expect several passes. Several agents share the GPU: if a render fails
with a GPU or memory error, wait 20 s and retry.

## How the models will be used (the planned screenshots)

1. **Serving window**: first person from inside the truck, looking out the +X serving window at a crowd of kids
   holding up coins, with a detective at the back of the crowd taking notes.
2. **Chase**: from the truck roof, looking back down a suburban road at two police cars with lights on; a crew member
   on the roof throwing a cone at them.
3. **Cop on board**: inside the truck kitchen, the freezer open with the diamond in the rocky road tub, an officer
   climbing in through the rear door.
4. **Kevin**: Kevin's bait and documents shack at the town line, Kevin holding up a fake plate, the truck parked
   beside it, a "Leaving Maplewood" sign.
5. **Harbor**: a wooden dock at sunset, the buyer's yacht at the end, crew members carrying the rocky road tub along
   the dock, police cars arriving behind.

## Final report

Reply with 3-6 short lines: each asset, its size and tris, and known weaknesses. The final sheet must exist at
`out/assets/<module>_sheet.png`.
