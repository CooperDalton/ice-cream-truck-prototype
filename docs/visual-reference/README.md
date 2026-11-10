# Big Milk Strikes Back (Divorced Dads): visual style reference

This document describes the look of the Divorced Dads prototype, released to players as "Big Milk Strikes Back". It is the reference for the production game. Every value comes from the prototype's source.

**Setting:** divorced dads run an ice cream truck to pay off Big Dairy. They scavenge ingredients, churn flavour tubs, feed kids at the serving window, and get home before the sugar-curfew cops come out.

**Art style:** internally "Style H, PS1 bright". Late-90s PlayStation low poly in a candy-pastel palette. Tiny point-sampled pixel textures. Every surface carries a baked self-glow. The game renders at 480x270 and is shown full screen with an ordered dither and colour quantisation. A day/night cycle runs from a pale-blue morning through a salmon dusk to a navy curfew night.

**Tone:** comedic suburban satire, never grim. Ice cream hits explode into confetti and sprinkles, and every action pops comic text ("SPLORCH!", "BUSTED! -$40", "*BUUUURP*").

## Screenshots in this folder

| File | Shows |
|---|---|
| `day-driving.png` | Morning drive through Maple Grove from the driver's seat |
| `day-serving-window.png` | Kids at the serving window with thought bubbles, holding a cone |
| `day-roof-turret.png` | Soft Serve Minigun on the roof, Big Dairy's lot and The Flats behind |
| `dusk.png` | Dusk sky and the "DUSK" banner |
| `night-curfew.png` | Curfew night and the "SUGAR CURFEW" banner |

## Source of truth

All paths are relative to `Zombie Ice Cream Truck/` unless they start with `Art/`.

| What | File |
|---|---|
| Style library (palette, pixel canvases, low-poly builders) | `Art/Tools/zombie-styles/style_H.py` |
| Characters, items, town | `Art/Tools/zombie-styles/h_dads_characters.py`, `h_dads_items.py`, `h_dads_town.py` |
| Van, guns, road kit | `h_truck.py`, `h_weapons.py`, `h_road.py` |
| Scene, lighting, day/night keys, FX, HUD layout | `Assets/Scripts/Editor/DivorcedDads/DivorcedDadsSceneBuilder*.cs` |
| View behaviour | `Assets/Scripts/DivorcedDads/*.cs` |
| Screen shader | `Assets/Art/Shaders/PS1Dither.shader` |
| Model import rules | `Assets/Scripts/Editor/PS1ArtPostprocessor.cs` |
| HUD sprites and icons | `Art/Tools/zombie-styles/hud_sprites_dads.py`, `hud_icons_dads.py` |

---

## 1. Render pipeline

### 1.1 Screen setup

**The game camera** renders into a **480x270** render texture: 24-bit depth, point filter, no anti-aliasing, saved as `Art/Dads PS1 Screen.renderTexture`. The low resolution is what makes the pixels.

| Setting | Value |
|---|---|
| FOV | **75** |
| FOV while aiming | **55** |
| FOV on the roof turret | **60** |
| FOV blend | `1 - exp(-14·dt)` |
| Driving | no separate FOV |
| Near / far clip | 0.05 / **400** |
| Clear | solid colour, set every frame to the sky colour (§2) |
| Post-processing | off (no URP camera data) |

**The display camera** draws only the UI layer and clears to black.
- A full-screen RawImage on the "Screen" canvas shows the render texture through the **PS1 Dither** material.
- The HUD canvas draws on top at full resolution, so it stays crisp.
- Both canvases use Screen Space Camera mode and scale with screen size from a **1280x720** reference.

### 1.2 PS1 Dither shader (`ZombieTruck/PS1 Dither`)

| Parameter | Value |
|---|---|
| `_Levels` | **24** levels per channel |
| `_DitherStrength` | **1** |

The fragment program, per pixel of the 480x270 source:

```
texel     = floor(uv * texSize)
color     = sample(texel center)
threshold = (bayer4x4[texel.x % 4 + (texel.y % 4) * 4] / 16 - 0.5) * strength
bayer4x4  = {0,8,2,10, 12,4,14,6, 3,11,1,9, 15,7,13,5}
color     = floor(color * 24 + threshold + 0.5) / 24
```

The result is chunky 4x pixels at 1080p, a fine checkerboard dither in gradients (most visible in the sky and fog), and slight banding.

### 1.3 URP settings

| Setting | Value |
|---|---|
| Rendering path | Forward+ |
| HDR | on |
| MSAA | off |
| Render scale | 1 |
| Main-light shadows | 2048 map, **50 m** distance, 4 cascades (0.123 / 0.293 / 0.536), soft shadows at high quality, depth bias 0.1, normal bias 0.5 |
| Additional lights | per pixel, up to 4 per object |

- **SSAO** renderer feature: intensity **0.4**, direct lighting strength 0.25, radius 0.3, depth-normals source.
- No volume post-processing: no bloom, tonemapping, grading or vignette.
- The whole look comes from palette, emission, lighting and the dither.

---

## 2. Lighting and the day/night cycle

### 2.1 Clock

