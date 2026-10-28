# PLAYBOOK - detail behind SKILL.md (learned on Camo Guys, Unity 6 IL2CPP, arm64)

## Tool map
| Need | Tool | Notes |
|---|---|---|
| Names/enums/strings in minutes | `bin/meta_parse.py` | pure Python, v24-31 layouts; check printed version |
| Fields, offsets, RVAs, consts, tooltips | Il2CppDumper -> `dump.cs` | `GenerateStruct` gives `il2cpp.h`; DummyDll for UnityPy |
| Method addresses | `script.json` (`ScriptMethod`) | Name = `Ns.Class$$Method`; also ScriptString addresses |
| Scene/prefab/ScriptableObject values | UnityPy (`bin/unity_dump.py`) | Addressables keep typetrees; `data.unity3d` needs DummyDll |
| Tiny functions | `bin/a64dis.py` | formulas, constants, literal pools |
| Big functions | Ghidra headless + `Il2CppDecomp.java` | labels all methods, decompiles regex targets + direct callees |
| Binary-protocol / Lua / other engines | out of scope of the scripts | see detect_engine output |

## Reading arm64 IL2CPP code
- Args: `w0/x0` = this (instance) or first arg (static); IL2CPP appends `MethodInfo*` as last arg - ignore it.
- `csel w0,w9,w8,ne` after `tst w0,#1` = `cond ? a : b`. `mov w8,#0x14` = literal 20. `fmov s0,#...`/`ldr s0,[x8,#off]` = float literal (read the pool with `a64dis.py --f32 VA`).
- `ldr x0,[x20]` after `adrp` = loading a static field/metadata ptr (class, string literal, MethodInfo). `bl 0x17a2ee0` style calls into il2cpp runtime (type init) at method start are boilerplate.
- Field access `[x19,#0x30]` -> look up offset 0x30 in `dump.cs` (`// 0x30`). Constructors (`.ctor`) write defaults of non-serialized fields: `str q0,[x19,#0x20]` stores 4 floats from a literal pool.
- `Class$$MoveNext` of `<Foo>d__N` = coroutine/async state machine; the real logic is in the switch over the state field.
- Generic/shared code appears as `Il2CppFullySharedGenericType` - resolve via the call site.

## Where balance data hides (check in this order)
1. `const`/`static readonly` in dump.cs (and `raw/game_constants`).
2. ScriptableObjects in bundles (`unity_dump.py --bundles`), prefab component values.
3. `RemoteConfigData`/`GameConfig`/`*Profile` objects in `data.unity3d` (JSON-in-string defaults + shipped snapshot `value`).
4. Constructor defaults (no serialized instance).
5. Server-driven (shop prices from store, milestone tables, per-level data) -> mark [?], note the config key.

## Secrets handling
Common leaks: cheat/admin passwords, server product keys, test keys, tracking/ad SDK keys. Mask in deliverables; keep a line in the security doc: "present in X (value redacted)". `redact.py --check` before handing the folder over. Decompiled `.c` files can embed string literals through `STR_<n>_<value>` labels - run redact there too.

## Failure modes seen
| Symptom | Cause / fix |
|---|---|
| Ghidra "unsupported java version", asks for JDK path | only JRE or JDK < required; install full JDK (Temurin) in tools/, `JAVA_HOME` |
| Ghidra script `.py` does nothing | Jython removed in Ghidra 12; use Java script |
| `read_typetree` fails with missing-key editor DLLs | harmless per-object; others still decode |
| `BundleFile.path` AttributeError | iterate `env.files` / `bf.files` instead |
| bash tool call blocked on chained `sleep` | poll with a Monitor/until loop; and never `pgrep -f <text in your own command>` |
| sudo needed | ask the user to run it; agent cannot type the password |
| memory pressure (<4 GB free) | `GHIDRA_MAXMEM=4G`, `-noanalysis`, decompile targets only |

## Quality bar
- Every number: source tag + (ideally) two independent sources.
- Separate "code default" from "shipped remote snapshot" from "server unknown".
- Say plainly what was not verified (no device run, no server access).
