#!/usr/bin/env python3
"""Print a Ghidra .c compactly (token saver): drops decls, il2cpp init guards, stack noise; names `this[0xOFF]` fields from dump.cs.
usage: fn.py <file.c | Class$$Method> [DIR] [-n MAXLINES]
  exact `Class$$Method` (or bare `Method` if unique) wins; several matches -> lists them, pick one. DIR defaults to $GRE_DECOMP or ./decompiled.
  field names need dump.cs (auto: $GRE_DUMP, $GRE_WORK/il2cpp/dump.cs, $GRE_WORK/tools/out_perfare/dump.cs)."""
import re, sys, glob, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dump
ap = argparse.ArgumentParser(usage=__doc__); ap.add_argument('target'); ap.add_argument('dir', nargs='?')
ap.add_argument('-n', type=int, default=400)
o = ap.parse_args(); d = o.dir or os.environ.get('GRE_DECOMP', 'decompiled')
if os.path.isfile(o.target): f = o.target
else:
    g = sorted(glob.glob(f'{d}/*{o.target}*.c'))
    ex = [x for x in g if os.path.basename(x)[:-2] == o.target or os.path.basename(x)[:-2].endswith('$$' + o.target)]
    g = ex if len(ex) >= 1 else g
    if not g: sys.exit('not found: ' + o.target)
    if len(g) > 1: sys.exit(f'{len(g)} matches, be specific:\n' + '\n'.join('  ' + os.path.basename(x)[:-2] for x in g[:25]) + ('\n  ...' if len(g) > 25 else ''))
    f = g[0]
cls = os.path.basename(f).split('$$')[0]
F = _dump.fields(cls)
decl = re.compile(r'^\s+(?:undefined\d*|float|double|long|ulong|int|uint|short|ushort|char|byte|bool|code|void|\w+_o)\s*\**\s*[\w\[\] ,*]+;\s*$')
def field(m):
    n = F.get(int(m.group(1), 16)); return f'this.{n[0]}' if n else f'this[{m.group(1)}]'
out = []; skip = 0
for l in open(f):
    l = l.rstrip()
    if decl.match(l) or not l.strip(): continue
    if re.match(r'^\s+if \(\(b?Ram\w+ & 1\) == 0\) \{', l): skip = 1; continue
    if skip:
        if l.strip() == '}': skip = 0
        continue
    if re.search(r'\b(?:u|f)?Stack_\w+ = |extraout_|unaff_', l) and '=' in l and '(' not in l: continue
    l = re.sub(r'PTR_STR_\d+_(\w+?)_0[0-9a-f]{7}', r'"\1"', l); l = re.sub(r'PTR_DAT_0[0-9a-f]{7}', 'KLASS', l)
    l = re.sub(r'\((?:undefined\d?|float|long|ulong|int|uint|char|bool|byte|code) ?\*+\)', '', l)
    l = re.sub(r'\b(?:UnityEngine|Unity_FPS_Gameplay|Chameleon\w*?)_(\w+?)__(?=\w)', r'\1.', l)
    l = re.sub(r'\(param_1 \+ (0x[0-9a-f]+)\)', field, l); l = re.sub(r'\*this([.\[])', r'this\1', l)
    if l.startswith('//'): continue
    out.append(l)
print(f'# {os.path.basename(f)} ({len(out)} lines{", fields named" if F else ""})'); print('\n'.join(out[:o.n]))
if len(out) > o.n: print(f'... +{len(out) - o.n} more (-n)')