- **Length:** a day lasts `DayLength = 300` s. The clock runs from 0 to 1 during the Day, Dusk and Night phases.
- **Phases:** dusk at **0.70** and night at **0.82**. Morning and the tutorial sit at clock 0.
- **HUD time:** 0 = 9:00 AM, 1 = midnight, in 5-minute steps. So 0.30 = 1:30 PM, 0.62 = 6:18 PM, 0.70 = 7:30 PM, 0.82 = 9:18 PM.
- **Driver:** `DayNight.cs` sets these every frame:
  - `RenderSettings.ambientLight` (flat ambient)
  - `RenderSettings.fogColor` = sky colour
  - `camera.backgroundColor` = sky colour
  - sun colour and intensity

### 2.2 Keyframes (`DivorcedDadsSceneBuilder.Scene.cs:139-159`)

Gradients use Blend mode. Blank cells mean no key at that clock value for that channel.

| Clock | Time | Sun colour | Ambient (flat) | Sky = fog = clear colour |
|---|---|---|---|---|
| 0.00 | 9:00 AM | `#ffd9b3` (1, .85, .7) | `#8c80a6` (.55, .5, .65) | `#c7d1ff` (.78, .82, 1) |
| 0.20 | 12:00 PM | | | `#8cccff` (.55, .8, 1) |
| 0.30 | 1:30 PM | `#fff7e6` (1, .97, .9) | `#9e99b8` (.62, .6, .72) | |
| 0.60 | 6:00 PM | | | `#99bfff` (.6, .75, 1) |
| 0.62 | 6:18 PM | `#ffcc8c` (1, .8, .55) | | |
| 0.68 | 7:12 PM | | `#99738c` (.6, .45, .55) | |
| 0.72 | 7:48 PM | | | `#ff8c73` (1, .55, .45) salmon dusk |
| 0.74 | 8:06 PM | `#ff7359` (1, .45, .35) | | |
| 0.78 | 8:42 PM | | `#594780` (.35, .28, .5) | |
| 0.80 | 9:00 PM | | | `#73408c` (.45, .25, .55) violet |
| 0.85 | 9:45 PM | `#7380e6` (.45, .5, .9) moonlight | | |
| 0.86 | 9:54 PM | | `#2e295c` (.18, .16, .36) | |
| 0.88 | 10:12 PM | | | `#1a0f38` (.1, .06, .22) |
| 1.00 | 12:00 AM | `#5966cc` (.35, .4, .8) | `#241f4d` (.14, .12, .3) | `#0f0a26` (.06, .04, .15) |

**Sun intensity** curve, as (clock, intensity): (0, 0.9), (0.3, 1.35), (0.7, 1.0), (0.8, 0.35), (1, 0.25).

**Sun angle:**
- Before night, pitch is `lerp(20°, 185°, clock / 0.82)` with yaw -35°.
- After night it is fixed at (50°, -35°, 0) as a moon.
- It slerps toward the target at `1 - exp(-2·dt)`.
- The light is directional with soft shadows.

**Fog:** **linear, 45 m to 170 m**, coloured like the sky. Distant scenery fades into the sky, which hides the 400 m far clip.

**Ground plane:** a 1200x600 m cube, URP Lit, `#4d9e52` (0.3, 0.62, 0.32).

### 2.3 Practical lights

| Light | Values | When |
|---|---|---|
| Street lamps | Point light, colour (1, .82, .55) `#ffd18c`, intensity 2.2, range 11 m. Only every other lamp has a light (`(x+z) % 2 == 0`). | Clock ≥ 0.67, unless knocked down |
| Van headlights | Two spot lights at (±0.75, 1.1, 3.3), pitched 12° down, colour (1, .93, .75) `#ffedbf`, intensity 6, range 22 m, 60° cone | Clock > 0.65 |
| Cop sirens | Two 0.07 m unlit cubes on the cop's head, red (1, .15, .2) `#ff2633` and blue (.2, .4, 1) `#3366ff`. They alternate every 0.125 s (`repeat(t·4, 1) < 0.5`). No light component. | Only while chasing |

**Windows** do not light up at runtime. About 50% of house windows are painted lit (`#ffd36b` with pink curtains) straight into the textures, and they glow through the 0.32 emission baseline.

---

## 3. Materials (every art asset)

### 3.1 Material model

**Blender** (`style_H.tex_mat`):
- One Principled BSDF. A single image texture feeds both **Base Color and Emission Color**.
- Interpolation **Closest**. Roughness 0.8. Specular IOR level 0.2. Emission strength **0.32** by default.

**Unity** (`PS1ArtPostprocessor`):
- URP Lit with base map = emission map = the texture.
- `_EmissionColor = (e, e, e).gamma`, where e is the Blender strength.
- Metallic 0, **smoothness 0.15**.
- Textures: point filter, no mipmaps, uncompressed, clamp. `__repeat` textures repeat.
- Material suffixes:
  - `__clip`: alpha clip 0.5, double-sided. Used for picket fences, chain-link and valances.
  - `__blend`: transparent, base alpha 0.55, emission x0.25. Used for glass and ice.

**Why the emission matters:** the self-glow keeps colours saturated in shadow and at night, so a navy night still reads as candy-coloured, just darker.

### 3.2 Emission scale (Dads assets)

