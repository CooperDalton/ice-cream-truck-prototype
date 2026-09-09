Run the performance test from the repository root with Unity connected and Play Mode stopped:

```powershell
& '.\Ice Cream Truck Prototype\Tools\Run-PerformanceBenchmark.ps1' -Label after-change
```

The runner takes the shared Unity lock, saves the current scene, temporarily selects town seed 4312, enters Play Mode, runs the measurements, checks the console, then restores the scene, world settings, and frame-rate settings. Reports, frame-by-frame CSV files, and a screenshot go to `Library/CodexPlaytests/Performance/`. The label identifies the combined report; raw captures have UTC timestamps.

The frame test warms up for 90 frames and records 720 frames across a scripted road traversal, a parked crowd with music, and tool placement. It discards the first 10 frames of each phase from summary statistics. The separate navigation test checks all 102 resident approaches and a blocked destination. `Truck.Navigation` and `Truck.Placement` markers are also available in Unity's Profiler.

Measured on September 9, 2026 UTC, using Unity 6000.3.12f1, an RTX 3070 Ti, and an 876 × 493 Game view:

| Measurement | Before | After |
| --- | ---: | ---: |
| One blocked-destination path request | 48.204 ms | 0.006 ms |
| Normal resident approaches reaching their target | 102/102 | 102/102 |
| Driving: mean draw calls | 3,420 | 1,450 |
| Parked crowd: mean draw calls | 4,814 | 1,539 |
| Kitchen placement: mean draw calls | 6,622 | 2,075 |
| Kitchen placement: mean CPU draw-submission time | 2.275 ms | 1.497 ms |
| Driving: p95 wall-frame time | 16.117 ms | 13.555 ms |
| Parked crowd: p95 wall-frame time | 12.654 ms | 12.010 ms |
| Kitchen placement: p95 wall-frame time | 16.931 ms | 15.628 ms |

Rendering control capture: `20260909-043716`. Final capture: `20260909-044040`. The rendering control already included the navigation fix to isolate rendering costs. The blocked-path measurement was captured separately before that fix.

Changes kept:

- Reject obstructed or out-of-bounds destinations before A* searches the map. Failed customer paths respect their retry timer.
- Enable GPU resident drawing on the desktop URP asset, retain its required shader variants, and disable competing static batching for Standalone builds. Existing Forward+ rendering stays in use.

GPU occlusion was tested separately and left disabled. It reduced submitted geometry, but the final occlusion-enabled run had higher GPU time and worse kitchen frame times than batching alone. Capture `20260909-043921` records that experiment. Frustum culling remains enabled.

These are Editor measurements, including Editor overhead, with a fixed seed and a scripted route. They do not establish standalone-build FPS, loading performance, or performance on every map or GPU. Compare matching resolutions and hardware. The initial broad inventory counted shared static-batch meshes repeatedly; use the per-frame triangle counter instead of that early inventory's mesh-triangle total.

The second graphics pass uses two shadow cascades instead of four, half-resolution ambient occlusion, and GPU resident drawing's small-mesh culling threshold of 0.5% of screen height. It also disables the opaque-color texture copy; no project shaders use that texture. Shadow distance stays at 50 m, with the existing 2048 shadow map and soft-shadow quality. The shadow split and depth bias were adjusted for the two-cascade layout.

Run the same route with a fixed 1920 x 1080 camera render target:

```powershell
& '.\Ice Cream Truck Prototype\Tools\Run-PerformanceBenchmark.ps1' -Label graphics-1080p -FullHD
```

This mode restores the camera target after sampling and skips the screenshot. It measures the scene rendered offscreen inside the Editor; overlay UI is not part of that render target. The normal mode still captures the Game view.

Matching 1080p captures on the same hardware, before and after this second pass:

| Measurement | Previous optimized settings | Second graphics pass |
| --- | ---: | ---: |
| Driving: mean draw calls | 1,451 | 987 |
| Parked crowd: mean draw calls | 1,539 | 1,086 |
| Kitchen placement: mean draw calls | 2,078 | 1,537 |
| Driving: mean GPU time | 1.293 ms | 1.212 ms |
| Parked crowd: mean GPU time | 1.389 ms | 1.290 ms |
| Kitchen placement: mean GPU time | 1.697 ms | 1.205 ms |
| Kitchen placement: mean CPU draw-submission time | 1.844 ms | 1.404 ms |

Control capture: `20260909-045301`. Final capture: `20260909-045358`. These comparisons used warmed runs; an earlier first run had large frame-time outliers. The final sample had no frames over 33.3 ms, all 102 navigation approaches succeeded, and the console had no errors. This does not establish that all intermittent stalls are gone. Outdoor screenshots were also checked after the final shadow-bias adjustment.
