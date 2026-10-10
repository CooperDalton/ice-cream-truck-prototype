#!/usr/bin/env bash
# Runs Quantum's qtn codegen headlessly. User C# that may reference not-yet-generated types is parked in .codegen-held/
# (outside Assets, not Temp/) while Unity runs, then restored even if Unity fails.
set -u
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
HELD="$PROJECT/.codegen-held"
export UNITY_NON_INTERACTIVE=1 UNITY_NO_BANNER=1 DISPLAY="${DISPLAY:-:0}" WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
FILES=(Assets/QuantumUser/Simulation/ZombieTruck Assets/QuantumUser/Simulation/DivorcedDads Assets/QuantumUser/Simulation/SystemSetup.User.cs Assets/QuantumUser/Simulation/RuntimeConfig.User.cs Assets/Scripts)
if [ -e "$HELD" ]; then echo "error: $HELD exists from an interrupted run; restore it first" >&2; exit 1; fi
mkdir -p "$HELD"
restore() {
  for item in "${FILES[@]}"; do
    rm -rf "$PROJECT/$item"
    mkdir -p "$(dirname "$PROJECT/$item")"
    cp -a "$HELD/$item" "$PROJECT/$item"
  done
  rm -rf "$HELD"
}
trap restore EXIT
for item in "${FILES[@]}"; do
  mkdir -p "$(dirname "$HELD/$item")"
  cp -a "$PROJECT/$item" "$HELD/$item"
done
# Keep the qtn files in place; move the C# out.
find "$PROJECT/Assets/QuantumUser/Simulation/ZombieTruck" "$PROJECT/Assets/QuantumUser/Simulation/DivorcedDads" -name "*.cs" -delete
find "$PROJECT/Assets/Scripts" -name "*.cs" -delete
printf 'namespace Quantum { public static partial class DeterministicSystemSetup { } }\n' > "$PROJECT/Assets/QuantumUser/Simulation/SystemSetup.User.cs"
printf 'namespace Quantum { public partial class RuntimeConfig { } }\n' > "$PROJECT/Assets/QuantumUser/Simulation/RuntimeConfig.User.cs"
unity run "$PROJECT" --timeout 900 -- -executeMethod Quantum.Editor.QuantumCodeGenQtn.Run -logFile "$PROJECT/Logs/codegen.log" > /dev/null 2>&1
status=$?
grep -E "Finished Qtn CodeGen|error" "$PROJECT/Logs/codegen.log" | grep -v "Licensing\|LogAssemblyErrors" | tail -5
exit $status
