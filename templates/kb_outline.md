# <Game> (<package> v<ver>) - Knowledge Base
Source: static analysis of <file> (not run on device). Tags: [C] confirmed · [A] asm/decompile · [P] prefab/asset · [S] inferred · [?] unknown.

| File | Content |
|---|---|
| 01_overview.md | what the game is, build info, engine/backend, SDK stack, permissions |
| 02_gameplay.md | loop, phases, roles, controls, AI/bots, camera |
| 03_networking.md | transport, endpoints, opcodes table, lobby/match state machine, resync/rejoin, voice |
| 04_meta_economy.md | currencies, items, shop/IAP SKUs, ads placements, events |
| 05_content.md | maps/levels, models, assets/bundles, UI panels |
| 06_config_tracking.md | remote config keys + defaults, analytics events |
| 07_debug_security.md | debug/cheat classes, hardcoded secrets (values redacted), risks |
| 08_class_index.md | namespace -> key classes |
| 09_data_tables.md | numeric tables from ScriptableObjects/prefabs |
| 10_values_and_config.md | opcode numbers, constants, config values |
| 11_rules_formulas.md | formulas from asm/decompile with source tags |
| 12_remote_config_defaults.md | shipped RemoteConfig/Profile defaults + snapshot diffs |
| 13_decompiled_logic.md | pseudo-code walkthroughs of the big systems |
| raw/ , il2cpp/ , decompiled/ | raw dumps (CONTAIN SECRETS - do not share) |

## Gaps (always keep this section)
- what could not be found / needs a device / server-side
