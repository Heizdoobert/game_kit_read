#!/usr/bin/env bash
# unpack.sh <game.apk|xapk|apks> <workdir>   -> <workdir>/apk (unzipped) + engine report
set -euo pipefail
src="$1"; W="$2"; K="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$W/apk"; unzip -q -o "$src" -d "$W/apk"
# split APK/XAPK: unzip nested .apk files too
for n in "$W"/apk/*.apk; do [[ -f "$n" ]] && unzip -q -o "$n" -d "$W/apk" || true; done
aapt dump badging "$src" 2>/dev/null | grep -E "^(package|sdkVersion|targetSdkVersion|application-label:|launchable)" > "$W/manifest_badging.txt" || true
aapt dump permissions "$src" 2>/dev/null > "$W/permissions.txt" || true
python3 "$K/detect_engine.py" "$W/apk" | tee "$W/engine.txt"
