#!/usr/bin/env python3
"""Field defaults from a decompiled .ctor: maps `*(T*)(this+0xOFF) = imm` to dump.cs field names.
usage: ctor_defaults.py <ctor.c> <dump.cs> <Namespace.Class>   (float bit patterns shown as floats)"""
import re,struct,sys
c,d,cls=sys.argv[1:4]
ns,_,name=cls.rpartition('.')
dump=open(d,errors='ignore').read()
m=re.search(r'// Namespace: %s\n(?:\[[^\n]*\n)*[^\n]*?\b(?:class|struct) %s\b[^\n]*\n\{.*?\n\}\n'%(re.escape(ns),re.escape(name)),dump,re.S)
body=m.group(0) if m else ''
F={int(o,16):(n,t.strip()) for t,n,o in re.findall(r'\n\t(?:public|private|protected|internal) (?:readonly )?([^\n(;=]+?) (\w+); // 0x([0-9A-F]+)',body)}
for l in open(c):
    g=re.search(r'\*\(\w+(?: \*)?\)\(param_1 \+ (0x[0-9a-f]+)\) = (0x[0-9a-f]+|\d+);',l)
    if not g: continue
    o=int(g.group(1),16); v=int(g.group(2),0); n,t=F.get(o,('?','?'))
    if t=='float': v=round(struct.unpack('<f',struct.pack('<I',v&0xffffffff))[0],5)
    elif t=='bool': v=bool(v)
    print(f"{o:#06x} {t:>12} {n} = {v}")
