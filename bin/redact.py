#!/usr/bin/env python3
"""Find/mask secrets in text/JSON outputs so knowledge bases can be shared.
  redact.py --check DIR [DIR..]     report suspicious hits (exit 1 if any)
  redact.py --apply DIR [DIR..]     mask in place (keeps first 0 chars: <REDACTED>)
Heuristic: values of keys named *password|secret|token|api_key|apikey|product_key|private|auth*, JSON-in-string forms,
and decompiler labels STR_<n>_<value>. ALWAYS eyeball the report: raw/il2cpp dumps legitimately keep originals -> don't publish those dirs."""
import re, sys, os, json
KEY = r'(?:password|passwd|secret|token|api[_-]?key|product[_-]?key|private[_-]?key|auth|credential|test_connection)'
PATS = [
    re.compile(r'(?i)("?[\w.]*' + KEY + r'[\w.]*"?\s*[:=]\s*\\?")([^"\\\n]{4,})(\\?")'),   # "key": "value"
    re.compile(r'(?i)(\b[\w.]*' + KEY + r'[\w.]*\s*=\s*)("?)([^\s";]{4,})'),               # key = value
]
def redact_text(s):
    s = PATS[0].sub(lambda m: m.group(1) + '<REDACTED>' + m.group(3), s)
    return s
def redact_obj(o, kn=None):
    if isinstance(o, dict):
        return {k: ('<REDACTED>' if isinstance(v, str) and re.search(KEY, k, re.I) and len(v) >= 4 else redact_obj(v, k)) for k, v in o.items()}
    if isinstance(o, list): return [redact_obj(v) for v in o]
    if isinstance(o, str): return redact_text(o) if ('"' in o) else o
    return o
def scan(paths, apply, excl=()):
    hits = 0
    for root in paths:
        for dp, ds, fs in os.walk(root):
            ds[:] = [d for d in ds if d not in excl]
            for f in fs:
                p = os.path.join(dp, f)
                try: t = open(p, encoding='utf8').read()
                except Exception: continue
                n = 0
                for pat in PATS[:1]:
                    for m in pat.finditer(t):
                        if m.group(2).lower().startswith('<redacted'): continue
                        n += 1
                        if not apply: print(f'{p}: {m.group(1).strip()[:40]}...')
                if n:
                    hits += n
                    if apply: open(p, 'w', encoding='utf8').write(redact_text(t))
    return hits
if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('--check', '--apply'): sys.exit(__doc__)
    args = sys.argv[2:]; excl = ()
    if '--exclude' in args:
        i = args.index('--exclude'); excl = tuple(args[i + 1].split(',')); del args[i:i + 2]
    h = scan(args, sys.argv[1] == '--apply', excl); print('hits:', h); sys.exit(1 if (h and sys.argv[1] == '--check') else 0)
