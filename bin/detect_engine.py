#!/usr/bin/env python3
"""Fingerprint the game engine/scripting backend from an unzipped APK dir. Prints next-step advice."""
import os, sys, glob
r = sys.argv[1]
def has(p): return glob.glob(os.path.join(r, p), recursive=True)
e = []
if has('lib/*/libunity.so'):
    il = has('lib/*/libil2cpp.so'); md = has('assets/bin/Data/Managed/Metadata/global-metadata.dat')
    mono = has('assets/bin/Data/Managed/Assembly-CSharp.dll')
    e.append('Unity')
    if il and md: e.append('IL2CPP -> use bin/il2cpp_dump.sh (+ unity_dump.py, ghidra_decomp.sh)')
    elif mono: e.append('Mono: Assembly-CSharp.dll present -> decompile with ilspycmd/dnSpy (no IL2CPP step)')
    if has('assets/aa/**/*.bundle'): e.append('Addressables bundles present (assets/aa) -> unity_dump.py --bundles')
    if has('assets/bin/Data/data.unity3d'): e.append('data.unity3d (built-in scenes/ScriptableObjects) -> unity_dump.py --data')
    if has('lib/*/libmain.so') and not il: e.append('note: libil2cpp.so missing - check split APK (config.arm64_v8a.apk)')
elif has('lib/*/libUE4.so') or has('lib/*/libUnreal.so'): e.append('Unreal (pak files, use UE4 tooling: UModel/repak)')
elif has('lib/*/libgodot*.so') or has('assets/*.pck'): e.append('Godot (.pck -> gdsdecomp)')
elif has('assets/**/*.lua') or has('lib/*/libcocos*.so'): e.append('Cocos/Lua (check assets for .jsc/.luac)')
elif has('classes*.dex') and not has('lib/*/*.so'): e.append('Native Android/Java (jadx)')
else: e.append('unknown: inspect lib/*/ and assets/')
if has('lib/*/libFirebase*.so'): e.append('SDKs: Firebase')
if has('lib/*/liblivekit*'): e.append('SDKs: LiveKit (voice)')
print('\n'.join(e))
