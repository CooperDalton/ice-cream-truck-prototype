# PurrNet co-op netcode prototype: architecture report

Throwaway Unity 6000.3.12f1 project with PurrNet 1.25.0. It covers the multiplayer core of the heist game:

- one player drives a truck that never stops;
- the others walk around inside it, hop out and climb back in, and shoot ice cream;
- kids and cops ragdoll when hit by ice cream or the truck, then stand up again.

Testing used 30 automated soak runs of 90 s each, with 3 to 4 game instances (a host plus clients) driven by bots on this machine. A UDP proxy sat between each client and the host to add latency, jitter and packet loss. Every frame of every instance was logged and checked by `Loop/analyze.py` against the criteria in `Loop/STATE.md`.

## Results

"Baseline" means 60 ms one-way (120 ms round trip), ±10 ms jitter and 1% loss each way. "Bad" means 120 ms one-way, ±30 ms jitter and 3% loss.

| Check | Baseline (runs 22, 25, 28 on the final netcode) | Bad network (runs 26–30) |
| --- | --- | --- |
| Driver steering shows on the driver's screen | Same frame or next frame | Same frame or next frame |
| Truck snaps on any screen | ≤ 7 mm; ≤ 2.3 cm in the seat-handoff run | ≤ 2.6 cm (one bot-caused seat-flap run aside) |
| Passengers sliding inside the moving truck | ≤ 0.1 mm per frame | ≤ 0.1 mm per frame |
| Remote players snapping | None > 10 cm | 1–2 shoves of 0.15–0.18 m per run (truck corner hitting a runner) |
| Ice cream splat on observers vs shooter | 0.0 m (p95) | 0.0 m (p95) |
| Ragdoll pose agreement after the 0.4 s start merge | ≤ 6.4 cm (p95 0.1 mm) | ≤ 1.3 cm (p95 0.1 mm) |
| Stand-up spot, all machines | Identical; walking resumes within 7.5 mm | Identical; within 2.5 cm |
| Ragdoll pops > 25 cm caused by the network | None | 1–4 per run, 0.25–0.30 m |
| Bandwidth per client | 24–31 KB/s down, 3–7 KB/s up | Same |
| Exceptions | None | None |

The baseline network passes every criterion repeatedly. The bad network has the residuals listed under "Open issues".

## The decisions, and why

### 1. One timeline per machine, and events are points on it

Every remote thing a machine draws (truck, players, NPCs, shots, ragdolls) is sampled at one render time: `RenderTime = newest server time we could have − render delay`. This is the decision that makes everything else line up. If each object had its own interpolation buffer, as with one PurrNet `NetworkTransform` per object, the truck and the players standing in it would be drawn at slightly different moments, so passengers would slide around.

- **Clock.** Clients map server time using the fastest packet seen in a sliding window (`ClockMapper`), with at most 1% time-warp while adjusting. PurrNet's synced tick was not needed.
- **Owner-sent data** (player states, shots, hit reports, ragdoll frames) is stamped onto the server timeline by the host using one clock mapping per sender. Everything one player sends therefore shares one offset and stays in sync with itself.
- **Events are applied when the render time reaches their stamp, never on receipt.** This covers shots, shot hits, ragdoll start, ragdoll end and stand-up. Applying them on receipt was the cause of most of the "teleport" bugs.
- **The render delay adapts** (`GameManager.AdaptDelay`). It is the worst recent sample lateness plus one send interval. It grows fast (5% slow-motion) and shrinks slowly (1% fast-forward). It settled at 80–115 ms on the baseline network and 150–190 ms on the bad one. The fixed 110 ms delay starved 366 frames on the bad network; adaptive brought that to 24.

### 2. What PurrNet does, and what is custom

PurrNet handles:
- the UDP transport;
- connections and player IDs;
- `PlayerSpawner` and ownership;
- scene `NetworkBehaviour`s;
- RPCs, including `Channel.Unreliable`;
- the tick (set to 30 Hz).

