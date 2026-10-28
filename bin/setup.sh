#!/usr/bin/env bash
# Idempotent toolchain install into $GRE_HOME/tools (default: <kit>/tools). No sudo needed.
# Installs: python venv (UnityPy, TypeTreeGeneratorAPI, capstone, pyelftools), Il2CppDumper, JDK 25 (Temurin), Ghidra.
# Needs: python3, curl, unzip, tar, dotnet (>=6, for Il2CppDumper; set DOTNET_ROLL_FORWARD=Major if only 8+).
set -euo pipefail
KIT="$(cd "$(dirname "$0")/.." && pwd)"
T="${GRE_HOME:-$KIT}/tools"; mkdir -p "$T"; cd "$T"
only="${1:-all}"   # all | py | dumper | ghidra
step(){ [[ "$only" == all || "$only" == "$1" ]]; }

if step py && [[ ! -x venv/bin/python ]]; then
  python3 -m venv venv
  venv/bin/pip -q install UnityPy TypeTreeGeneratorAPI capstone pyelftools
fi
if step dumper && [[ ! -f il2cppdumper/Il2CppDumper.dll ]]; then
  # net6 build; runs on newer dotnet via roll-forward. Pin version, check https://github.com/Perfare/Il2CppDumper/releases
  curl -sL -o d.zip https://github.com/Perfare/Il2CppDumper/releases/download/v6.7.46/Il2CppDumper-net6-v6.7.46.zip
  mkdir -p il2cppdumper && unzip -q -o d.zip -d il2cppdumper && rm d.zip
  sed -i 's/"RequireAnyKey": true/"RequireAnyKey": false/' il2cppdumper/config.json
fi
if step ghidra; then
  # Ghidra 12.x needs a full JDK >= 25 (a JRE or older JDK fails with "unsupported java version"). Check application.properties.
  if ! ls -d jdk-25* >/dev/null 2>&1; then
    curl -sL -o jdk.tgz "https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jdk/hotspot/normal/eclipse"
    tar xzf jdk.tgz && rm jdk.tgz
  fi
  if ! ls -d ghidra_*_PUBLIC >/dev/null 2>&1; then
    url=$(curl -s https://api.github.com/repos/NationalSecurityAgency/ghidra/releases/latest | python3 -c "import json,sys;print([a['browser_download_url'] for a in json.load(sys.stdin)['assets'] if a['name'].endswith('.zip')][0])")
    curl -L -o ghidra.zip "$url" && unzip -q ghidra.zip && rm ghidra.zip
  fi
fi
echo "tools ready in $T"
