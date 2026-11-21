#!/usr/bin/env python3
"""Checks a soak run's per-frame logs against the acceptance criteria in Loop/STATE.md.

Snap metric: second-order prediction error e_i = |p_i - (p_{i-1} + v_{i-1} * dt_i)|, i.e. how
far the drawn position lands from where its previous velocity would have put it. Smooth motion
gives millimetres even when accelerating; a snap of d metres shows up as about d.
"""
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

WARMUP = 3.0


def load(path):
    frames = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    frames.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # last line cut off by a kill
    return frames


def snap_errors(samples):
    """samples: list of (t, vec) -> list of (t, err) from the 2nd frame on."""
    out = []
    for i in range(2, len(samples)):
        t0, p0 = samples[i - 2]
        t1, p1 = samples[i - 1]
        t2, p2 = samples[i]
        dt1 = t1 - t0
        dt2 = t2 - t1
        if dt1 <= 0 or dt2 <= 0:
            continue
        pred = [p1[k] + (p1[k] - p0[k]) / dt1 * dt2 for k in range(len(p1))]
        out.append((t2, math.dist(pred, p2)))
    return out


def ang(a):
    return (a + 180) % 360 - 180


def pct(values, q):
    if not values:
        return 0.0
    v = sorted(values)
    return v[min(len(v) - 1, int(q * len(v)))]


