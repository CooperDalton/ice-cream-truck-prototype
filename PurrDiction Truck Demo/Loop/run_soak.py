#!/usr/bin/env python3
"""Launch one host and N clients of the Linux player build behind netem proxies, wait, collect logs.

Each instance runs a scripted bot role and writes a per-frame JSONL log. Afterwards analyze.py
checks the acceptance criteria in Loop/STATE.md.
"""
import argparse
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
PLAYER = os.path.join(PROJECT, "Build", "TruckDemo.x86_64")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--host-bot", default="gunner")
    ap.add_argument("--client-bots", default="driver,runner")
    ap.add_argument("--latency", type=float, default=60)
    ap.add_argument("--jitter", type=float, default=10)
    ap.add_argument("--loss", type=float, default=0.01)
    ap.add_argument("--duration", type=float, default=90)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--capture", default="", help="instance names that save screenshots, comma separated")
    ap.add_argument("--extra", default="", help="extra args passed to every instance")
    args = ap.parse_args()
    args.out = os.path.abspath(args.out)
    os.makedirs(args.out, exist_ok=True)
    env = dict(os.environ, DISPLAY=os.environ.get("DISPLAY", ":0"))
    procs = []
    captures = set(filter(None, args.capture.split(",")))

    def launch(name, role, port, bot):
        cmd = [PLAYER, "-batchmode", "-logFile", os.path.join(args.out, name + ".log"),
               "-role", role, "-port", str(port), "-bot", bot, "-name", name,
               "-out", os.path.join(args.out, name + ".jsonl"), "-duration", str(args.duration),
               "-seed", str(args.seed)]
        if name in captures:
            cmd += ["-capture", os.path.join(args.out, "shots_" + name)]
        cmd += args.extra.split()
        procs.append((name, subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))

    server_port = 7777
    launch("host", "host", server_port, args.host_bot)
    time.sleep(1.5)
    for i, bot in enumerate(filter(None, args.client_bots.split(","))):
        port = 7801 + i
        proxy = subprocess.Popen([sys.executable, os.path.join(HERE, "netem_proxy.py"), "--listen", str(port),
                                  "--server", str(server_port), "--latency", str(args.latency),
                                  "--jitter", str(args.jitter), "--loss", str(args.loss),
                                  "--seed", str(args.seed * 100 + i),
                                  "--stats", os.path.join(args.out, f"proxy_c{i + 1}.json")])
        procs.append((f"proxy{i + 1}", proxy))
        time.sleep(0.2)
        launch(f"c{i + 1}", "client", port, bot)

    deadline = time.time() + args.duration + 40
    games = [(n, p) for n, p in procs if not n.startswith("proxy")]
    while time.time() < deadline and any(p.poll() is None for _, p in games):
        time.sleep(0.5)
    status = {}
    for name, p in procs:
        if p.poll() is None:
            p.send_signal(signal.SIGTERM)
            try:
                p.wait(5)
            except subprocess.TimeoutExpired:
                p.kill()
            status[name] = "killed"
        else:
            status[name] = p.returncode
    print("exit status:", status)


if __name__ == "__main__":
    main()
