# source this: eval "$(game_re_kit/bin/env.sh <workdir>)"  or  source game_re_kit/bin/env.sh <workdir>
# Sets GRE_* paths so every tool finds the unpacked APK / il2cpp outputs / tools.
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GRE_KIT="$KIT"
export GRE_HOME="${GRE_HOME:-$KIT}"
export GRE_WORK="${1:-${GRE_WORK:-$PWD}}"
export GRE_TOOLS="$GRE_HOME/tools"
export PY="$GRE_TOOLS/venv/bin/python"
export JAVA_HOME="$(ls -d "$GRE_TOOLS"/jdk-25* 2>/dev/null | head -1)"
[[ -n "$JAVA_HOME" ]] && export PATH="$JAVA_HOME/bin:$PATH"
export GHIDRA_MAXMEM="${GHIDRA_MAXMEM:-4G}"
export DOTNET_ROLL_FORWARD=Major
# first existing candidate wins (kit layout, then the layout used by the first build: apk_extract/ + tools/out_perfare/)
first(){ for p in "$@"; do [[ -e "$p" ]] && { echo "$p"; return; }; done; echo "$1"; }
export GRE_SO="${GRE_SO:-$(first "$GRE_WORK/apk/lib/arm64-v8a/libil2cpp.so" "$GRE_WORK/apk_extract/lib/arm64-v8a/libil2cpp.so")}"
export GRE_SCRIPT="${GRE_SCRIPT:-$(first "$GRE_WORK/il2cpp/script.json" "$GRE_WORK/tools/out_perfare/script.json")}"
