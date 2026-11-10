## Project context

This is the Divorced Dads ice cream truck game (player-facing name "Big Milk Strikes Back") for a game development class. The Unity project is in `Zombie Ice Cream Truck/` (the folder keeps the name of the zombie demo it grew out of). Agents should implement as much of the requested work as possible, including creating and moving scripts, scene objects, prefabs, folders, and assets as needed. Keep Unity references intact when moving assets by using the editor or preserving their existing `.meta` files.

The earlier tycoon prototype (`Ice Cream Truck Prototype/`, with the master `IceCreamTruckWorkshop.blend`) and the zombie mode were removed; both are in git history (the last commit with them is `a09e0723`). Blender models are built by the Python scripts in `Art/Tools/zombie-styles/`, not kept in a .blend. The visual style reference is `docs/visual-reference/README.md`.

## Code Style Preferences

- Do not add unnecessary null checks. If something should exist, assume it exists and let the game crash so the root issue is obvious.
- Always look for the root cause of bugs. Do not add defensive checks that hide the real problem.
- Prefer explicit singleton setup inside each manager script. Do not create a generic reusable `Singleton<T>` base class.
- Never use `GameObject.Find`, `GameObject.FindWithTag`, `FindObject(s)OfType`, `FindFirstObjectByType`, `FindAnyObjectByType`, `Resources.FindObjectsOfTypeAll`, `Transform.Find`, or similar implicit name/type-based object discovery. Wire dependencies through serialized references or explicit manager-owned references instead.
- Use `EventHandler` / `EventHandler<TEventArgs>` for events. Do not use `Action` for game events.
- ScriptableObject script and class names must end with `SO`.
- Put ScriptableObject scripts in `Assets/Scripts/Scriptable Objects`.
- Put manager scripts in `Assets/Scripts/Managers`.
- Keep most other scripts directly in `Assets/Scripts` unless there is a strong reason for another folder.
- Do not split `EventArgs` classes into separate files. Define event args in the same script as the class immediately above where the eventHandler is defined.
- Define small, owner-specific enums in the same script that owns the concept. For example, define `GamePhase` in `GameManager.cs`.
- Interface script names must start with `I`.
- Do not construct visual UI hierarchies or add visual/layout components at runtime. Author UI layout and styling in scenes or prefabs through the Unity Editor so it remains manually editable. Runtime code may instantiate those prefabs and populate their data or state, but it must use serialized references instead of creating the visual structure in code.
- Do not care about save version migration edge cases. The game is in such early development that it does not matter and all saves will be wiped anyway.
- Don't create functions that are just 1 line.
- Let the Unity Editor generate `.meta` files for new assets. Preserve existing `.meta` files when moving assets.

## Unity CLI