Custom code handles snapshot buffers, the clock, prediction and the ragdoll stream. Reasons:
- **PurrNet's prediction system (PurrDiction) is not in the package.** It is a separate product. The core package has no rollback.
- **`NetworkTransform` and `NetworkBones` are not suitable here.** Each keeps its own buffer and timing, so neither can be lined up with the truck or with ragdoll start and end events.

For props that don't touch the truck, `NetworkTransform` is fine.

### 3. Truck: host-authoritative, predicted by the driver

- **Pure-math simulation.** The truck uses a kinematic bicycle model with box-vs-building collision (`TruckSim.Step`). It is a pure function with no PhysX, so the host and the driver run the identical code, and replaying inputs is cheap. The brakes don't work: speed is clamped between 3.5 and 12 m/s.
- **Driver input.** The driver sends inputs (sequence number, steer, throttle) 60 times a second, each packet repeating the last 6 inputs. The host consumes them through a 2-input buffer. The driver predicts with the same code and, on each acknowledged snapshot, replays its unacknowledged inputs.
- **Zero added steering latency.** The predicted truck is drawn as the last fixed step plus a partial step using the current input. Interpolating between the last two fixed steps added a frame of lag.
- **Corrections** go into one critically damped, velocity-preserving visual offset (`Vector3.SmoothDamp`). Exponential decay caused an 18 cm jolt at a seat handoff, and restarting an eased blend mid-way caused a 6 cm one.
- **Seat handoff.** Taking the wheel switches your view of the truck from the past (interpolated) to the present (predicted). The gap is the truck's speed times the time difference: about 1.4 m at 120 ms round trip, and 4.7–7.5 m at 240 ms round trip with jitter. The gap eases out over about a second. Two things also help:
  - The new driver's prediction starts from where the host's truck will be when its first input arrives (coast forward by one round trip plus the input buffer). Before that fix the first correction was about 1 m.
  - **Recommendation for the final game:** cover the switch with a sit-down or stand-up animation, and don't allow a seat switch more often than about once a second.
- **Run-overs are decided by the machine that sees the truck in the present:** the driver, or the host when the host drives or nobody does. Passengers see the hit about 33 ms of truck travel early (the driver is ahead of the host by its input buffer).

### 4. Passengers walk in a stationary copy of the truck

Players inside the truck are simulated with a CharacterController in a static copy of the interior placed at y = −200. Their position is synced in truck coordinates, and every machine draws them at its own drawn truck pose times that local position. Measured idle drift inside a turning, accelerating truck was at most 0.1 mm per frame on every screen. Do this in the final game: it is the single biggest smoothness win and costs almost nothing.

### 5. Players outside near the truck are synced relative to the truck

The owner places itself against the truck it sees. Observers draw the truck at a different moment, about (2 × one-way latency + render delay) × truck speed apart, which is around 1.6 m. A runner alongside the truck therefore appears metres off on other screens and snaps when climbing in. Outside players therefore send both a world position and a truck-relative position. Observers blend from truck-relative (within 3 m of the truck) to world (beyond 9 m).

This was designed from that analysis. The A/B run to measure it was not done, because the run budget ran out. The `-worldOutside` flag switches it off for that test.

Board and unboard transitions are held at the sample boundary and then eased over 0.25 s. Interpolating across them squeezed a 0.4–0.9 m step into one 33 ms send interval.

### 6. Players vs the truck body is custom, and soft

Unity's CharacterController against a moving kinematic collider popped players 20–25 cm in one frame. Players now ignore the truck collider. A custom push gives them the speed of the truck's surface at the contact point, and resolves any extra overlap over a few frames. What remains is real physics: a truck corner swinging round at about 9 m/s into a sprinting player moves them 15–18 cm in a frame. For the final game, consider knocking the player down instead of shoving them.

### 7. Shots are not networked objects