| Emission | Surfaces |
|---|---|
| 0.05-0.15 | Voids and darks: crawlspace, pits, asphalt, tyres, bus black, dumpster lid, vault interior, soil 0.12-0.2 |
| 0.2 | Belts, holsters, straps |
| **0.32** | **Baseline** |
| 0.35-0.45 | Most props |
| 0.36-0.40 | Flavour creams: mud 0.36, coffee and rocky road 0.38, strawberry 0.4 |
| 0.5-0.75 | Lane yellow 0.5, flowers 0.5, water 0.5-0.6, bills 0.55, gold cream 0.55, sprinkles 0.6, ice 0.6, gold trim 0.6-0.7, coins 0.7, thought bubble 0.75 |
| 0.8-1.6 | Glows: TV 0.8, fountain 0.9, watch and insulin-pump screens 0.9, headlights 1.2, diamond 1.2, cop radio 1.4, bus flashers 1.4, porch lamp and flood lamps 1.6, cigar ember 1.6 |
| 2.0-2.2 | Gold Leaf and lunch-money sparkle stars |

### 3.3 Builder materials (URP)

| Material | Shader | Colour | Use |
|---|---|---|---|
| Dads Pedestal | Lit | (1, .31, .64) `#ff4fa3` | Turret post, shop pedestals |
| Dads Turret Deck | Lit | (.22, .95, .76) `#38f2c2` | Roof deck |
| Dads Ice | Unlit, transparent | (.6, .95, 1, .5) | Brain-freeze head cube |
| Dads Steel | Lit | (.75, .75, .85) | Cuffs, clock post |
| Dads Clock | Lit | (1, .88, .29) `#ffe04a` | Time clock |
| Dads Ink | Lit | (.1, .06, .2) | Card slot |
| Dads Label Backing | Unlit, transparent | (.1, .06, .2, .85) | Price tags |
| Dads Cream | Lit | white, tinted per kid | Face cream |
| FX Atlas | Particles/Unlit, opaque, alpha clip 0.5, double-sided | | Particles |
| FX Atlas Glow | Particles/Unlit, additive | | Glow particles |

---

## 4. Colour palette

### 4.1 Core candy palette (`style_H.py`)

| Name | Hex | Role |
|---|---|---|
| PINK | `#ff4fa3` | Signature colour: truck band, curbs, HUD panels, strawberry |
| MINT | `#38f2c3` | Frosting drips, window frames, picket rails, HUD secondary |
| YEL | `#ffe14a` | Lane dashes, trims, HUD money and key text |
| BLUE | `#2e86ff` | Pinstripes, Dad 2, text drop shadows |
| WHITE | `#fff7ee` | Warm off-white (never pure white) |
| INK | `#1b1033` | Outlines, pupils, dark trim, HUD text outline |
| RED | `#ff2448` | Cherries, sirens, warning text |
| DRED | `#b0103a` | Dark red |
| ORNG | `#ff8a3d` | Accents, crocs, Fat Kid tee |
| PURP | `#8f5bff` | Accents, Hoodie kid, thought-bubble rim |
| LAV / LAV_D | `#b48cff` / `#8f66e6` | Lavender accents |
| ZG | `#9cff57` | Lime accents, watch LCD |
| SKIN | `#ffc29e` | Base skin |
| HAIR | `#7a3a1c` | Base hair |
| PANTS | `#3c3fb8` | Indigo |
| CHOC | `#6e3a1e` | Chocolate |
| STEEL | `#d9d4ff` | Metal is lavender, never grey |
| GLASS | `#2a2f6b` | Dark window glass |
| ASPH | `#3d3358` | Purple asphalt |

**Rules:**
- Shadows lean purple.
- Shades come from `hex_scale(col, f)`, which multiplies RGB by f (0.86 for speckle, 0.8 for rims).
- Every flat colour is an 8x8 texture with 9 random darker texels, so nothing is perfectly flat.

### 4.2 Road and ground (`h_road.py`)

All three districts share the road kit.

| Element | Colours |
|---|---|
| Asphalt | `#3d3358`, speckles `#4a4068` / `#2f2745` / `#55497a`, cracks `#231c36` |
| Curbs | PINK/WHITE candy stripes, 0.3 m |
| Sidewalk | Lavender `#cfc6f0`, joints `#9d90cc` |
| Grass | Teal-green `#36a46a`, flecks `#2c8c5a` / `#43bd78` / `#4fd68a`, plus pink/yellow/white flower texels |
| Lane lines | White edge line at 3.7 m, yellow dashes |
| Trees | Leaves `#2fae66` / `#3fcf7a` / `#26995a`, pines `#1f9e7a` / `#2bbf8f`, bark `#7a4a5a` |
| Lamp poles | `#5b5fc0` |

### 4.3 Characters (`h_dads_characters.py:15-25`)