- Unity is driven through the official `unity` CLI (Homebrew cask `unity-cli`) talking to the `com.unity.pipeline` package installed in this project. There is no MCP server to start: run `unity` directly from the shell.
- Run every `unity` command from `Zombie Ice Cream Truck/` or pass `--project-path "<repo>/Zombie Ice Cream Truck"`. Add `--json` when you need to parse output. Set `UNITY_NON_INTERACTIVE=1 UNITY_NO_BANNER=1` in scripted use.
- Start every Unity task with `unity status`. If no editor is listed, launch it with `unity open "<repo>/Zombie Ice Cream Truck"` and poll `unity status` until the state is ready. If `unity pipeline list` shows the editor running but `Server Reachable` false, the editor is probably still importing or in Safe Mode because of compile errors; read `unity command get_console_logs --severity error` once it answers, or fix the compile errors on disk first.
- Then `unity command set_autotick --enable true` so the editor keeps compiling, importing, and ticking while unfocused. This also means the editor now imports new files and creates `.meta` files when an agent triggers a refresh, not only when the user is tabbed in.
- Discovery: `unity command` lists everything the editor exposes (`--query <term>` filters, `--tag game` shows this project's commands). `unity command <name>` runs one, args are `--name value`, JSON objects are passed as a JSON string.
- Core loop after editing scripts: `unity command recompile`, then poll `unity command recompile_status` until it reports completed or up_to_date (connection errors during the domain reload are expected), then `unity command get_console_logs --severity error`. Never continue past a failed compile.
- Tests: `unity command list_tests --mode editor`, then `unity command run_tests --mode editor --filter <ClassOrTest>` (long runs: `--async_tests true` and poll `test_status`). `unity test --mode EditMode` is the batch-mode alternative that spawns its own editor and only works when no editor has the project open.
- One-off inspection: `unity command eval 'return <expression>;'` runs C# on the editor main thread with no recompile; `unity command eval_file <path.cs>` for longer snippets. Use it for reading state and quick experiments, never as a substitute for committed code changes.
- Play Mode: `unity command editor_play`, `editor_pause`, `editor_stop`, `editor_status`, `screenshot --view game --output <path>`.

### Sharing Unity between agents

- Unity is a shared resource across Codex and Claude threads. Concurrent read-only use is fine: `unity status`, `editor_status`, `get_console_logs`, `list_tests`, `eval` that only reads state.
- Exclusive operations must be serialized: launching Unity, recompiling, importing, running tests, entering Play Mode, and commands that change game state. Before doing one, atomically acquire the repository-local `.codex/unity-mcp.lock` directory by first ensuring `.codex/` exists, then running `mkdir "<repo>/.codex/unity-mcp.lock"` (ownership only if `mkdir` succeeds; never check-then-create) and write `owner.txt` inside it with the task/thread identifier and the UTC acquisition time. When unsure whether an operation mutates Unity or game state, treat it as exclusive.
- If the lock already exists, continue safe read-only inspection but do not perform exclusive operations. Report that another task is using Unity, then wait and retry with light polling, doing useful non-Unity work meanwhile. Refresh the `owner.txt` timestamp at least every five minutes while holding the lock and release it in a `finally`-style cleanup as soon as Unity work is finished, including after failures. Never remove a lock held by another active task; a lock with no refresh for 30 minutes may be treated as abandoned and replaced after reporting that recovery.

### When to test in-game

- Inspect the test inventory before invoking PlayMode tests. Do not run an empty PlayMode suite, since Unity still starts the game scene.
- For small fixes, routine refactors, and text/data tuning, use focused non-game checks unless the user asks for in-game testing.
- Run in-game testing when the user asks or when implementing a large, first-time gameplay/UI feature whose behavior requires it. Use the smallest relevant test flow.
- Discover available commands with `unity command`. Idler's `game_*` commands and `Tools/game-cmd.py` wrapper are not part of this project.
- Save Game-view screenshots under `Library/CodexPlaytests/`.
- Never claim a gameplay flow was tested without reporting the observed input, before/after state or screenshots, and console result.

## Quantum project

- `Zombie Ice Cream Truck/`: Unity 6000.3.12f1, Photon Quantum 3.0.14, URP, Input System only. Scene `Assets/QuantumUser/Scenes/DivorcedDads.unity`. Divorced dads run an ice cream truck to pay off Big Dairy: scavenge ingredients, churn flavor tubs, feed kids at the serving window, get home before the sugar curfew's cops.
- Simulation: `Assets/QuantumUser/Simulation/DivorcedDads/` (`DivorcedDads.qtn`, systems, `DadsSettings`). It follows Quantum's rules instead of the Unity rules above: systems are stateless, all game state is declared in `.qtn` files, math uses `FP`/`FPVector3`, no `UnityEngine` types, events are Quantum DSL `event`s and signals (not `EventHandler`), and tunable data lives in Quantum `AssetObject` classes (no `SO` suffix) next to the systems.
- View, HUD, effects and audio: `Assets/Scripts/DivorcedDads/` (plus the shared `FxBurst`, `FxExpand`, `WalkCycle` and `GameMenu` in `Assets/Scripts`). View code subscribes with `QuantumCallback.Subscribe` / `QuantumEvent.Subscribe`; it never changes game state.
- After editing a `.qtn` file, run `Zombie Ice Cream Truck/Tools/codegen.sh`: it parks user C# outside `Assets` while Quantum codegen runs (C# that references not-yet-generated types would otherwise block the batch run) and restores it. Never park files in the project's `Temp/` folder; Unity deletes it.
- `DivorcedDadsSceneBuilder.Build` (Tools > Divorced Dads > Build Scene) regenerates the prefabs in `Assets/Prefabs/Dads`, `DadsSettings.asset`, the town (block placement, baked static colliders, planned kid paths out of the fenced yards) and the scene, plus its online-menu scene info. Change values there, not in the generated assets. `Tools > Reimport PS1 Art` reapplies `PS1ArtPostprocessor` rules.
- Tutorial: a run starts on moving day (`DayPhase.Tutorial`) in the walled-off Moving Day yard south of town (`h_dads_town.py` `moving_day`, placed by `BuildYard`). `DayCycleSystem.Lessons` ticks off the `Lesson` steps from the world state, the dads' kid walks over for the serve lesson, and taking the wheel at any point (`DadsGame.FinishTutorial`) moves the truck, with whatever was churned, to Big Dairy's lot for Day 1. `DadsSettings.Tutorial` turns it off; `TutorialMemory` saves `DivorcedDads.TutorialPlayed` in PlayerPrefs once it ends and sets `RuntimeConfig.SkipTutorial` for later local games (games started from the online menu always play it). The HUD's checklist, coaching line and arrow are in `DadsHud.Coach`.
- Debug menu: P in game lists cheats on keys 1-9 (money, today's sales, full freezer, every upgrade, minigun hopper, repair, skip ahead, clear strikes, truck to the lot). `DadsDebugMenu` sends a `DadsCheat` command; `DadsCheatSystem` applies it.
- Play-test bot: `DadsPlaytest.Run("<scenario>")` from an open editor (eval), or `-executeMethod DadsPlaytest.RunFromCommandLine` with `PLAYTEST_SCENARIO`. Scenarios: `tutorial`, `ladder`, `lamps`, `flats`, `turret`, `debug`, `tour`, `serve`, `shop`, `night`, `maple`, `chaos`, `ride`, `finale`, `cops` (all but `tutorial` skip the tutorial), plus the `pitch_*` pitch-deck shots described at the top of `DadsPlaytest.cs`. It mutes audio, writes snaps, frame sequences and a state log to `Library/CodexPlaytests/dads/`.
- On this Linux machine, headless `unity run` needs `DISPLAY=:0` (and `WAYLAND_DISPLAY=wayland-1`).

## Art, HUD and sound

- Models: `Art/Tools/zombie-styles/style_H.py` is the PS1 style library (palette, pixel canvases, low-poly builders). `h_dads_characters.py`, `h_dads_items.py` and `h_dads_town.py` build the game's own models; the van, the guns, the street lamp and road pieces and two FX models come from the shared libraries `h_truck.py`, `h_weapons.py`, `h_items.py`, `h_road.py`, `h_stops.py` and `h_fx.py`. `export_unity.py` exports them to `Assets/Art/PS1/<Category>/` (its `SHARED` list picks the few assets used from the shared libraries) and writes `manifest.json` with every socket in Unity coordinates. `Assets/Art/PS1/Vehicles` (police car, harbor, yacht, lighthouse) holds pitch-deck props with no source script in the repo.
- HUD: `hud_sprites_dads.py` (python3) draws the nine-slice frames and glyphs into `Assets/Art/Sprites/DadsHUD`, `hud_icons_dads.py` (Blender) renders the item icons into `Assets/Art/Sprites/DadsIcons`, and the HUD uses the OFL pixel fonts in `Assets/Art/Fonts` (Press Start 2P, Pixelify Sans). `DivorcedDadsSceneBuilder.BuildHud` lays it out and sets the nine-slice borders.
- Generated assets: `fx_sprites.py` writes the particle atlas and screen splats to `Assets/Art/Sprites`; `sfx_synth.py` writes the shared sounds and the music-box jingle to `Assets/Audio` and `sfx_dads.py` the rest to `Assets/Audio/Dads` (both need numpy: `uv run --with numpy python <script>`; append new sounds to `sfx_synth.py` at the end of its list so the shared random generator leaves the existing ones unchanged). Rerun them instead of editing the outputs by hand.

## Main menu and builds

- `Assets/Scenes/MainMenu.unity` is the first scene of a build: single player (the game scene's local runner starts the game) or multiplayer (the Quantum sample menu, with the game preselected through its `Photon.Menu.SceneName` PlayerPref). `GameMenuBuilder.Build` (Tools > Build Main Menu) regenerates it and keeps it first in the build settings.
- Player builds: `PlayerBuilds.Windows` / `PlayerBuilds.Mac` (Tools > Build Players) build every enabled build scene; batch mode: `unity run "<project>" -- -executeMethod PlayerBuilds.Windows -buildOutput <folder> -logFile <log>` with the editor closed. The itch.io page is `wizdro/ice-cream-truck-simulator-prototpye` (channels `windows`, `mac`); push with `butler push <folder> wizdro/ice-cream-truck-simulator-prototpye:<channel> --userversion <version>` after moving the `*_BurstDebugInformation_DoNotShip` folders out.

## Agents.md

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
