#!/usr/bin/env bash
# ghidra_decomp.sh <workdir> <targets.txt> <outdir> [import]
# First run (or arg 'import'): imports libil2cpp.so (no auto-analysis, fast). Later runs reuse the project.
# Env overrides: GRE_PROJ (existing project dir), GRE_SO, GRE_SCRIPT, GHIDRA_MAXMEM. Reused project needs il2cpp.rep.
# targets.txt: Java regexes matched against 'Namespace.Class$$Method' (see templates/targets_example.txt)
set -euo pipefail
W="$1"; TG="$2"; OUT="$3"; MODE="${4:-}"; K="$(cd "$(dirname "$0")/.." && pwd)"
source "$K/bin/env.sh" "$W"
H=$(ls -d "$GRE_TOOLS"/ghidra_*_PUBLIC | head -1)
[[ -n "${JAVA_HOME:-}" ]] || { echo "no JDK25 in tools/: run bin/setup.sh ghidra"; exit 1; }
P="${GRE_PROJ:-$W/ghidra_proj}"; mkdir -p "$P" "$OUT"
if [[ "$MODE" == import || ! -d "$P/il2cpp.rep" && ! -f "$P/il2cpp.gpr" ]]; then
  "$H/support/analyzeHeadless" "$P" il2cpp -import "$GRE_SO" -noanalysis -overwrite \
     -scriptPath "$K/ghidra" -postScript Il2CppDecomp.java "$GRE_SCRIPT" "$TG" "$OUT"
else
  "$H/support/analyzeHeadless" "$P" il2cpp -process libil2cpp.so -noanalysis \
     -scriptPath "$K/ghidra" -postScript Il2CppDecomp.java "$GRE_SCRIPT" "$TG" "$OUT"
fi
echo "decompiled -> $OUT ; run bin/redact.py --check on it before sharing"