| Name | Hex |
|---|---|
| SKIN_D / SKIN_DD / SKIN_PALE | `#f0a888` / `#e0906c` / `#ffd9c4` |
| KHAKI / _D / _L | `#d9c08a` / `#b89a62` / `#ecd6a4` |
| DENIM / _D / _L | `#4a72d6` / `#3456b0` / `#6f92e8` |
| SWEAT / _D / _L | `#aaa6bf` / `#8c88a6` / `#c4c0d6` |
| NAVY / _D | `#24307a` / `#18205a` |
| GOLD / _D | `#ffd23a` / `#d9901a` |
| LEAF / _D | `#3fdc6e` / `#1f9e4a` |
| BELT | `#5a3418` |
| LEATHER | `#8a4a26` |
| TEE / _D | `#ece6f4` / `#cfc6e0` |
| BLACK | `#20182c` |
| LENS | `#2a1f45` |
| COW_K (cow spots) | `#241a30` |

Face colours: lip `#ff6f8f`, mouth `#8a1f3d`, open mouth `#c0305a`, blush `#ff8fae`, kid-eye glint `#6a5aa8`.

### 4.4 Treats (flavours)

| Treat | In-game tint (`TreatPalette.cs`) | Model cream / shade / highlight | Chunks |
|---|---|---|---|
| Mud | (.48, .35, .24) `#7a5a3d` | `#7a5a3c` / `#5e4430` / `#9a7a58` | pebbles, gummy worm `#ff6a3d` |
| Strawberry | (1, .31, .64) `#ff4fa3` | `#ff9fcf` / `#ff7dbb` / `#ffd6ea` | berry chunks, RED |
| Coffee | (.78, .57, .38) `#c79161` | `#c69261` / `#a8743f` / `#e0b080` | beans `#3a1c0c` |
| Rocky Road | (.43, .23, .12) `#6e3b1f` | `#8a4a26` / `#6a3418` / `#a8643a` | marshmallows WHITE, nuts `#d9a868` |
| Gold Leaf | (1, .85, .25) `#ffd940` | `#fff1c7` / `#f0d590` / `#fffbea` | gold flakes glowing at 1.3 |
| Vanilla (default) | (1, .95, .85) | | |

**Cones:**
- Sugar cone `#f0b860`.
- Waffle `#ffcf5a` with grid `#d9862a`.
- Chocolate-dip waffle `#6e3a1e`.
- Double waffle with a pink dip and sprinkles.

**FX tint colours** (`DadsEffects.cs`):

| Name | Value |
|---|---|
| Gold | (1, .85, .2) |
| Pink | (1, .31, .64) |
| Mint | (.22, .95, .76) |
| Siren | (.35, .55, 1) |
| Green | (.6, .9, .3) |
| Dust | (.85, .78, .7) |
| Leaf | (.35, .75, .3) |
| Lactose gas | (.55, .8, .25) |

**Rainbow confetti:** `#ff4fa3`, `#ffe04a`, `#38f2c2`, `#2e87ff`, white.

### 4.5 Town and district colours (`h_dads_town.py`)

**Suburb house palettes** (`HOUSE_COLORS`), as siding / roof / door / shutters:

| # | Siding | Roof | Door / shutters |
|---|---|---|---|
| 1 | mint `#9ff0d8` | blue `#5b6cff` | PINK / BLUE |
| 2 | pink `#ffc2dc` | purple `#8f5bff` | MINT / PURP |
| 3 | lemon `#fff09a` | coral `#ff6f8f` | BLUE / MINT |
| 4 | periwinkle `#c8d8ff` | teal `#3fae8a` | YEL / PINK |
| 5 | peach `#ffd8b0` | grape `#6a5aa8` | RED / BLUE |
| 6 | lime `#d8ffc8` | brick-orange `#e86a4a` | PURP / ORNG |

Shared house parts: foundation `#9a8fc8`, porch `#e6e0ff`, brick chimney `#c95a7a`.

**Districts:**
- **The Flats** (trailer park):
  - Dirt lot `#8a6a5a`.
  - Trailers in (MINT, PINK), (YEL, BLUE), (pink `#ffc2dc`, MINT) and (`#c8d8ff`, ORNG), with rust `#b8703a`.
  - Chain-link `#c9c2f0`. Junk car `#b48cff` on cinder blocks.
- **Maple Grove** (suburbs, park, school, coffee strip):
  - Pastel houses with white picket fences on mint rails.
  - Park: mulch `#a85a3a`, rubber play surface `#ff8a3d`.
  - School: pink brick `#ff8f8f`, bus `#ffc93a`.
  - Coffee strip: shopfronts `#ffe0b0` / `#c8f0ff` / `#e8d8ff`, pavers `#e8907a`.
- **Hillside Estates** (mansions):
  - Cream `#fff1dc`, gold trim `#ffd23a`, grape roofs `#6a5aa8`, hedges `#2a9e5a`.
  - Marble `#f4f0ff`, wrought iron `#4a3a6e`, white gravel, red carpet.
- **Big Dairy's Lot:**
  - A 10x9x8 m giant milk carton: white, BLUE bands, cow spots, a PINK label band.
  - Pink counter `#d63a86`, yellow bollards.
- **Creek:** water `#4fa8ff`, bank `#8a6a4a`, PINK bridge rails.
- **Moving Day yard:** "HERS" house in pink, "HIS" trailer in periwinkle, a purple car, moving boxes `#d8a868`.

### 4.6 UI palette (`hud_sprites_dads.py:23-27`)

