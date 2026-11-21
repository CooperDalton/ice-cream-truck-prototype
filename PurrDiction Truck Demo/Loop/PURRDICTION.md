# PurrDiction variant: results

This project is a copy of `PurrNet Truck Demo` with the truck and player movement moved onto PurrDiction v1.4.1. It uses PurrNet 1.25.0, pinned to the same commit as the original. Shots, ragdolls and NPCs are unchanged custom code. `Loop/REPORT.md` and `Loop/STATE.md` describe the original custom version.

## What changed

- **Network tick.** It is now 60 Hz, because PurrDiction simulates at the network tick rate. NPC and ragdoll streams stay at 30 Hz. PurrDiction sends server frames at 30 Hz (`_serverUpdateRate`).
- **No physics provider.** Ragdolls are local Unity physics, which is never rolled back, so Unity keeps stepping physics itself.
- **Truck (`Truck.cs`).**
  - The truck is a scene `PredictedIdentity<TruckInput, TruckState>` with `FullPrediction`. Every client predicts it and extrapolates the driver's last input for up to about 0.7 s (`_repeatInputFactor` 4), so players near it collide with the present truck.
  - The driver owns it. The seat is taken and left inside the player simulation with `PredictionManager.SetOwnership`, so the hand-off is predicted and rolled back like any other state.
  - What each screen draws is custom:
    - Passengers draw the host-confirmed states at RenderTime, which is the shared timeline with players, NPCs and shots.
    - The driver draws its newest prediction at `localTick - 1 + tickModule.floatingPoint`.
    - Switching seats moves the drawn moment between the two by running the drawn truck at most 15% faster or slower than real time. Nothing jumps.
  - Replays that move the drawn truck are eased out (`onStartingToRollback` / `onRollbackFinished`).
- **Players (`PlayerAvatar.cs`).**
  - Each player is a `PredictedIdentity<PlayerInput, PlayerSimState>` with `PredictedIfOwned`. Movement is now decided by the host and predicted by the owner. The original was owner-authoritative.
  - The interior pocket and the truck-relative sync are unchanged.
  - Remote players are drawn from confirmed states at RenderTime.
  - The owner draws its own prediction like the driver does, and eases out corrections. Truck-relative and world corrections are handled separately.
- **Shots (`ShotRelay.cs`).** Shot and hit-point RPCs moved to one scene `NetworkBehaviour`, because `PredictedIdentity` can't carry PurrNet RPCs.

## Results (seat hand-off scenario: client drives, leaves the seat at 45 s, another client takes it at 50 s)

| | Original custom netcode | PurrDiction variant |
| --- | --- | --- |
| Truck snaps, any screen, normal network | ≤ 2.3 cm | ≤ 1.8 cm (runs p03 to p06) |
| Truck snaps, bad network | ≤ 2.6 cm | ≤ 1.8 cm (p07) |
| Seat switch, normal network | 1.4 m slide, eased over about 1 s | No jump. The views are 0.26–0.31 s apart (1.4–2.2 m), caught up in 1.6–2.0 s at ±15% speed |
| Seat switch, bad network | 4.7–7.5 m slide | No jump. The views are 0.41–0.44 s apart (2.3–3.1 m), caught up in 2.8–3.0 s |
| Driver steering response | 0–1 frames | 1–2 frames (input is read once per 60 Hz tick) |
| Own movement response | Same frame | About 1 tick (17 ms) later |
| Own player corrections | None (owner-authoritative) | 6–12 cm at join and right after leaving the seat; 10–45 cm for a runner beside the truck when the driver steers. All eased over 0.2 s |
| Remote player snaps > 10 cm | None (normal network) | None (p06, p07) |
| Splats (observer vs shooter) | 0.0 m p95 | 0.0 m p95 |
| Ragdoll agreement and stand-up | Identical | Identical (unchanged code) |
| Bandwidth per client | 24–31 KB/s down, 3–7 up | 23–28 KB/s down, about 6 up |

Bad network: 120 ms ±30 one way, 3% loss. Normal network: 60 ms ±10, 1% loss. Runs are in `Library/CodexPlaytests/purrdiction/p01` to `p08`. `p08/seat_switch_c2.gif` is the overhead view of the runner taking the wheel.

## Problems hit, and the fixes

- **Repeated button presses.** When an input is missing, the host repeats the last one, so a "pressed E" flag pressed again and the seat toggled on and off. Inputs now carry press counters.
- **Unchanged states are never re-sent.** PurrDiction doesn't send or store a state that hasn't changed, so the newest confirmed state can be seconds old.
  - The truck is stamped with the newest applied server frame (`verifiedServerTick`).
  - A remote player who stood still and then walks gets a "held until the previous frame" sample. Without it they would creep across the whole idle time.
  - Past the newest state, idle players hold still instead of extrapolating.
- **Tick labels.** The state after simulating tick T is labelled T + 1, as PurrDiction labels verified states.
- **Buffers keyed by tick.** Buffers are keyed by tick number, not time. The tick-to-time offset varies by floating-point noise, so a replayed tick added a near-duplicate entry instead of replacing the old one, which threw the truck about 11 cm.
- **Tick-to-server-time offset.** It comes from PurrNet's fixed tick schedule (`tickModule.lastTickTime`), not from frame times, which wobbled by a few milliseconds and moved the truck up to 14 cm.
- **PurrDiction's view tick.** It holds and then jumps a tick whenever PurrNet adjusts the client's tick pace. The driver and the own player are drawn from `localTick - 1 + floatingPoint` instead.
- **Startup order.** The host could step the NPC AI before `OnSpawned(asServer)` had seeded it, so the AI step now waits for an explicit flag.

## Not resolved

- **Prediction lead.** The driver is 0.26–0.44 s ahead of the shared timeline, against about 0.2 s in the original. The kids on the driver's screen trail the truck by that much.
- **Corrections after the seat change.** At join and right after leaving the seat, the host's version of the player's walk differs from the prediction by exactly 1–2 ticks. The probable cause is PurrDiction re-adjusting the prediction lead; this was not confirmed.
- **Runner beside the truck.** The runner's screen predicts the truck with the driver's last steering, so their position relative to the truck is corrected by up to 45 cm (eased) whenever the driver steers.
- **Analyzer.** `analyze.py` A3 (idle drift) flags the frame after the bot releases the keys, because movement now shows a tick later, and the easing of those corrections. A1 still requires 0–1 frames.
