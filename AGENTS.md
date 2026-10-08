## Project context

This is an ice cream truck simulator prototype for a game development class. The Unity project is in `Ice Cream Truck Prototype/`. Agents should implement as much of the requested prototype work as possible, including creating and moving scripts, scene objects, prefabs, folders, and assets as needed. Keep Unity references intact when moving assets by using the editor or preserving their existing `.meta` files.

All Blender models belong in the master scene at `Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend`. Keep new assets in that scene, organized into collections and arranged side by side for review. Preserve unsaved user edits before updating the file.

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
- Run every `unity` command from `Ice Cream Truck Prototype/` or pass `--project-path "/Users/cooperdalton/Ice Cream Truck Prototype/Ice Cream Truck Prototype"`. Add `--json` when you need to parse output. Set `UNITY_NON_INTERACTIVE=1 UNITY_NO_BANNER=1` in scripted use.
- Start every Unity task with `unity status`. If no editor is listed, launch it with `unity open "/Users/cooperdalton/Ice Cream Truck Prototype/Ice Cream Truck Prototype"` and poll `unity status` until the state is ready. If `unity pipeline list` shows the editor running but `Server Reachable` false, the editor is probably still importing or in Safe Mode because of compile errors; read `unity command get_console_logs --severity error` once it answers, or fix the compile errors on disk first.
- Then `unity command set_autotick --enable true` so the editor keeps compiling, importing, and ticking while unfocused. This also means the editor now imports new files and creates `.meta` files when an agent triggers a refresh, not only when the user is tabbed in.
- Discovery: `unity command` lists everything the editor exposes (`--query <term>` filters, `--tag game` shows this project's commands). `unity command <name>` runs one, args are `--name value`, JSON objects are passed as a JSON string.
- Core loop after editing scripts: `unity command recompile`, then poll `unity command recompile_status` until it reports completed or up_to_date (connection errors during the domain reload are expected), then `unity command get_console_logs --severity error`. Never continue past a failed compile.
- Tests: `unity command list_tests --mode editor`, then `unity command run_tests --mode editor --filter <ClassOrTest>` (long runs: `--async_tests true` and poll `test_status`). `unity test --mode EditMode` is the batch-mode alternative that spawns its own editor and only works when no editor has the project open.
- One-off inspection: `unity command eval 'return <expression>;'` runs C# on the editor main thread with no recompile; `unity command eval_file <path.cs>` for longer snippets. Use it for reading state and quick experiments, never as a substitute for committed code changes.
- Play Mode: `unity command editor_play`, `editor_pause`, `editor_stop`, `editor_status`, `screenshot --view game --output <path>`.

### Sharing Unity between agents

- Unity is a shared resource across Codex and Claude threads. Concurrent read-only use is fine: `unity status`, `editor_status`, `get_console_logs`, `list_tests`, `eval` that only reads state.
- Exclusive operations must be serialized: launching Unity, recompiling, importing, running tests, entering Play Mode, and commands that change game state. Before doing one, atomically acquire the repository-local `.codex/unity-mcp.lock` directory by first ensuring `.codex/` exists, then running `mkdir "/Users/cooperdalton/Ice Cream Truck Prototype/.codex/unity-mcp.lock"` (ownership only if `mkdir` succeeds; never check-then-create) and write `owner.txt` inside it with the task/thread identifier and the UTC acquisition time. When unsure whether an operation mutates Unity or game state, treat it as exclusive.
- If the lock already exists, continue safe read-only inspection but do not perform exclusive operations. Report that another task is using Unity, then wait and retry with light polling, doing useful non-Unity work meanwhile. Refresh the `owner.txt` timestamp at least every five minutes while holding the lock and release it in a `finally`-style cleanup as soon as Unity work is finished, including after failures. Never remove a lock held by another active task; a lock with no refresh for 30 minutes may be treated as abandoned and replaced after reporting that recovery.

### When to test in-game

- Inspect the test inventory before invoking PlayMode tests. Do not run an empty PlayMode suite, since Unity still starts the game scene.
- For small fixes, routine refactors, and text/data tuning, use focused non-game checks unless the user asks for in-game testing.
- Run in-game testing when the user asks or when implementing a large, first-time gameplay/UI feature whose behavior requires it. Use the smallest relevant test flow.
- Discover available commands with `unity command`. Idler's `game_*` commands and `Tools/game-cmd.py` wrapper are not part of this project.
- Save Game-view screenshots under `Library/CodexPlaytests/`.
- Never claim a gameplay flow was tested without reporting the observed input, before/after state or screenshots, and console result.

## Zombie Ice Cream Truck (Quantum) project

- The multiplayer zombie demo is a separate Unity project in `Zombie Ice Cream Truck/` (Unity 6000.3.12f1, Photon Quantum 3.0.14, URP, Input System only). The tycoon prototype stays in `Ice Cream Truck Prototype/`.
- Simulation code lives in `Assets/QuantumUser/Simulation/ZombieTruck/` and follows Quantum's rules instead of the Unity rules above: systems are stateless, all game state is declared in `.qtn` files, math uses `FP`/`FPVector3`, no `UnityEngine` types, events are Quantum DSL `event`s and signals (not `EventHandler`), and tunable data lives in Quantum `AssetObject` classes (no `SO` suffix) next to the systems.
- Unity-side (view) code stays in `Assets/Scripts` and subscribes with `QuantumCallback.Subscribe` / `QuantumEvent.Subscribe`; it never changes game state.
- After editing a `.qtn` file, run `Zombie Ice Cream Truck/Tools/codegen.sh`: it parks user C# outside `Assets` while Quantum codegen runs (C# that references not-yet-generated types would otherwise block the batch run) and restores it. Never park files in the project's `Temp/` folder; Unity deletes it.
- `ZombieTruckSceneBuilder.Build` (Tools > Zombie Truck > Build Prototype Scene) regenerates every entity and effect prefab from the PS1 art in `Assets/Art/PS1`, plus `ZombieTruckSettings`, `SurvivorController`, the gameplay scene, the HUD and the online menu setup; change values there, not by hand in the generated assets. `Tools > Zombie Truck > Reimport PS1 Art` reapplies `PS1ArtPostprocessor` rules. The art itself is exported by `Art/Tools/zombie-styles/export_unity.py` (with `manifest.json` listing every socket in Unity coordinates).
- Headless play-test: `Unity -batchmode -projectPath "<project>" -executeMethod Playtest.Run -logFile <log>` (no `-quit`). `PLAYTEST_SCENARIO` picks the flow: `drive` (default), `kitchen` (ammo loop), `showcase` (two local players, roof shooting, auto-driven run-overs, a crash), `depot` (auto-drives area 1 to the depot, buys an upgrade, rolls out), `cab` (seat and cab walking). It drives the game through virtual input devices and writes full-frame captures (game plus HUD), recorded frame sequences under `frames/` (turn into GIFs with ffmpeg) and a state log to `Library/CodexPlaytests/`.
- `FxGallery.Capture` (Tools > Zombie Truck > Capture FX Gallery) renders every effect prefab at three moments into `Library/CodexPlaytests/fx_gallery.png`; the builder also writes top-down chunk collider maps to `Library/CodexPlaytests/colliders/`.
- Generated assets: `Art/Tools/zombie-styles/fx_sprites.py` writes the particle atlas and HUD sprites to `Assets/Art/Sprites`, and `Art/Tools/zombie-styles/sfx_synth.py` synthesizes every sound and the music-box jingle to `Assets/Audio`. Rerun them instead of editing the outputs by hand.
- On this Linux machine, headless `unity run` needs `DISPLAY=:0` (and `WAYLAND_DISPLAY=wayland-1`). PS1 art source scripts for the demo are in `Art/Tools/zombie-styles/`.

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