| Name | Hex |
|---|---|
| INK | `#1b1033` |
| PINK / _L / _D | `#ff4fa3` / `#ff9fd0` / `#b0306f` |
| MINT / _L / _D | `#38f2c3` / `#a8ffe8` / `#1f9e7a` |
| GOLD / _L / _D | `#ffcf3a` / `#fff0a0` / `#b8860b` |
| LAV / LAV_D | `#b48cff` / `#6a4fb0` |
| CREAM / _D | `#fff2d6` / `#e0b98a` |
| WHITE | `#fff7ee` |
| YEL | `#ffe14a` |
| BLUE | `#2e86ff` |
| RED | `#ff2448` |

---

## 5. Modelling and texture rules

### 5.1 Geometry

- Metres. Blender is Z up with characters facing -Y; Unity maps as `(-x, z, -y)`.
- Feet at the root origin. The right hand is on Blender -X.
- **Hand-built low poly, no subdivision.**
  - `tube` lofts, 6 sides on limbs and 8 on torsos, heads and barrels.
  - `tbox` boxes with per-face UVs.
  - `lowball` (subdivision-1 icospheres).
- **Shading:** gouraud on organic shapes, flat on hard surfaces.
- **Moving parts:** every one is its own object pivoted at its hinge.
- **Sockets:** empties named `<Asset> socket <purpose>`, for example `socket camera`, `socket bubble`, `socket mouth`, `socket scoop 1..3`, `socket serving window`, `socket turret`.
- **Triangle budgets:**

| Asset class | Budget (tris) |
|---|---|
| Props | 50-800 |
| Guns | 300-1500 |
| Characters | 600-2500 |
| Vehicles | 3000-8000 |
| Buildings | 800-4000 |

- Actual counts:

| Asset | Tris |
|---|---|
| Dads | 1016-1224 |
| Kids | 864-1088 |
| Cop | 1422 |
| Big Dairy | 1228 |
| First-person arms | 780 |
| Van | 7618 |

### 5.2 Pixel textures

All detail is painted texel by texel. There are no normal or roughness maps, and nothing is larger than 160 px.

| Use | Size (px) |
|---|---|
| Heads, torsos | 64x64 |
| Limbs | 16x32 |
| Hands, shoes | 16x16 |
| Solid colours | 8x8 |
| Buildings | 128x128 |
| Trailers | 128x64 |
| Asphalt | 64x64 |
| Ground | 32x32 |

- **Speckle:** 2-3 nearby tones over a base. Cracks are random walks.
- **Pixel font:** `FONT2`, 3x5 glyphs on a 4-texel advance, covering A-Z, 0-9 and `$ - . :`. Integer scale k. A coloured drop shadow sits at (+k, -k).
- **Signs:** `sign_tex` uses a 6k line height and a 2 px border.

### 5.3 Recurring motifs

- **Frosting drips:** a MINT band with drips 2-4 texels wide and sprinkle texels. Used on the truck top and the HUD banner.
- **Candy stripes:** awnings in 4 px pink/white bands, pink/white curbs, hazard stripes in 4 px YEL/INK diagonals.
- **Waffle grid:** `(x+y)%5==0 or (x-y)%5==0` texels set to `#d9862a` on a `#ffcf5a` base.
- **Sprinkles:** PINK, BLUE, YEL, MINT, WHITE, PURP and ORNG, emission 0.6-0.9.
- **Signage:**
  - Big Dairy lot: "BIG DAIRY" in white on pink with a `#a8206a` shadow, "WE OWN YOU", "BIG DAIRY / LOANS 24-7", "PAY HERE", "CLOCK OUT", "NO / REFUNDS", "BESSIE".
  - Maple Grove: "NO DADS" on the treehouse, "MAPLE / PARK", "MAPLE GROVE ELEMENTARY", "BEAN THERE", "SUDS", "VIDEO".
  - Hillside: "PRIVATE".
  - Moving Day: "HERS", "HIS".
  - Elsewhere: "PERMIT / ONLY", "VAULT".

---

## 6. Characters

### 6.1 Dads

The shared rig:
- Hips 0.87 m, head pivot 1.425 m, head scale 1.14.
- A jowl and a forward belly.
- Tired eyes.
- A tan line where the wedding ring was, on the left hand.
- 12 arm-hair pixels.

| Dad | Height | Look |
|---|---|---|
| Pink | 1.86 m | Pink Hawaiian shirt (leaves, flowers) open at the collar with chest hair. Khaki cargo shorts. Tube socks in sandals. Bucket hat `#f2e6c4` with a pink band. Yellow fanny pack. Sunburnt nose, freckles, grin. |
| Blue | 1.84 m | Tucked blue polo, gold belt buckle, pleated khaki shorts, pale legs. Chunky white dad sneakers. Navy cap with sunglasses pushed up. Big droopy mustache. Whistle on a lanyard. |
| Mint | 1.77 m, slimmer, head 1.05 | Mint fleece vest over a long-sleeve tee, jeans, trail shoes. Grey hair, goatee. Mint visor. Phone holster. |
| Yellow | 1.80 m, slouched | "DAD / ROCK" band tee with a coffee stain. Grey sweatpants, orange crocs. Backwards purple cap. Beard, bags under the eyes. |
| First-person arms | | Pale sleeve with a pink band, hairy forearms, ring tan line. Chunky digital watch: LCD `#9cff57` reading "12". |

