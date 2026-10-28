#!/usr/bin/env bash
# selftest.sh - offline smoke test of the analysis helpers on tiny fixtures (no APK/Ghidra needed). Exit 1 on failure.
K="$(cd "$(dirname "$0")/.." && pwd)"; B="$K/bin"; T="$K/templates/selftest"; export GRE_DUMP="$T/dump.cs" GRE_DECOMP="$T/decompiled"; bad=0
ok(){ if eval "$2" >/dev/null 2>&1; then echo "ok   $1"; else echo "FAIL $1"; bad=1; fi; }
ok "py_compile" "python3 -m py_compile $B/*.py"
ok "bash -n" "for f in $B/*.sh; do bash -n \$f || exit 1; done"
ok "fn names base+own fields" "[[ \$($B/fn.py 'Foo\$\$Hit') == *'this.hp < 1'* && \$($B/fn.py 'Foo\$\$Hit') == *'this.alive'* ]]"
ok "fn ambiguous -> error" "! $B/fn.py o"
ok "ctor_defaults float+bool" "[[ \$($B/ctor_defaults.py $T/decompiled/Demo.Foo\\\$\\\$.ctor.c Demo.Foo) == *'speed = 5.0'*'alive = True'* ]]"
ok "xref field write" "$B/xref.py -f Demo.Foo speed | grep -q 'W .*Hit'"
ok "xref field read" "$B/xref.py -f Demo.Foo hp | grep -q 'R .*Hit'"
ok "xref string" "$B/xref.py -s hit_msg | grep -q Hit"
ok "xref call" "$B/xref.py -c Log | grep -q Hit"
printf '{"cheat_password": "hunter2xx"}\n' > "${TMPDIR:-/tmp}/gre_secret.json"
ok "redact catches secret" "! python3 $B/redact.py --check ${TMPDIR:-/tmp}/gre_secret.json"
rm -f "${TMPDIR:-/tmp}/gre_secret.json"
[[ $bad == 0 ]] && echo "selftest PASS" || echo "selftest FAIL"; exit $bad
