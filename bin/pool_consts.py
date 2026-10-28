#!/usr/bin/env python3
"""Float/int constants a method loads: literal-pool ldr, fmov #imm, mov/movk pairs.
usage: GRE_SO=.. GRE_SCRIPT=.. python pool_consts.py 'Class$$Method' [...]   (or regex with -r)
Bounds = next method address, so tail-call neighbours can bleed in: check the printed size."""
import json,os,re,struct,sys,bisect
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
SO=os.environ.get('GRE_SO','apk_extract/lib/arm64-v8a/libil2cpp.so')
SC=os.environ.get('GRE_SCRIPT','tools/out_perfare/script.json')
S=json.load(open(SC))['ScriptMethod']; A=sorted({m['Address'] for m in S}); N={m['Address']:m['Name'] for m in S}
f=open(SO,'rb'); segs=[(s['p_vaddr'],s['p_offset'],s['p_filesz']) for s in ELFFile(f).iter_segments() if s['p_type']=='PT_LOAD']
def rd(va,n):
    for v,o,sz in segs:
        if v<=va<v+sz: f.seek(o+va-v); return f.read(n)
cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM); cs.detail=False
def fl(b): return struct.unpack('<f',struct.pack('<I',b&0xffffffff))[0]
def sane(x): return x==x and (x==0 or 1e-6<abs(x)<1e7)
def run(m):
    a=m['Address']; i=bisect.bisect_right(A,a); end=A[i] if i<len(A) else a+0x400
    print(f"== {m['Name']} @ {a:#x} ({end-a} B)")
    regs={}; pages={}; seen=set()
    for ins in cs.disasm(rd(a,end-a),a):
        mn,op=ins.mnemonic,ins.op_str; v=None
        if mn=='ldr' and re.match(r'[swdx]\d+, #0x',op):
            r,t=op.split(', #'); t=int(t,16); sz=8 if r[0] in 'dx' else 4
            b=rd(t,sz)
            if b: v=(struct.unpack('<d',b)[0] if r[0]=='d' else fl(struct.unpack('<I',b)[0]) if r[0]=='s' else struct.unpack('<Q' if sz==8 else '<I',b)[0])
        elif mn=='adrp':
            r,t=op.split(', #'); pages[r]=int(t,16)
        elif mn in('ldr','ldp') and '[x' in op and ', #' in op and 'x' in op.split('[')[1]:
            m2=re.search(r'\[(x\d+), #(0x[0-9a-f]+|\d+)\]',op)
            if m2 and m2.group(1) in pages and op[0] in 'sd':
                b=rd(pages[m2.group(1)]+int(m2.group(2),0),8 if op[0]=='d' else 4)
                if b: v=struct.unpack('<d',b)[0] if op[0]=='d' else fl(struct.unpack('<I',b)[0])
        elif mn=='fmov' and '#' in op: v=float(op.split('#')[1])
        elif mn=='mov' and re.match(r'w\d+, #',op):
            r,t=op.split(', #'); regs[r]=int(t,0)&0xffffffff
            if regs[r]>0xffff and sane(fl(regs[r])): v=fl(regs[r])
        elif mn=='movk' and re.match(r'w\d+, #',op):
            r=op.split(',')[0]; t=op.split('#')[1].split(',')[0]; sh=16 if 'lsl #16' in op else 0
            if r in regs: regs[r]=(regs[r]&~(0xffff<<sh))|(int(t,0)<<sh); x=fl(regs[r])
            else: continue
            if sh==16 and sane(x): v=x
        if isinstance(v,float) and not sane(v): continue
        if v is not None and (ins.address,v) not in seen:
            seen.add((ins.address,v)); print(f"{ins.address:#x}  {v:.6g}" if isinstance(v,float) else f"{ins.address:#x}  {v}")
if __name__=='__main__':
    rx=sys.argv[1]=='-r'; args=sys.argv[2:] if rx else sys.argv[1:]
    for n in args:
        ms=[m for m in S if (re.search(n,m['Name']) if rx else m['Name']==n or m['Name'].endswith(n))]
        for m in ms[:200]: run(m)
