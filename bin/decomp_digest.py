#!/usr/bin/env python3
"""Digest decompiled .c files (from ghidra_decomp.sh) into readable per-class markdown:
per method: size, callees (decompiler-named IL2CPP functions), string literals (STR_n_ labels), float/int literals, field offsets touched.
Use it to skim a system fast, then open the .c of interesting methods.
usage: decomp_digest.py DECOMP_DIR OUT.md [--class-regex REGEX] [--min-lines N]"""
import re, os, sys, collections
d, out = sys.argv[1], sys.argv[2]
cre = re.compile(sys.argv[sys.argv.index('--class-regex') + 1]) if '--class-regex' in sys.argv else None
minl = int(sys.argv[sys.argv.index('--min-lines') + 1]) if '--min-lines' in sys.argv else 8
call = re.compile(r'\b((?:[A-Z][A-Za-z0-9_]*_){1,}_[A-Za-z0-9_]+)\s*\(')
strl = re.compile(r'STR_\d+_([A-Za-z0-9_]+)')
flt = re.compile(r'(?<![\w.])(\d+\.\d+(?:e[-+]?\d+)?)(?:f)?\b')
off = re.compile(r'\+ 0x([0-9a-f]{2,3})\)')
bycls = collections.defaultdict(list)
for f in sorted(os.listdir(d)):
    if not f.endswith('.c'): continue
    cls, _, m = f[:-2].partition('$$')
    if cre and not cre.search(cls): continue
    t = open(os.path.join(d, f), errors='replace').read()
    body = t.split('\n', 2)[-1]; n = body.count('\n')
    if n < minl: continue
    calls = list(dict.fromkeys(c for c in call.findall(body) if not c.startswith(('FUN_', 'thunk')))) 
    strs = list(dict.fromkeys(strl.findall(body)))
    flts = list(dict.fromkeys(flt.findall(body)))[:12]
    offs = sorted(set(off.findall(body)))[:14]
    bycls[cls].append((m, n, calls, strs, flts, offs))
with open(out, 'w') as o:
    for cls, ms in bycls.items():
        o.write(f'\n## {cls}\n')
        for m, n, calls, strs, flts, offs in sorted(ms, key=lambda x: -x[1]):
            o.write(f'### {m} ({n} lines)\n')
            if calls: o.write('- calls: ' + ', '.join(c.replace('_','.',1) for c in calls[:25]) + '\n')
            if strs: o.write('- strings: ' + ', '.join(strs[:10]) + '\n')
            if flts: o.write('- floats: ' + ', '.join(flts) + '\n')
            if offs: o.write('- field offsets: ' + ', '.join('0x' + x for x in offs) + '\n')
print('classes', len(bycls), '->', out)