### 6.2 Kids

All kids:
- About 1.2 m tall, head scale **1.36** (big heads), hips 0.47 m.
- Solid ink eyes with a white glint.
- A thought bubble showing the scoop they want: white puffs with a purple rim.

| Kid | Look |
|---|---|
| Stripes | Red-striped tee, smiley badge, spiky cowlick, gap-tooth grin |
| Overalls | Denim bib with gold buttons, pigtails with pink ties |
| Hoodie | Purple hoodie, orange backpack |
| Dress | Yellow polka-dot sundress, pink bow |
| Fat Kid | 1.58 m, head 1.62. Orange tee, "YUM" bib with chocolate smears, propeller beanie. |
| Lactose Kid | Green-tinged skin `#e4f0c4`, queasy face, "SOY" juice box |
| Diabetic Kid | Insulin pump with an LCD reading "120", medical bracelet |
| Rich Kid | Navy blazer with a gold crest, red bow tie, slicked blond hair, smug smirk |

### 6.3 Adults

- **Cop** (1.83 m):
  - Big gut. Blue shirt `#5a7ef0` with a gold badge, navy pants with yellow stripes, navy police cap.
  - Gold aviators with pink-tinted lenses, huge mustache, no visible eyes.
  - Pink-frosted donut in hand. Siren cubes on the head.
- **Big Dairy, the loan collector** (1.98 m, hands scaled 1.35):
  - Cow-print suit, black sunglasses, slicked hair.
  - Glowing cigar, gold chain with a milk-drop pendant, diamond pinky ring.
  - Says "You got my money?"

### 6.4 Van

- It is the original ice cream truck model, flipped to American left-hand drive.
- **Body:** white, a pink top band with a blue rule, mint frosting drips, "ICE CREAM" pixel lettering with cone icons. Pink/white scalloped awning over the serving window.
- **Interior:** pastel kitchen fixtures: churn, scoop counter, gun rack, hopper gauge, roof bell, ingredient bins.
- **Roof:** a turret platform (pink post, mint deck) with the **Soft Serve Minigun** at 1.5x scale. Loudspeaker horns.
- **Damage:** no dents. Hood smoke above 20% damage, plus a TRUCK bar on the HUD.

### 6.5 Guns and items

**Guns:**
- **Scoop Pistol:** mint body, waffle-cone muzzle, pink pint-tub magazine.
- **Sundae Shotgun:** candy-cane stock.
- **Soft Serve Minigun:** six steel barrels and a mint pint hopper.

**Ingredients:**

| Item | Look |
|---|---|
| Mud Bucket | Dented pail |
| Iced Coffee | Carrier with "BEAN THERE" sleeves |
| Nut Sack | Burlap "NUTS" sack |
| Strawberry Basket | Basket |
| Gold Leaf | Velvet box with glowing sheets |

**Money:** Lunch Money, a crumpled green dollar `#7fe0a0` with coins.

---

## 7. FX language

### 7.1 Building blocks

**Particles** use a **128x128 greyscale atlas** with an 8x8 grid of 16 px cells.
- Rows: blob, star, dithered smoke puff, sprinkle, spark, teardrop, ring, shard.
- Each particle is tinted at runtime and picks a random frame from its row.
- Defaults:
  - Random rotation, world simulation space.
  - Size holds until 75% of life, then shrinks to 0. Smoke grows instead.
  - Stretched billboards for drops and sparks (velocity scale 0.06, length scale 1.5). Flat billboards for ground splats.
  - Blobs bounce off the world (dampen 0.7, bounce 0.15).

### 7.2 Bursts

`FxBurst.Play(color, scale)` tints the marked layers.

| Burst | Composition |
|---|---|
| Cream Burst (normal hit) | 5 glow sparkle stars; 16 tinted blobs (size .08-.2) that collide; 16 stretched tinted drops |
| Big Cream Burst | 30 rainbow sprinkles; 8 yellow glow stars; a spinning "Hit Star" model (0.25 s, overshoot 1.3, 500°/s, x0.9); 40 tinted blobs (.12-.3); 20 drops |
| Gas Burst (lactose fart) | 30 smoke puffs (size 1-2, growing 2.5x); 12 rising rings, tinted green |
| Dust Burst | 6 yellow glow stars; 14 dust puffs growing 2x |
| Leaf Burst (tree shake) | 40 leaf shards falling slowly over a 2.5 m radius |
| Crash Burst | 40 orange sparks (1, .5, .15); 25 glass shards (.7, .9, 1); 10 dark smoke puffs (.3, .27, .35) |
| Confetti Burst | 80 rainbow sprinkles in a 35° cone; 15 tinted glow stars |
| Sparkle Burst | 25 rainbow sprinkles; 18 tinted rising glow stars |

**Other emitters:**
- **Ground splats:** flat blobs of 0.3-0.7 m that last **30 s**, up to 800 at once.
- **Muzzle flash:** the "Pistol Muzzle Flash" model for 0.08 s.
- **Van:**
  - Exhaust: grey puffs (.55, .52, .6), rate 6 + 30·pace·throttle.
  - Hood smoke: (.32, .3, .38) once damage > 0.2.
  - Wheel dust: (.75, .62, .5) above 4 m/s.
