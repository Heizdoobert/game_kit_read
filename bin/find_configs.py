#!/usr/bin/env python3
"""Hunt remote-config / balance data in dumps. Finds (1) RemoteConfig-like lists {key,defaultValue}, (2) JSON blobs in strings,
(3) numeric-heavy ScriptableObjects. usage: find_configs.py DIR_OF_JSON [--grep price,reward,limit]"""
import json, os, sys, re
root = sys.argv[1]; kw = (sys.argv[sys.argv.index('--grep') + 1].split(',') if '--grep' in sys.argv else ['price','reward','limit','cooldown','duration','damage','speed','chance','interval'])
for dp, _, fs in os.walk(root):
    for f in sorted(fs):
        if not f.endswith('.json'): continue
        try: d = json.load(open(os.path.join(dp, f)))
        except Exception: continue
        s = json.dumps(d)
        if re.search(r'"defaultValue"', s) and re.search(r'"key"', s): print('REMOTECONFIG-LIKE', f)
        hit = sorted({k for k in kw if re.search(k, s, re.I)})
        nums = len(re.findall(r'[:\[,]\s*-?\d+\.?\d*', s))
        if hit and nums > 5: print(f'{f[:90]:90} nums={nums} kw={",".join(hit)}')
