# Art style review

Round two adds an ice cream stand, open waffle iron, two-scoop serving bowl, and scooper in both Soft and Cel. [Open the new comparison](Previews/ArtStyleRound2/SoftVsCel_Props.png). The master workshop contains the eight models in `M - Soft and Cel shop props`. Scene `Art style review 2` has enlarged display instances, with Soft on the left and Cel on the right. Original model dimensions are unchanged by display magnification.

The live Blender session was backed up before appending these additions. The append check preserved all 786 existing objects' mesh geometry, transforms, parents, and material assignments. These remain Blender art studies; the gameplay FBX and Unity shaders have not been replaced. The new waffle iron has a separate lid hinge, but it has no gameplay behavior yet.

Open [the comparison sheet](Previews/ArtStyleReview/ArtStyleComparison.png) to compare the current cottage, maple tree, and strawberry tub with nine new 3D variants.

| Direction | Changes |
| --- | --- |
| A. Soft toy town | Curved roof, thick rounded trim, smooth clustered foliage, cream enamel tub, rippled ice cream. |
| B. Cel cartoon | Angular roof, three shading bands, thin plum outlines, simpler highlights. |
| C. Painted storybook | Leaning roof, irregular foliage, broad procedural color variation, matte materials. |

The user selected B, Cel cartoon, after round two. The resulting [toon model kit](TOON_MODEL_KIT.md) contains 91 models and variants. C remains a subtle material and shape study; it does not contain hand-painted textures.

All studies are in `Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend`, under `L - Art style alternatives`. Columns run from the original through A, B, and C. The rows contain cottages, trees, and tubs. The `Art style review` scene isolates this collection. Select a model and use Frame Selected to inspect it at its actual scale.

The PNGs are Blender EEVEE renders with matching framing and studio lighting for each asset. Cel materials use a fixed light direction to test the bands and outline shells. These materials are not Unity shaders, and this pass does not change the game's meshes, lighting, or post-processing. A chosen direction still needs a Unity material and lighting pass at gameplay distances.

The meshes are art studies, not optimized replacements. The soft cottage currently has about 8,000 triangles, compared with 2,884 in the existing cottage. Cel outlines add geometry. Optimize the selected version before replacing repeated game assets.

`Previews/ArtStyleReview/audit.json` records the rendered variants and mesh counts. The build compared all 527 original objects' transforms, parents, mesh vertices, face indices, and material assignments before and after the additions. They matched. The original workshop backup is `Source/BeforeArtStyleReview_20260910.blend`. The separate live Blender window was left on its unsaved scene.

`Source/verify_art_style_review.py` also reopened the saved master and confirmed those 527 objects, 12 comparison collections, and nine new variants. Unity completed the source-file import and returned to ready state. The refresh took 5.17 seconds and exceeded the command bridge's five-second limit, which logged a bridge timeout. The import log also reported self-intersecting polygons in existing truck body and door meshes. Those original meshes were unchanged, and the gameplay FBX was not replaced.

Steam Blender is installed here and works from PowerShell:

```powershell
& 'C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe' --version
```

`Source/build_art_style_review.py` builds a candidate from the original backup and renders the studies. It writes to `Art/Source/ArtStyleReview_Candidate.blend`, so re-running it does not overwrite the master. `Source/compose_art_style_review.py` assembles the comparison sheet using Pillow. Preserve later workshop edits before transferring a rebuilt candidate into the master.
