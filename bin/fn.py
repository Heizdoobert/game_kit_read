#!/usr/bin/env python3
"""Print a Ghidra .c compactly (token saver): drops local declarations, il2cpp init guards, stack/extraout noise.
usage: fn.py <file.c|Class$$Method substring> [decompiled_dir] [-n MAXLINES]"""
import re,sys,glob,os
a=[x for x in sys.argv[1:] if x!='-n']; mx=int(os.environ.get('N','400'))
if '-n' in sys.argv: mx=int(sys.argv[sys.argv.index('-n')+1]); a=[x for x in a if x!=str(mx)]
t=a[0]; d=a[1] if len(a)>1 else os.environ.get('GRE_DECOMP','decompiled')
f=t if os.path.isfile(t) else (glob.glob(f'{d}/*{t}*.c') or [None])[0]
if not f: sys.exit('not found: '+t)
decl=re.compile(r'^\s+(?:undefined\d*|float|double|long|ulong|int|uint|short|ushort|char|byte|bool|code|void|\w+_o)\s*\**\s*[\w\[\] ,*]+;\s*$')
out=[];skip=0
for l in open(f):
    l=l.rstrip()
    if decl.match(l) or not l.strip(): continue
    if re.match(r'^\s+if \(\(b?Ram\w+ & 1\) == 0\) \{',l): skip=1; continue
    if skip:
        if l.strip()=='}': skip=0
        continue
    if re.search(r'\b(?:u|f)?Stack_\w+ = |extraout_|unaff_',l) and '=' in l and '(' not in l: continue
    l=re.sub(r'PTR_STR_\d+_(\w+?)_0[0-9a-f]{7}',r'"\1"',l); l=re.sub(r'PTR_DAT_0[0-9a-f]{7}','KLASS',l)
    l=re.sub(r'\((?:undefined\d?|float|long|ulong|int|uint|char|bool|byte|code) ?\*+\)','',l)
    l=re.sub(r'\b(?:UnityEngine|Unity_FPS_Gameplay|Chameleon\w*?)_(\w+?)__(?=\w)',r'\1.',l)
    l=re.sub(r'\(param_1 \+ (0x[0-9a-f]+)\)',r'this[\1]',l); l=re.sub(r'\*this\[',r'this[',l)
    if l.startswith('//'): continue
    out.append(l)
print(f'# {os.path.basename(f)} ({len(out)} lines)'); print('\n'.join(out[:mx]))
if len(out)>mx: print(f'... +{len(out)-mx} more (-n)')
