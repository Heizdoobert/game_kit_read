#!/usr/bin/env python3
"""Parse Unity IL2CPP global-metadata.dat (v24+ layout, tested v31) without Il2CppDumper.
Outputs string_literals.txt and types_dump.txt (type/field/method names). Fast first look, no .so needed.
usage: meta_parse.py global-metadata.dat outdir"""
import struct, sys, os
P, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
d = open(P, 'rb').read()
assert struct.unpack_from('<I', d, 0)[0] == 0xFAB11BAF, 'not il2cpp metadata'
ver = struct.unpack_from('<i', d, 4)[0]; print('metadata version', ver)
names = ['stringLiteral','stringLiteralData','string','events','properties','methods','paramDefVals','fieldDefVals',
         'fapDefData','fieldMarshaled','parameters','fields','genParams','genParamCons','genContainers','nested',
         'interfaces','vtable','ifaceOffsets','typeDefs']  # v31 order; verify counts look sane
H = {n: struct.unpack_from('<ii', d, 8 + i * 8) for i, n in enumerate(names)}
so, sz = H['string']; S = d[so:so + sz]
def s(i): return S[i:S.index(b'\0', i)].decode('utf8', 'replace')
lo, ls = H['stringLiteral']; ld, _ = H['stringLiteralData']
lits = []
for i in range(ls // 8):
    ln, di = struct.unpack_from('<II', d, lo + i * 8)
    lits.append(d[ld + di:ld + di + ln].decode('utf8', 'replace'))
open(f'{O}/string_literals.txt', 'w').write('\n'.join(l.replace('\n', '\\n') for l in lits))
to, ts = H['typeDefs']; fo = H['fields'][0]; mo = H['methods'][0]
out = []
for i in range(ts // 88):
    v = struct.unpack_from('<16i8H2I', d, to + i * 88)
    nm = (s(v[1]) + '.' if s(v[1]) else '') + s(v[0])
    out.append(f'T {nm} parent={v[4]} flags={v[7]:#x}')
    for f in range(v[18]):
        out.append(f'  F {s(struct.unpack_from("<iii", d, fo + (v[8] + f) * 12)[0])}')
    for m in range(v[16]):
        a = struct.unpack_from('<7i4H', d, mo + (v[9] + m) * 36); out.append(f'  M {s(a[0])}({a[10]})')
open(f'{O}/types_dump.txt', 'w').write('\n'.join(out))
print(ts // 88, 'types,', len(lits), 'literals ->', O)
