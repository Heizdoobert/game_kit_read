#!/usr/bin/env bash
# il2cpp_dump.sh <workdir>   needs <workdir>/apk from unpack.sh -> <workdir>/il2cpp/{dump.cs,il2cpp.h,script.json,DummyDll,stringliteral.json}
set -euo pipefail
W="$1"; T="${GRE_TOOLS:-$(cd "$(dirname "$0")/.." && pwd)/tools}"
so=$(ls "$W"/apk/lib/arm64-v8a/libil2cpp.so 2>/dev/null || ls "$W"/apk/lib/*/libil2cpp.so | head -1)
md="$W/apk/assets/bin/Data/Managed/Metadata/global-metadata.dat"
mkdir -p "$W/il2cpp"
DOTNET_ROLL_FORWARD=Major dotnet "$T/il2cppdumper/Il2CppDumper.dll" "$so" "$md" "$W/il2cpp/" </dev/null
ls -la "$W/il2cpp"
echo "If it errors: 'metadata version' -> try other Il2CppDumper build; 'protected/encrypted metadata' -> dump from memory (Frida/GameGuardian) instead."
