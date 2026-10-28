# game_re_kit - static game reverse-engineering kit + agent skill

Package -> confidence-tagged knowledge base (KB). Built from the Camo Guys analysis (Unity 6 / IL2CPP / arm64). Everything is self-contained in this folder (`tools/` is created here by `setup.sh`).

## Layout
```
SKILL.md               agent workflow (install: ln -s <this dir> ~/.claude/skills/game-reverse)
README.md              this file
bin/setup.sh           install venv + Il2CppDumper + JDK25 + Ghidra into ./tools (idempotent; arg: py|dumper|ghidra)
bin/doctor.sh [work]   check toolchain, show which pipeline stages are done/todo
bin/env.sh <work>      source it -> GRE_* vars, $PY, JAVA_HOME, GRE_SO, GRE_SCRIPT
bin/run_all.sh         one-shot pipeline: unpack, meta, dump, assets, kb scaffold
bin/unpack.sh          unzip apk/xapk (+nested splits) + engine fingerprint
bin/detect_engine.py   Unity IL2CPP/Mono, Unreal, Godot, Cocos, native + next-step advice
bin/meta_parse.py      global-metadata.dat -> types/fields/strings (no deps)
bin/il2cpp_dump.sh     Il2CppDumper -> dump.cs, script.json, il2cpp.h, DummyDll
bin/unity_dump.py      Addressables bundles / data.unity3d MonoBehaviours -> JSON (auto-redact; --only NAME)
bin/find_configs.py    rank dumped JSON by "looks like a balance table"
bin/a64dis.py          disassemble small methods by name; --f32 VA n reads literal pool
bin/ctor_defaults.py   map a decompiled .ctor's `this+0xOFF = imm` stores to dump.cs field names (code-default field values)
bin/fn.py              print a decompiled .c compactly (no decls/guards/casts) and name fields from dump.cs (`this.m_LoadCo`); ambiguous name -> lists matches; fn.py 'Class$$Method' -n 120
bin/xref.py            who touches a field (-f Class FIELD, W/R) / uses a string (-s) / calls a function (-c) across decompiled/
bin/selftest.sh        offline smoke test of the helpers on tiny fixtures (run after any change to bin/)
bin/_dump.py           shared dump.cs field-table helper (base classes, nested types)
bin/pool_consts.py     list float/int constants a method loads (ldr literal, adrp+ldr, fmov, mov+movk); -r REGEX for a whole class
bin/ghidra_decomp.sh   headless decompile of regex-selected methods (ghidra/Il2CppDecomp.java)
bin/decomp_digest.py   decompiled dir -> per-class markdown (callees, strings, floats, field offsets)
bin/redact.py          --check / --apply: find & mask secrets before sharing
ghidra/Il2CppDecomp.java   Ghidra script: label methods+strings from script.json, bounded decompile
templates/             kb_outline.md, targets_example.txt
docs/PLAYBOOK.md       reading arm64/IL2CPP output, where balance data hides, failure modes
```

## Requirements
Linux x64, python3, curl, unzip, tar, dotnet >= 6 runtime (Il2CppDumper), ~3 GB disk for tools, >= 4 GB free RAM for Ghidra. `setup.sh` downloads (~1 GB): ask the user first. `bin/doctor.sh` tells what is missing.

## Steps (all paths relative to kit; `W` = your workdir)
```bash
bin/setup.sh                                   # 0. once
bin/doctor.sh                                  #    verify
bin/run_all.sh game.apk W                      # 1-4. unpack -> meta -> il2cpp dump -> asset dump (+kb scaffold: add 'kb' stage)
source bin/env.sh W                            #    gives $PY, GRE_SO, GRE_SCRIPT
$PY bin/find_configs.py W/assets_dump          # 4b. find balance/config tables; look for RemoteConfigData/GameConfig/*Profile
$PY bin/ctor_defaults.py out/Ns.Class\$\$.ctor.c Ns.Class      # 5c. field defaults by name (prefab may override)
$PY bin/pool_consts.py -r '^Ns\.Class\$\$'                 # 5b. all numeric thresholds of a class (needs GRE_SO, GRE_SCRIPT)
$PY bin/a64dis.py 'Class$$Method'              # 5a. small rules (formulas, defaults); --f32 VA n for ctor literal pools
cp templates/targets_example.txt W/kb/targets.txt   # 5b. edit regexes -> Class$$Method
bin/ghidra_decomp.sh W W/kb/targets.txt W/decompiled   # first run imports .so (no auto-analysis); later runs reuse
# reuse an old project / custom paths: GRE_PROJ=<dir with il2cpp.gpr> GRE_SO=<libil2cpp.so> GRE_SCRIPT=<script.json> GHIDRA_MAXMEM=3G bin/ghidra_decomp.sh ...
# regex tip: Namespace differs per class (e.g. SeekerHumanizer is Chameleon.Bot, SeekerOklab is Chameleon.Seeker) - grep dump.cs for "class X" first. Bleed-over fix: mk() deletes the containing function.
python3 -I bin/decomp_digest.py W/decompiled W/digest.md   # skim first, then read .c of interesting methods
# 6. cross-check numbers (asm vs dump const vs prefab vs remote default)
# 7. write KB from templates/kb_outline.md, tag [C][A][P][S][?], keep Gaps
python3 -I bin/redact.py --check W/kb --exclude raw,il2cpp,decompiled   # 8. must be 0 hits; --apply to mask
```
Run stages separately: `bin/run_all.sh game.apk W "unpack meta"` (stages: unpack meta dump assets kb).

## Picking Ghidra targets (the part that needs judgement)
1. Start from `dump.cs`/`types_dump.txt`: find the manager/controller classes named in strings and enums (MatchManager, *Controller, *Service, *Booster).
2. Use regex per class (`^Ns\.Class\$\$`) - a whole class of ~150 methods decompiles in ~5 min; whole game (140k methods) does not.
3. Skip getters/setters/ctors/event add_/remove_: tiny methods may decompile with 1000+ lines of bleed-over (body bound = next method address; tail-call getters fall through). Use `a64dis.py` for them.
4. Decompiled code has no struct types: `*(T*)(this+0x98)` = field at offset 0x98 -> look up in `il2cpp/dump.cs` (`// 0x98`). `STR_<n>_<text>` labels are string literals; `func_0x...(PTR_DAT_..)` is class-init noise, ignore. `*(char*)(x+0xe4)==0` followed by `func_0x...` = static-ctor check.
5. Coroutines/async: logic is in `<Name>d__N$$MoveNext` (state machine switch on `*(param+0x10)`).

## Troubleshooting
| Symptom | Fix |
|---|---|
| `unsupported java version` / JDK prompt | need full JDK >= 25 in tools/ (`setup.sh ghidra`), `source env.sh` sets JAVA_HOME |
| `LockException` project locked | previous Ghidra killed: `rm W/ghidra_proj/*.lock*` |
| Ghidra OOM / box freezes | `GHIDRA_MAXMEM=3G`, fewer targets, close other apps |
| Il2CppDumper "metadata version" / crash | wrong build or encrypted metadata -> dump from memory on device (out of scope) |
| `UnityPy` missing typetree | pass `--dummydll W/il2cpp/DummyDll` |
| `pkill -f` killed my shell | use `pgrep -f "[a]nalyzeHeadless"` bracket trick |
| `sleep` blocked in agent | poll with a monitor/until-loop, not long sleeps |

## Safety
Static analysis of builds you are permitted to analyze. No cheating tools for live games, no bypassing protections. Dumps (`raw/ il2cpp/ decompiled/`) contain hardcoded secrets: never share them; `redact.py` the KB.
