#!/usr/bin/env python3
"""Disassemble IL2CPP arm64 methods by name (small rule functions read like formulas).
usage: a64dis.py --so libil2cpp.so --script script.json 'Class$$Method' [...]
       a64dis.py --so ... --script ... --f32 0xVA [n]   # read n floats at a literal-pool VA
Name = suffix match against script.json 'Name'. Env GRE_SO / GRE_SCRIPT supply defaults."""
import json, sys, os, bisect, struct, argparse
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

ap = argparse.ArgumentParser()
ap.add_argument('--so', default=os.environ.get('GRE_SO'))
ap.add_argument('--script', default=os.environ.get('GRE_SCRIPT'))
ap.add_argument('--max', type=int, default=400, help='max instructions')
ap.add_argument('--f32', nargs='+', help='VA [count]: dump floats/ints at literal address')
ap.add_argument('names', nargs='*')
a = ap.parse_args()
if not a.so or not a.script: sys.exit('need --so and --script (or GRE_SO/GRE_SCRIPT)')
S = json.load(open(a.script))['ScriptMethod']
A = sorted({m['Address'] for m in S}); N = {m['Address']: m['Name'] for m in S}
f = open(a.so, 'rb'); elf = ELFFile(f)
segs = [(s['p_vaddr'], s['p_offset'], s['p_filesz']) for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
def rd(va, n):
    for v, o, sz in segs:
        if v <= va < v + sz:
            f.seek(o + va - v); return f.read(n)
cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
def dis(name):
    c = [m for m in S if m['Name'] == name or m['Name'].endswith(name)]
    if not c: return f'; {name}: not found'
    m = c[0]; ad = m['Address']; i = bisect.bisect_right(A, ad)
    end = A[i] if i < len(A) else ad + 0x400
    out = [f"; {m['Name']} @ {ad:#x} ({end-ad} bytes)", f"; {m['Signature']}"]
    for ins in cs.disasm(rd(ad, min(end - ad, a.max * 4)), ad):
        op = ins.op_str
        if ins.mnemonic in ('bl', 'b'):
            try:
                t = int(op.lstrip('#'), 16); op += ('  ; ' + N[t]) if t in N else ''
            except Exception: pass
        out.append(f'{ins.address:#x}: {ins.mnemonic} {op}')
    return '\n'.join(out)
if a.f32:
    va = int(a.f32[0], 16); n = int(a.f32[1]) if len(a.f32) > 1 else 4
    b = rd(va, n * 4)
    print('f32:', struct.unpack(f'<{n}f', b)); print('i32:', struct.unpack(f'<{n}i', b))
for n in a.names: print(dis(n), '\n')