- **Lactose:** a dad's cough cloud (.6, .85, .3). Gas cloud entities: 25-40 puffs/s of (.55, .8, .25).
- **Cash pickups:** spin 540°/s and bob `0.15 + sin(t·8)·0.05`.

### 7.3 Popups

World text in Press Start 2P that rises at 1.5 m/s and lives 1.3 s.
- Pop-in scale 0.2 → 1.5 → 1 over 0.27 s.
- Scaled by `max(1, distance / 6)` so it stays readable at 480x270.
- Alpha `2·(1 - age/life)`. Hidden beyond 60 m.

| Event | Text | Colour |
|---|---|---|
| Kid fed | "SPLORCH!", "OM NOM!", "FACE FULL!", "ENJOY!", "SHHLUP!" | Treat colour |
| Payment | "+$n" (2.5 s) | Gold |
| Favourite flavour | "FAVORITE! +$n" | Mint |
| Rich Kid refuses | "EWW! POOR PEOPLE / ICE CREAM!" | Pink |
| Cops called | "SUGAR ALERT! / MOM IS CALLING THE COPS" | Siren blue |
| Arrested | "BUSTED! -$n" | Siren blue |
| Parked badly | "PARKING TICKET! -$n" | Siren blue |
| Bribe | "HUSH MONEY +$n" | Gold |
| Fat Kid | "HUNGRYYYY!!", "NOM NOM NOM -n SCOOPS", "*BUUUURP*" (green) | Pink, green |
| Lactose Kid | "uh oh...", "*PFFFRRRT*" | Green |
| Jingle and horn | "DING DING DING! / ICE CREAM!", "HONK!" | Gold |
| Hits | "BONK!", "OOF!", "WHEEE!", "CLANG!", "CRASH!" | White |
| Hillside | "VAULT OPEN!" | Gold |
| Nut tree | "NUTS!" | Gold |

---

## 8. Camera and game feel

### 8.1 Camera (`DadsCamera.cs`)

- **Eye height:** 1.5 m.
- **Shake:** trauma²; max 6°, max 0.12 m; Perlin noise at `t·25`; trauma decays 1.4/s. A van impact holds trauma at ≥ 0.5.
- **Recoil:** decays at rate 12.
- **Shove lunge:** `sin(lunge·π)·0.25` m forward.
- **Tumble view** (knocked over or busted): third person at (0, 2.8, -4.2), looking 0.6 m above the body.

### 8.2 Viewmodel (`DadsViewModel.cs`)

- **Recoil:** 0.06 m and 7°; shotgun x2.2; random yaw ±2°.
- **Bob:** 0.018 m, phase speed·2.2, only at 0.5-7.5 m/s, x0.2 while aiming.
- **Sway:** 0.004 per degree, capped at 0.05.
- **Item switch dip:** -0.12 m, pitched 35°, rolled -20°.
- **Shove jab:** reaches to (-0.12, 0.12, 0.45).

### 8.3 World animation

| Object | Motion |
|---|---|
| Van body | Pitch `sin(t·40)·shake·4`, roll `sin(t·33)·shake·6` |
| Steering wheel | 3x the steer angle |
| Churn crank | 720°/s |
| Minigun barrels | 1500°/s |
| Street lamps | Knocked 85° away from the van at speed 5 |
| Trees | Wobble `sin(t·25)·6°` |
| Knocked-down dad | Spins 720°/s and lands flat |
| Fed kid | Hops `sin·0.35` |
| Walk cycle | Legs 28°, arms 14°, stride 1.1 (kids 0.75, Fat Kid 0.6) |

---

## 9. HUD and UI

### 9.1 Fonts

Both are OFL fonts, imported as hinted raster. All HUD text has a 1 px outline in (0.1, 0.06, 0.2).

| Font | Used for |
|---|---|
| **Press Start 2P** | Numbers and titles: money 22, ammo 26, debt 14, story card title 28, stamp 30 |
| **Pixelify Sans SemiBold** | Body text: day and time 18, prompt 20, coaching tip 20, phase banner 22, story card body 24, controls 17 |

**Text colours:**
- Yellow (1, .88, .29) for money and key names.
- Mint (.22, .95, .76) for coaching and ammo labels.
- Lavender (.71, .55, 1) for hints.
- Pink (1, .31, .64) for losses and empty states.
- Checklist: done `#38f2c3` with "+ ", current `#ffe14a` with "> ", to-do `#b8a8e8`.

### 9.2 Frames

All frames are nine-slice pixel sprites drawn at **2x** (pixels-per-unit multiplier 0.5).

- **Construction:** 32 px, cut corners, 2 px coloured rim, 1 px bevel (light top-left, dark bottom-right), INK fill at about 93% alpha.

