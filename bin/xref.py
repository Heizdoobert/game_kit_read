#!/usr/bin/env python3
"""Cross-reference decompiled .c files (token saver vs grep -r): who touches a field / uses a string / calls a function.
usage: xref.py -f Class FIELD|0xOFF   methods of Class using that field (W = written, R = read only)
       xref.py -s REGEX               methods whose string literals (STR_n_<text>) match
       xref.py -c REGEX               methods calling a function matching REGEX
  [-d DIR]  (default $GRE_DECOMP or ./decompiled)   [-m MAX] (default 40)"""
import re, sys, os, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dump
ap = argparse.ArgumentParser(usage=__doc__)
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument('-f', nargs=2, metavar=('CLASS', 'FIELD')); g.add_argument('-s'); g.add_argument('-c')
ap.add_argument('-d', default=os.environ.get('GRE_DECOMP', 'decompiled')); ap.add_argument('-m', type=int, default=40)
o = ap.parse_args(); hits = []
if o.f:
    cls, fld = o.f
    if fld.lower().startswith('0x'): off = int(fld, 16)
    else:
        F = {n: k for k, (n, _) in _dump.fields(cls).items()}
        if fld not in F: sys.exit(f'field {fld} not in {cls}: ' + ', '.join(sorted(F)[:30]))
        off = F[fld]
    pat = re.compile(r'\(param_1 \+ %#x\)(\s*=[^=])?' % off); files = glob.glob(f'{o.d}/{cls}$$*.c')
else:
    pat = re.compile(r'STR_\d+_\w*(?:%s)' % o.s if o.s else r'\b\w*(?:%s)\w*\s*\(' % o.c); files = glob.glob(f'{o.d}/*.c')
for f in sorted(files):
    ms = list(pat.finditer(open(f, errors='replace').read()))
    if ms: hits.append((os.path.basename(f)[:-2], 'W' if o.f and any(m.group(1) for m in ms) else ('R' if o.f else str(len(ms)))))
for n, t in hits[:o.m]: print(f'{t:>2} {n}')
print(f'{len(hits)} methods' + (f' (showing {o.m})' if len(hits) > o.m else ''))
