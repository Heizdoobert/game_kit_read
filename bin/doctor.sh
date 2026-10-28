#!/usr/bin/env bash
# doctor.sh [workdir]  - check toolchain + (optionally) which pipeline stages are done. Exit 1 if a required tool is missing.
K="$(cd "$(dirname "$0")/.." && pwd)"; source "$K/bin/env.sh" "${1:-$PWD}"; bad=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "ok   $1"; else echo "MISS $1  -> $3"; bad=1; fi; }
chk python3 "command -v python3" "install python3"
chk venv+UnityPy "$PY -c 'import UnityPy,capstone,elftools'" "bin/setup.sh py"
chk il2cppdumper "test -f $GRE_TOOLS/il2cppdumper/Il2CppDumper.dll" "bin/setup.sh dumper"
chk dotnet "command -v dotnet" "install dotnet >= 6 runtime"
chk jdk25 "test -n '$JAVA_HOME' && $JAVA_HOME/bin/javac -version" "bin/setup.sh ghidra"
chk ghidra "ls -d $GRE_TOOLS/ghidra_*_PUBLIC" "bin/setup.sh ghidra"
chk "unzip/aapt (aapt optional)" "command -v unzip" "install unzip"
echo "free RAM: $(free -g | awk '/Mem:/{print $7}') GB (Ghidra needs ~4 GB; GHIDRA_MAXMEM=$GHIDRA_MAXMEM)"
if [[ -n "${1:-}" ]]; then
  for s in "apk/lib:unpack" "il2cpp/script.json:il2cpp_dump" "raw/types_dump.txt:meta_parse" "assets_dump/mono:unity_dump(bundles)" "assets_dump/player:unity_dump(data)" "ghidra_proj/il2cpp.rep:ghidra import"; do
    [[ -e "$1/${s%%:*}" ]] && echo "done ${s##*:}" || echo "todo ${s##*:}"; done
fi
exit $bad
