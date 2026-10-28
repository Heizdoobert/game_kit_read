#!/usr/bin/env bash
# run_all.sh <game.apk|xapk> <workdir> [stages]   stages (default "unpack meta dump assets"): unpack meta dump assets kb
# Runs the deterministic part of the workflow (SKILL steps 1-4) and scaffolds the KB. Ghidra stays manual (needs targets).
set -euo pipefail
K="$(cd "$(dirname "$0")/.." && pwd)"; APK="$1"; W="$2"; ST="${3:-unpack meta dump assets}"
mkdir -p "$W"; source "$K/bin/env.sh" "$W"
has(){ [[ " $ST " == *" $1 "* ]]; }
A="$W/apk"
if has unpack; then "$K/bin/unpack.sh" "$APK" "$W"; fi
if has meta; then
  md=$(ls "$A"/assets/bin/Data/Managed/Metadata/global-metadata.dat 2>/dev/null || true)
  if [[ -n "$md" ]]; then "$PY" "$K/bin/meta_parse.py" "$md" "$W/raw"; else echo "no IL2CPP metadata: skip meta (see engine.txt)"; fi
fi
if has dump; then "$K/bin/il2cpp_dump.sh" "$W" || echo "il2cpp dump failed: see PLAYBOOK 'failure modes'"; fi
if has assets; then
  [[ -d "$A/assets/aa/Android" ]] && "$PY" "$K/bin/unity_dump.py" --bundles "$A/assets/aa/Android" --out "$W/assets_dump/mono" || echo "no Addressables bundles"
  [[ -f "$A/assets/bin/Data/data.unity3d" && -d "$W/il2cpp/DummyDll" ]] && \
    "$PY" "$K/bin/unity_dump.py" --data "$A/assets/bin/Data/data.unity3d" --dummydll "$W/il2cpp/DummyDll" --out "$W/assets_dump/player" || echo "skip data.unity3d (needs DummyDll)"
  [[ -d "$W/assets_dump" ]] && "$PY" "$K/bin/find_configs.py" "$W/assets_dump" | tee "$W/config_candidates.txt" | head -20
fi
if has kb; then
  mkdir -p "$W/kb"; [[ -f "$W/kb/README.md" ]] || cp "$K/templates/kb_outline.md" "$W/kb/README.md"
  [[ -f "$W/kb/targets.txt" ]] || cp "$K/templates/targets_example.txt" "$W/kb/targets.txt"
  echo "KB scaffold: $W/kb (edit targets.txt, then bin/ghidra_decomp.sh $W $W/kb/targets.txt $W/decompiled)"
fi
"$K/bin/doctor.sh" "$W" | grep -E "^(done|todo)"