- **The shooter decides hits** against what it sees, and its copy appears the frame the button is pressed.
- **The path is analytic** (origin, velocity, gravity), so every machine can compute the shooter's exact path.
- **Observers** start their copy at the shooter's gun as drawn on their own screen, with their own drawn truck's velocity, then converge onto the shooter's true path within 0.3 s.
- **Static splats agree.** Every copy traces the true path against the static world, so wall and ground splats match on every machine.
- **NPC splats.** The shooter reports its hit point, and observers splat their copy there when the timeline reaches it.
- **Result:** observer splats landed within 0.0 m of the shooter's at p95. Early versions were up to 8.6 m off.
- **Sending:** shots and hit reports go out unreliable, twice (a tick apart), deduplicated by ID. Reliable-ordered sends drew shots up to 190 ms late, because one lost packet holds everything behind it until it is resent (head-of-line blocking).

### 8. Ragdolls: one machine simulates, everyone else replays

Cross-machine physics determinism isn't needed, and Unity PhysX can't provide it anyway: different hit timing gives different inputs. Instead:

1. **The hitter simulates.** The shooter, or the driver for a run-over, starts the ragdoll locally at once, from exactly the pose it was drawing, and sends a claim to the host. The host accepts the first claim; the first streamed frame also counts as a claim. A late claimer gets a rejection and blends into the winner's stream. Hits on someone else's ragdoll are forwarded to its owner as impulses.
2. **The owner streams frames at 30 Hz.** Each frame is the pelvis position plus each bone relative to the pelvis in half precision, and half-precision quaternions (PurrNet `HalfVector3` / `HalfQuaternion`). Each packet includes the previous frame, so one lost packet leaves no gap.
3. **The owner ends the ragdoll** when it settles (still for 0.4 s, or after 6 s). It sends one reliable message: final pose, stand-up spot and facing.
4. **Every machine plays the same stand-up** from that final pose to that spot, at the same timeline moment. The host's AI resumes walking from the same spot once the stand-up finishes. This is why the kid stands up in the same place on every screen.

The one unavoidable mismatch is at the start. The hitter saw the kid (2 × one-way + render delay) earlier than observers draw it: 0.3 m for a walking kid, about 1 m for a running cop. Observers know the ragdoll's start pose about one render delay before they draw it. They use that lookahead to ease the walking kid onto the start spot before the hit. Whatever is left merges into the tumbling ragdoll over 0.4 s, where it's invisible. The ease is fast for running cops (up to about 10 m/s for a few frames); the analyzer reports it separately as "pre-hit ease".

### 9. Ragdoll ownership races

Each of these was found by the soak runs and showed up as a kid teleporting on one or more screens. The final design numbers each ragdoll episode (an epoch from the host) and keeps a small per-NPC state machine on the timeline.

- **Old walking data.** The host sends no walking data while an NPC ragdolls. Falling back to walking samples later drew the kid where it was before its first hit, up to 21 m away. Worse, a shooter who hit that stale copy won the claim for everyone. Rule: never draw walking samples older than the render time; hold the pose instead.
- **Episodes overtaking each other.** Messages on different channels arrive in any order, so a new episode's first frame can arrive before the previous episode's end. Keep the previous episode's stream until the timeline has played through it, and still accept its late end.
- **A late frame reclaiming the NPC.** The old owner's last unreliable frame arrived after its own reliable end and counted as a new claim. The NPC was then "owned" by a machine that wasn't simulating it. The host now ignores frames older than that owner's end.
- **A superseded local stand-up.** The last owner was still standing the kid up locally when someone else hit it, and kept showing it standing for the whole new episode. A new episode now cancels the local stand-up.
- **A rejected claim between frames.** A claim rejected after that frame's display update started a blend with no target.

**Lesson for the final game:** model each NPC's network life as explicit episodes with IDs, keep the previous episode until played out, and treat every message as possibly late, duplicated or out of order.

### 10. Reliability by message type

| Message | Channel |
| --- | --- |
| Truck snapshots, NPC walking, player states, ragdoll frames, driver inputs | Unreliable. Inputs, player states and ragdoll frames repeat earlier data in each packet. |
| Shots, shot hits | Unreliable, sent twice, deduplicated |
| Ragdoll claims, forwarded impulses | Reliable, unordered |
| Ragdoll end, driver changed | Reliable |

