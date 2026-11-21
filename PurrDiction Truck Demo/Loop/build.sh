#!/usr/bin/env bash
# Rebuilds the scene and the Linux player in batch mode. Fails on compile or build errors.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=/tmp/purrnet/build.log
mkdir -p /tmp/purrnet
DISPLAY=${DISPLAY:-:0} timeout 900 ~/Unity/Hub/Editor/6000.3.12f1/Editor/Unity -batchmode -projectPath "$PWD" -executeMethod DemoBuilder.BuildAll -quit -logFile "$LOG" > /dev/null 2>&1 || true
if grep -qE "error CS|Scripts have compiler errors" "$LOG"; then grep -E "error CS" "$LOG" | sort -u; exit 1; fi
grep -q "DemoBuilder: build Succeeded" "$LOG" || { grep -iE "exception|error" "$LOG" | head -20; exit 1; }
echo "build ok"
