# Round character models

The current characters are in collections `C • Characters` and `D • First-person hands` in `Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend`, relative to the repository root. `Art/Exports/Characters.glb` contains the same models and rigs.

The lineup has a crew player, two adult appearances, two child appearances, and a first-person mitten pair. They have large round heads, simple eyes, bean-shaped bodies, and floating four-digit hands. There are no human arms, legs, shoes, or individual finger joints.

Each character is one skinned mesh. The adult appearances share mesh data, as do the child appearances. Named material slots control skin, clothing, hat or hair, and accents. The variant objects override those slots, so changing their palettes does not require another mesh. Eye, pupil, and nose materials are shared.

Character rigs have five bones: `Root`, `Body`, `Head`, `Hand_L`, and `Hand_R`. The first-person rig has a root and two hand bones. Use Pose Mode to turn the head, tilt the body, or gesture with either hand. These are generic rigs without animation clips or a Unity Humanoid Avatar.

`Art/Previews/Characters_04_Round_Lineup.png` shows the current set. Earlier numbered character previews show the superseded human-style pass. The old models remain in the revision backups under `Art/Source`.

Verification checks normalized weights on every vertex, shared customer meshes, all six GLB skins, and a hand-bone rotation that moves the weighted mesh. `Art/MODEL_BUDGET.md` records source and exported geometry counts.

`Art/Source/build_round_characters.py` builds the current characters. `revise_workshop.py` calls it while assembling the master. Preserve manual edits before rebuilding; the older `build_characters.py` creates the superseded models.

## Easy-mode player hands

The crew player and first-person pair use floating hands with no arms or reach constraints. Their `Hand_L` and `Hand_R` bones are unconnected children of `Root`, so turning or tilting `Body` does not pull the hands. Move and rotate each hand control independently. `Crew_Grip_L_SOCKET`, `Crew_Grip_R_SOCKET`, and the equivalent `FirstPerson_Grip_*_SOCKET` anchors follow their respective palms for attaching held props.

Verified that translating each hand moves only its weighted vertices and its grip anchor. Tilting the crew body leaves both hands in place. The saved pose is unchanged. This is the easy-mode model setup; grabbing, scooping, and mode selection have not been implemented in gameplay.