Use reliable-ordered only where order really matters. Every reliable-ordered timeline message tested here showed up late after packet loss.

### 11. Bandwidth

24–31 KB/s down and 3–7 KB/s up per client (measured at the proxy), with 4 players, 20 NPCs and several ragdolls active. That is well within budget for Steam peer-to-peer. By message size (estimated, not measured separately), the truck is about 2 KB/s and NPC walking about 13 KB/s for 20 NPCs at 30 Hz with full floats, the biggest steady cost and the place to compress first.

## PurrNet gotchas hit along the way

- **Start the network in `Start`, not `Awake`.** `UDPTransport` sets itself up in its own `Awake`; calling `StartHost` from another `Awake` threw a NullReferenceException.
- **The host's own client receives `ObserversRpc`s.** They arrive through local delivery with `isServer == true`. Guard handlers with `if (isServer) return;` when the server already applied the data, or it applies twice.
- **`PlayerSpawner` spawns first and gives ownership afterwards.** In `OnSpawned`, `owner` is null on the server. Set up in `OnOwnerChanged`, and cache the owner ID: `owner.Value` was briefly null during an ownership callback and threw.
- **Avoid `ReliableOrdered` for anything time-critical** (head-of-line blocking). `ReliableUnordered` and `Unreliable` with redundancy behaved well.
- **Defaults to change:**
  - A `NetworkRules` asset is mandatory; `ServerOwner.asset` worked.
  - Turn off the auto-start flags when starting from code.
  - The `NetworkPrefabs` asset only fills itself from a folder in the editor.
  - Don't put "Editor" in a runtime assembly name, or PurrNet's code generation skips it.
- **`Instantiate` and `Destroy` are rewritten by PurrNet** to network spawn and despawn. Local-only prefabs (projectiles) still work.

## Open issues (not resolved, with the next step)

1. **Bad network, ragdoll pops.** 1–4 per 90 s run of 0.25–0.30 m. Hypothesis: three consecutive lost packets, or a burst later than the adaptive delay, then extrapolation and correction. Next step: log the stream gap at each pop. Possibly add a third redundant frame, or extrapolate with gravity instead of linearly.
2. **Bad network, truck-corner shoves.** 0.15–0.18 m. This is gameplay physics, not sync. It is a design choice (knock down vs shove).
3. **Splat outlier.** One shot in 105 splatted 2 m off on observers (both hit reports lost or late).
4. **Not tested:**
   - the truck-relative outside-player A/B (`-worldOutside`);
   - soaks longer than 90 s;
   - more than 4 players;
   - Steam transport and real internet (bursty loss, clock drift between PCs: here all instances shared one machine's clock);
   - host migration;
   - skinned characters and animation;
   - CPU cost of many client-side ragdolls.
5. **Driver's view.** While predicting, the driver sees the truck about (render delay + one-way) ahead of the kids it is approaching. Run-over decisions favour the driver; passengers see the hit about 33 ms of travel early.

## Run it

```bash
cd "PurrNet Truck Demo"
Loop/build.sh                                   # batch: build scene + Linux player into Build/
python3 Loop/run_soak.py --out Library/CodexPlaytests/purrnet/myrun \
  --host-bot rammer --client-bots gunner,gunner,runner --duration 90 --seed 1 --capture c1
python3 Loop/analyze.py Library/CodexPlaytests/purrnet/myrun
```

- **Bot roles:** `driver`, `rammer`, `gunner`, `runner`.
- **Seat handoff:** add `--extra "-leaveAt 45 -driveAt 50"`.
- **Bad network:** add `--latency 120 --jitter 30 --loss 0.03`.
- **Playing by hand:** start `Build/TruckDemo.x86_64` without arguments for the Host/Join menu.
  - Controls: WASD to move or steer, mouse to look, left mouse to shoot, E to take the seat, Shift to sprint.
  - You board by running into the open back of the truck and get off by walking out of it.

Run history, every failure and every analyzer change: `Loop/STATE.md`. Visual review: `Library/CodexPlaytests/purrnet/run28_gunner_view.gif` and `run25_runner_view.gif`.
