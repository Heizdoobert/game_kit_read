#!/usr/bin/env python3
"""Field defaults from a decompiled .ctor: maps `*(T*)(this+0xOFF) = imm` to dump.cs field names.
usage: ctor_defaults.py <ctor.c> <Namespace.Class>   (float bit patterns shown as floats; dump.cs from GRE_DUMP / GRE_WORK)"""
import re, struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dump
a = sys.argv[1:]
if len(a) != 2: sys.exit(__doc__)
c, cls = a; F = _dump.fields(cls)
if not F: sys.exit(f'class {cls} not found in dump.cs (set GRE_DUMP)')
for l in open(c):
    g = re.search(r'\*\(\w+(?: \*)?\)\(param_1 \+ (0x[0-9a-f]+)\) = (0x[0-9a-f]+|\d+);', l)
    if not g: continue
    o = int(g.group(1), 16); v = int(g.group(2), 0); n, t = F.get(o, ('?', '?'))
    if t == 'float': v = round(struct.unpack('<f', struct.pack('<I', v & 0xffffffff))[0], 5)
    elif t == 'bool': v = bool(v)
    print(f"{o:#06x} {t:>12} {n} = {v}")