| Sprite | Look | Border |
|---|---|---|
| `panel` | Pink rim | 8 |
| `panel_mint` | Mint rim | 8 |
| `panel_gold` | Gold rim, for Big Dairy items | 8 |
| `card` | Cream rim 3 px, with pink, mint, yellow and blue corner pixels | 8 |
| `slot` | Lavender rim, fill `#2a1f4f` | 8 |
| `slot_selected` | Pink 3 px rim, fill `#5a2a6e`, sprinkle pixels | 8 |
| `bar_back` | | 4 |
| `bar_fill` | Pink candy stripes, 64x12 | |
| `bar_fill_mint` | Mint candy stripes, 64x12 | |
| `banner` | 48x24 pink frosting band with drips and sprinkles | (4, 8, 4, 2) |

- **Glyphs** (16x16, ink outline): sun, moon, police badge, music note, milk carton, red X strike, crosshair, down-arrow marker.
- **Minigun reticle:** 32x32 mint ring with tick marks and a pink centre dot.
- **Item icons:** rendered from the models at 64x64. Orthographic three-quarter or side view, key sun `#fff4e2` and rim sun `#d8e6ff`, with a 1 px ink outline from alpha threshold and dilate.

### 9.3 Layout

Reference resolution 1280x720, 16 px margins.

| Element | Anchor, position | Size | Content |
|---|---|---|---|
| Money | Top left (16, -16) | 212x60 | `panel`, cash icon, yellow "$n". Punches 1.35x on change; turns pink on loss. |
| Day | Top left (16, -84) | 212x60 | Sun or moon icon, "DAY n" with the time in yellow |
| Heat | Top left (16, -152) | 212x46 | 5 police badges; inactive ones at 20% alpha |
| Debt | Top right (-16, -16) | 300x76 | `panel_gold`, carton icon, "OWED $950", mint progress bar 222x24 |
| Tonight | Top right (-16, -100) | 300x50 | `panel_gold`, "TODAY $0/$40" and 3 red strikes |
| Jingle | Top right (-16, -158) | 180x46 | `panel_mint`, note icon, "JINGLE ON" |
| Speed | Top right (-16, -212) | 180x46 | `panel_mint`, "n MPH" |
| Truck | Top right (-16, -266) | 180x46 | `panel`, "TRUCK" with a pink health bar |
| Phase banner | Top centre (0, -14) | 720x48 | Shown 5 s: "BIG DAIRY'S LOT", "DUSK  head back to the lot", "SUGAR CURFEW  cops are out" |
| Coaching line | Top centre (0, -70) | 720x60 | Mint text |
| Prompt | Centre (0, -44) | auto | `panel`, white text; key names in yellow |
| Crosshair | Centre | 32x32 | Swapped for the 64x64 reticle on the turret |
| Hotbar | Bottom centre, 4 slots at x = (i - 1.5)·82, y 16 | 74x74 | 62 px icon, 36 px flavour badge |
| Ammo | Bottom right (-16, 16) | 232x76 | `panel_mint`, big count, mint label (e.g. "HOPPER MUD") |
| Help hint | Bottom left | | Lavender "F1 controls   P debug" |
| Story card | Centre | 760x420 | Cream `card`, yellow title, white body, rubber-stamp text (PAID / FREE in mint, STRIKE in red) rotated 12° that slams in from 3x |

**Screen overlays:**
- **Screen splats:** up to 6 at 300 px, alpha 0.92. They slide down at 25 px/s and fade over 2.5 s.
- **Cough tint:** (.45, .8, .2, .35).
- **Brain-freeze tint:** (.7, .9, 1, .45).
- **Fade to black:** decays at 1.5.

### 9.4 Main menu

- **Camera:** clears to ink (0.11, 0.06, 0.2), with no low-res pass.
- **Title:** a `banner` at (0, 250), 900x48, with "BIG MILK STRIKES BACK" in Press Start 2P 28.
- **Buttons:** two `panel` buttons, 420x140: SINGLE PLAYER and MULTIPLAYER.
- **Button tints:** highlight (1, .75, .9), pressed (.8, .6, 1).

---

## 10. Notes for the production game

These are recommendations, not prototype facts.

**Keep:**
- The palette.
- Purple instead of grey.
- The 0.32 self-emission baseline.
- Point-sampled tiny textures.
- The low-res render with Bayer dither at 24 levels.
- Flat ambient driven by the day/night keys.
- Fog and clear colour matched to the sky.
- Candy FX with comic popups.
- The crisp HUD on top of the pixelated game.

**Tuning knobs that matter most:**

| Knob | Prototype value |
|---|---|
| Render resolution | 480x270 |
| Colour levels | 24 |
| Emission baseline | 0.32 |
| Fog | 45-170 m |
| Sky, sun and ambient keys | §2.2 |
| Sun intensity curve | §2.2 |

**Alternative pixel pass:** a distance-aware version was tried on the zombie demo. It renders at 1080p and pixelates in 4 px cells up close, 2 px from 18 m and 1 px from 45 m, so distant characters stay readable. It is in git history at commit `629dc3ba` (`PixelLook.shader`, `PixelLookFeature.cs`).

**Prototype shortcuts not to copy:**
- The ground is one flat green cube.
- Windows never light up at night (the lit ones are painted in).
- The van has no damage model beyond smoke.
- Several models (van, guns, road pieces) are reused from the zombie demo.
- The multiplayer menu is the unstyled Photon Quantum sample menu.