def main(run):
    names = sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(run, "*.jsonl")))
    data = {n: load(os.path.join(run, n + ".jsonl")) for n in names}
    report = {"run": run, "instances": {}, "criteria": {}}
    issues = defaultdict(list)

    # Episode bookkeeping across instances.
    owner_frames = defaultdict(list)  # (npc) -> list of (inst, t, pelvis)
    end_sent = []  # (inst, npc, epoch, root, yaw)
    end_recv = []

    impulse_src = defaultdict(list)
    for name, frames in data.items():
        for f in frames:
            for e in f.get("ev", []):
                if e["k"] == "impulse_applied":
                    impulse_src[e["d"]["npc"]].append(e["d"]["t"])
    for name, frames in data.items():
        ready = [f for f in frames if f.get("ready")]
        if not ready:
            issues["A11"].append(f"{name}: never ready")
            continue
        t_ready = ready[0]["t"]
        # trim warm-up and the last 3 s (the host quits first, starving clients at the end)
        frames_w = [f for f in ready if f["t"] - t_ready > WARMUP and ready[-1]["t"] - f["t"] > 3.0]
        inst = {"frames": len(frames), "ready_frames": len(ready)}
        ev_counts = defaultdict(int)
        for f in frames:
            for e in f.get("ev", []):
                ev_counts[e["k"]] += 1
                d = e["d"]
                if e["k"] == "rag_frame":
                    owner_frames[d["npc"]].append((name, d["t"], d["pelvis"]))
                elif e["k"] == "rag_end_sent":
                    end_sent.append((name, d["npc"], d["epoch"], d["root"], d["yaw"], f["t"]))
                elif e["k"] == "rag_end_recv":
                    end_recv.append((name, d["npc"], d["epoch"], d["root"], d["yaw"]))
        inst["events"] = dict(ev_counts)

        # ---- frame time ----
        dts = [f["dt"] for f in frames_w]
        inst["fps_p50"] = round(1 / max(pct(dts, 0.5), 1e-6), 1)
        inst["dt_p99_ms"] = round(pct(dts, 0.99) * 1000, 1)
        ds = [f["D"] for f in frames_w if "D" in f]
        if ds:
            inst["render_delay_ms_p50_max"] = [round(pct(ds, 0.5) * 1000), round(max(ds) * 1000)]

        # ---- truck (A2, A8) ----
        crash_near = set()
        for i, f in enumerate(frames_w):
            if f["tr"][4]:
                for j in range(i - 3, i + 4):
                    crash_near.add(j)
        truck_samples = [(f["t"], (f["tr"][0], f["tr"][1])) for f in frames_w]
        errs = snap_errors(truck_samples)
        tr_err = [e for k, (t, e) in enumerate(errs) if (k + 2) not in crash_near]
        yaw_samples = [(f["t"], (f["tr"][2],)) for f in frames_w]
        # unwrap yaw
        unwrapped = []
        acc = None
        for t, (y,) in yaw_samples:
            acc = y if acc is None else acc + ang(y - prev)
            prev = y
            unwrapped.append((t, (acc,)))
        yaw_err = [e for k, (t, e) in enumerate(snap_errors(unwrapped)) if (k + 2) not in crash_near]
        inst["truck_snap_max_m"] = round(max(tr_err, default=0), 4)
        inst["truck_snap_p99_m"] = round(pct(tr_err, 0.99), 4)
        inst["truck_snaps_over_5cm"] = sum(1 for e in tr_err if e > 0.05)
        inst["truck_yaw_snap_max_deg"] = round(max(yaw_err, default=0), 3)
        inst["truck_yaw_snaps_over_1deg"] = sum(1 for e in yaw_err if e > 1.0)
        modes = defaultdict(int)
        for f in frames_w:
            modes[f["tr"][3]] += 1
        inst["truck_modes"] = dict(modes)
        if inst["truck_snaps_over_5cm"]:
            worst = sorted(((e, t) for (t, e), k in zip(errs, range(len(errs))) if (k + 2) not in crash_near), reverse=True)[:3]
            issues["A2"].append(f"{name}: {inst['truck_snaps_over_5cm']} truck snaps >5cm, worst {[(round(e, 3), round(t - t_ready, 2)) for e, t in worst]}")
        if inst["truck_yaw_snaps_over_1deg"]:
            issues["A2"].append(f"{name}: {inst['truck_yaw_snaps_over_1deg']} truck yaw snaps >1deg (max {inst['truck_yaw_snap_max_deg']})")

        # ---- A1 driver input response ----
        lat = []
        for i in range(1, len(frames_w) - 10):
            f0, f1 = frames_w[i - 1], frames_w[i]
            if f1["tr"][3] not in (1, 2) or f0["inp"][0] == f1["inp"][0]:
                continue
            # only inputs held for a few frames: a one-frame tap may be undone before it shows
            if any(frames_w[k]["inp"][0] != f1["inp"][0] for k in range(i, i + 4)):
                continue
            target = f1["inp"][0] / 100 * 32
            s0 = f1["tr"][6] if len(f1["tr"]) > 6 else None
            if s0 is None:
                break
            if abs(target - s0) < 0.5:
                continue  # wheel already where the new input wants it
            for j in range(i, min(i + 30, len(frames_w))):
                sj = frames_w[j]["tr"][6]
                if abs(sj - s0) > 0.01 and (sj - s0) * (target - s0) > 0:
                    lat.append(j - i)
                    break
        if lat:
            inst["driver_response_frames_max"] = max(lat)
            inst["driver_response_frames_p50"] = pct(lat, 0.5)
            if max(lat) > 1:
                issues["A1"].append(f"{name}: steering responds after up to {max(lat)} frames")

        # ---- players (A3, A4, A9) ----
        per_player = defaultdict(list)
        for f in frames_w:
            for p in f["pl"]:
                per_player[p[0]].append((f["t"], p))
        pl_report = {}
        for pid, seq in per_player.items():
            seq = [x for x in seq if x[0] - seq[0][0] > 0.5]  # skip a joining player's first frames
            if len(seq) < 3:
                continue
            own = seq[0][1][1] == 1
            # truck-local continuity while inside/driving
            inside = [(t, tuple(p[6:9])) for t, p in seq if p[2] != 1]
            world = [(t, tuple(p[3:6])) for t, p in seq]
            # split into contiguous runs (frames consecutive in seq)
            loc_err = []
            run_ = []
            prev_mode = None
            for t, p in seq:
                if p[2] == 1 or (prev_mode is not None and prev_mode != p[2]):
                    if len(run_) > 2:
                        loc_err += [e for _, e in snap_errors(run_)]
                    run_ = []
                if p[2] != 1:
                    run_.append((t, tuple(p[6:9])))
                prev_mode = p[2]
            if len(run_) > 2:
                loc_err += [e for _, e in snap_errors(run_)]
            w_err = snap_errors(world)
            # transitions: world error around mode changes
            trans = []
            for k in range(1, len(seq)):
                if seq[k][1][2] != seq[k - 1][1][2]:
                    window = [e for (t, e) in w_err if abs(t - seq[k][0]) < 0.12]
                    trans.append((seq[k - 1][1][2], seq[k][1][2], round(max(window, default=0), 3), round(seq[k][0] - t_ready, 2)))
            # idle drift for own player inside: no input, local position should not move
            drift = []
            mode_change_t = [seq[k][0] for k in range(1, len(seq)) if seq[k][1][2] != seq[k - 1][1][2]]
            for k in range(1, len(seq)):
                a, b = seq[k - 1][1], seq[k][1]
                # skip the deliberate 0.25 s board/seat ease (checked by A9), not truck drift
                if any(0 <= seq[k][0] - tc < 0.3 for tc in mode_change_t):
                    continue
                if own and a[10] == 0 and b[10] == 0 and a[2] == 0 and b[2] == 0:
                    drift.append(math.dist(a[6:9], b[6:9]))
            ow_err = []
            run_ = []
            for t, p in seq:
                if p[2] == 1:
                    run_.append((t, tuple(p[3:6])))
                else:
                    ow_err += [e for _, e in snap_errors(run_)]
                    run_ = []
            ow_err += [e for _, e in snap_errors(run_)]
            pr = {
                "own": own,
                "local_snap_max_m": round(max(loc_err, default=0), 4),
                "local_snaps_over_10cm": sum(1 for e in loc_err if e > 0.10),
                "outside_world_snap_max_m": round(max(ow_err, default=0), 4),
                "transitions": trans,
                "idle_drift_max_m": round(max(drift, default=0), 5),
            }
            pl_report[str(pid)] = pr
            label = f"{name} player {pid}{' (own)' if own else ''}"
            if pr["local_snaps_over_10cm"]:
                issues["A4"].append(f"{label}: {pr['local_snaps_over_10cm']} truck-local snaps >10cm (max {pr['local_snap_max_m']})")
            if pr["idle_drift_max_m"] > 0.001:
                issues["A3"].append(f"{label}: idle drift {pr['idle_drift_max_m']} m/frame")
            for tr in trans:
                if tr[2] > 0.15:
                    issues["A9"].append(f"{label}: mode {tr[0]}->{tr[1]} at {tr[3]}s snaps {tr[2]} m")
            if sum(1 for e in ow_err if e > 0.15):
                issues["A4"].append(f"{label}: outside world snaps >15cm: {sum(1 for e in ow_err if e > 0.15)} (max {pr['outside_world_snap_max_m']})")
        inst["players"] = pl_report

        # ---- NPCs (A7) ----
        per_npc = defaultdict(list)
        for f in frames_w:
            for n in f["np"]:
                per_npc[n[0]].append((f["t"], n))
        hit_times = defaultdict(list)
        for f in frames_w:
            for e in f.get("ev", []):
                if e["k"] == "hit":
                    hit_times[e["d"]["npc"]].append(f["t"])
        # Impulses another machine forwarded to a ragdoll's owner are real physics; observers see
        # them in the stream at the owner's clock time (srcTime), not at a local hit event.
        npc_bad = []
        walk_speed_bad = []
        prehit_slide = []
        for idx, seq in per_npc.items():
            pel = [(t, tuple(n[4:7])) for t, n in seq]
            src = {t: n[7] for t, n in seq}
            n_at = {t: n for t, n in seq}
            for (t, e) in snap_errors(pel):
                if any(0 <= t - h < 0.1 for h in hit_times[idx]):
                    continue
                if any(0 <= src[t] - it < 0.12 for it in impulse_src[idx]):
                    continue
                if n_at[t][1] == 1 and any(0 <= t - it < 0.12 for it in impulse_src[idx]):
                    continue  # the owner's own physics impact
                if e > 0.25:
                    k = [s for s in seq if s[0] == t][0][1]
                    npc_bad.append((idx, round(e, 3), round(t - t_ready, 2), k[1]))
            for k in range(1, len(seq)):
                (ta, a), (tb, b) = seq[k - 1], seq[k]
                if b[1] == 6 and a[1] in (0, 6):
                    prehit_slide.append(max(0.0, math.dist(a[2:4], b[2:4]) / (tb - ta)))
                if a[1] == 0 and b[1] == 0:
                    d = math.dist(a[2:4], b[2:4])
                    if d > 4.8 * (tb - ta) + 0.05:
                        walk_speed_bad.append((idx, round(d, 3), round(tb - t_ready, 2)))
        inst["npc_pelvis_snaps_over_25cm"] = len(npc_bad)
        inst["physics_impacts_logged"] = sum(1 for f in frames for e in f.get("ev", []) if e["k"] == "impulse_applied")
        inst["npc_walk_teleports"] = len(walk_speed_bad)
        # Deliberate pre-hit ease toward the shooter-seen start pose (state 6). Reported, not
        # a teleport: its size is NPC speed x (2*one-way + render delay).
        inst["prehit_speed_max_mps"] = round(max(prehit_slide, default=0), 2)
        inst["prehit_frames"] = len(prehit_slide)
        if npc_bad:
            issues["A7"].append(f"{name}: {len(npc_bad)} NPC pelvis snaps >25cm, worst {sorted(npc_bad, key=lambda x: -x[1])[:4]}")
        if walk_speed_bad:
            issues["A7"].append(f"{name}: {len(walk_speed_bad)} walking NPC teleports, worst {sorted(walk_speed_bad, key=lambda x: -x[1])[:4]}")

        # ---- underruns ----
        under = defaultdict(int)
        for f in frames_w:
            for k, v in f.get("under", {}).items():
                under[k] += 1
        inst["underrun_frames"] = dict(under)
        report["instances"][name] = inst
        data[name] = (frames_w, t_ready)

    # ---- A6 ragdoll agreement ----
    a6 = {"episodes": 0, "stream_err_max_m": 0, "stream_err_p95_m": 0, "end_root_mismatch_max_m": 0, "resume_root_err_max_m": 0}
    stream_errs = []
    blend_errs = []
    for name, (frames_w, t_ready) in data.items():
        stream_start = {}
        for f in frames_w:
            for n in f["np"]:
                if n[1] != 2 or n[7] < 0:
                    stream_start.pop(n[0], None)
                    continue
                stream_start.setdefault(n[0], f["t"])
                in_blend = f["t"] - stream_start[n[0]] < 0.45
                cands = owner_frames.get(n[0], [])
                # Compare only against the episode's real owner: the instance that sent this
                # epoch's end. A claimer whose claim was rejected also logged frames.
                owners = [e[0] for e in end_sent if e[1] == n[0] and e[2] == n[8]]
                best = None
                for inst_name in owners:
                    fr = sorted((c[1], c[2]) for c in cands if c[0] == inst_name)
                    for i in range(1, len(fr)):
                        if fr[i - 1][0] <= n[7] <= fr[i][0] and fr[i][0] - fr[i - 1][0] < 0.1:
                            u = (n[7] - fr[i - 1][0]) / max(fr[i][0] - fr[i - 1][0], 1e-6)
                            p = [fr[i - 1][1][k] + (fr[i][1][k] - fr[i - 1][1][k]) * u for k in range(3)]
                            best = math.dist(p, n[4:7])
                            break
                    if best is not None:
                        break
                if best is not None:
                    (blend_errs if in_blend else stream_errs).append(best)
    a6["stream_samples"] = len(stream_errs)
    a6["start_blend_err_p50_m"] = round(pct(blend_errs, 0.5), 3)
    a6["start_blend_err_max_m"] = round(max(blend_errs, default=0), 3)
    a6["stream_err_max_m"] = round(max(stream_errs, default=0), 4)
    a6["stream_err_p95_m"] = round(pct(stream_errs, 0.95), 4)
    a6["episodes"] = len(end_sent)
    for (inst_name, npc, epoch, root, yaw, t) in end_sent:
        for (r_inst, r_npc, r_epoch, r_root, r_yaw) in end_recv:
            if r_npc == npc and r_epoch == epoch:
                a6["end_root_mismatch_max_m"] = max(a6["end_root_mismatch_max_m"], round(math.dist(root, r_root), 4))
    # Where each machine actually shows the NPC when it starts walking again.
    resume_errs = []
    for name, (frames_w, t_ready) in data.items():
        last_show = {}
        for f in frames_w:
            for n in f["np"]:
                prev = last_show.get(n[0])
                if prev in (3, 4, 5) and n[1] in (0, 6):
                    ends = [e for e in end_sent if e[1] == n[0] and e[2] == n[8]]
                    if ends:
                        root = ends[0][3]
                        resume_errs.append((round(math.dist((root[0], root[2]), n[2:4]), 4), name, n[0], round(f["t"] - t_ready, 2)))
                last_show[n[0]] = n[1]
    a6["resume_root_err_max_m"] = max((r[0] for r in resume_errs), default=0)
    a6["resumes"] = len(resume_errs)
    report["criteria"]["A6"] = a6
    if a6["stream_err_p95_m"] > 0.15 or a6["stream_err_max_m"] > 0.3:
        issues["A6"].append(f"ragdoll stream divergence p95 {a6['stream_err_p95_m']} max {a6['stream_err_max_m']}")
    if a6["end_root_mismatch_max_m"] > 0.02:
        issues["A6"].append(f"stand-up root mismatch {a6['end_root_mismatch_max_m']}")
    bad_resume = [r for r in resume_errs if r[0] > 0.05]
    if bad_resume:
        issues["A6"].append(f"walk resumes away from stand-up root: {sorted(bad_resume, reverse=True)[:4]}")

    # ---- A5 shots ----
    shots = defaultdict(dict)
    for name, (frames_w, t_ready) in data.items():
        for f in frames_w:
            for e in f.get("ev", []):
                d = e["d"]
                if e["k"] == "splat":
                    shots[d["id"]][name] = (d["auth"], d["pos"])
                if e["k"] == "fire":
                    spawned = [x for x in f.get("ev", []) if x["k"] == "proj_spawn" and x["d"]["id"] == d["id"]]
                    if not spawned:
                        issues["A5"].append(f"{name}: shot {d['id']} not drawn the frame it was fired")
                if e["k"] == "shot_seen" and d["late"] > 0.034:
                    issues["A5"].append(f"{name}: shot {d['id']} drawn {d['late']:.3f}s after its timeline moment")
    splat_err = []
    for sid, per in shots.items():
        auth = [v[1] for v in per.values() if v[0] == 1]
        if auth:
            for v in per.values():
                if v[0] == 0:
                    splat_err.append(math.dist(auth[0], v[1]))
    report["criteria"]["A5"] = {"shots_compared": len(splat_err), "splat_err_p50_m": round(pct(splat_err, 0.5), 3),
                                "splat_err_p95_m": round(pct(splat_err, 0.95), 3), "splat_err_max_m": round(max(splat_err, default=0), 3)}

    # ---- A10 bandwidth ----
    bw = {}
    dur = max((fw[-1]["t"] - fw[0]["t"]) for fw, _ in data.values() if fw) if data else 1
    for p in glob.glob(os.path.join(run, "proxy_*.json")):
        st = json.load(open(p))
        for client, c in st["clients"].items():
            bw[os.path.basename(p)] = {"down_KBps": round(c["down_bytes"] / 1024 / (dur + WARMUP), 2), "up_KBps": round(c["up_bytes"] / 1024 / (dur + WARMUP), 2),
                                       "down_loss": c["down_drop"], "up_loss": c["up_drop"]}
            if c["down_bytes"] / 1024 / (dur + WARMUP) > 64:
                issues["A10"].append(f"{p}: {bw[os.path.basename(p)]['down_KBps']} KB/s down")
    report["criteria"]["A10"] = bw

    # ---- A11 errors ----
    for p in glob.glob(os.path.join(run, "*.log")):
        text = open(p, errors="replace").read()
        exc = re.findall(r"^(\w*Exception[^\n]*)", text, re.M)
        if exc:
            issues["A11"].append(f"{os.path.basename(p)}: {len(exc)} exceptions, first: {exc[0][:160]}")

    report["issues"] = dict(issues)
    crit = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A9", "A10", "A11"]
    report["pass"] = {c: (c not in issues) for c in crit}
    with open(os.path.join(run, "report.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({"pass": report["pass"], "issues": report["issues"]}, indent=1))
    for name, inst in report["instances"].items():
        brief = {k: inst[k] for k in inst if k not in ("players", "events")}
        print(name, json.dumps(brief))
    print("A5", json.dumps(report["criteria"]["A5"]))
    print("A6", json.dumps(report["criteria"]["A6"]))
    print("A10", json.dumps(report["criteria"]["A10"]))


if __name__ == "__main__":
    main(sys.argv[1])
