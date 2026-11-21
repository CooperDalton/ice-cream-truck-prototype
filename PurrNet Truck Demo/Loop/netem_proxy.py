#!/usr/bin/env python3
"""UDP proxy that adds one-way latency, jitter and loss between game clients and the host.

Clients connect to --listen; every client address gets its own upstream socket to --server.
Delay per packet = latency + uniform(-jitter, jitter), kept monotonic per flow (no reordering),
loss is applied independently per packet and direction. Byte counters per client and direction
are written to --stats every second.
"""
import argparse
import heapq
import json
import random
import select
import socket
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", type=int, required=True)
    ap.add_argument("--server", type=int, required=True)
    ap.add_argument("--latency", type=float, default=60.0, help="one-way ms")
    ap.add_argument("--jitter", type=float, default=10.0, help="+- ms")
    ap.add_argument("--loss", type=float, default=0.01)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--stats", default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    front = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    front.bind(("127.0.0.1", args.listen))
    front.setblocking(False)
    server_addr = ("127.0.0.1", args.server)

    upstream = {}  # client addr -> socket
    by_sock = {}  # socket -> client addr
    last_due = {}  # (flow) -> last scheduled time, keeps per-flow order
    stats = {}
    queue = []
    seq = 0
    next_stats = time.monotonic() + 1.0

    def schedule(flow, sock, data, dest, direction, client):
        nonlocal seq
        st = stats.setdefault(str(client), {"up_bytes": 0, "down_bytes": 0, "up_drop": 0, "down_drop": 0, "up_pkts": 0, "down_pkts": 0})
        if rng.random() < args.loss:
            st[direction + "_drop"] += 1
            return
        st[direction + "_bytes"] += len(data)
        st[direction + "_pkts"] += 1
        now = time.monotonic()
        due = now + max(0.0, args.latency + rng.uniform(-args.jitter, args.jitter)) / 1000.0
        due = max(due, last_due.get(flow, 0.0))
        last_due[flow] = due
        seq += 1
        heapq.heappush(queue, (due, seq, sock, data, dest))

    while True:
        timeout = 0.001
        if queue:
            timeout = max(0.0, min(timeout, queue[0][0] - time.monotonic()))
        readable, _, _ = select.select([front] + list(by_sock.keys()), [], [], timeout)
        for s in readable:
            if s is front:
                while True:
                    try:
                        data, addr = front.recvfrom(65536)
                    except BlockingIOError:
                        break
                    if addr not in upstream:
                        up = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        up.bind(("127.0.0.1", 0))
                        up.setblocking(False)
                        upstream[addr] = up
                        by_sock[up] = addr
                    schedule((addr, "up"), upstream[addr], data, server_addr, "up", addr[1])
            else:
                addr = by_sock[s]
                while True:
                    try:
                        data, _ = s.recvfrom(65536)
                    except BlockingIOError:
                        break
                    schedule((addr, "down"), front, data, addr, "down", addr[1])
        now = time.monotonic()
        while queue and queue[0][0] <= now:
            _, _, sock, data, dest = heapq.heappop(queue)
            sock.sendto(data, dest)
        if args.stats and now >= next_stats:
            next_stats = now + 1.0
            with open(args.stats, "w") as f:
                json.dump({"t": time.time(), "clients": stats}, f)


if __name__ == "__main__":
    main()
