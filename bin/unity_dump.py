#!/usr/bin/env python3
"""Dump Unity MonoBehaviour/ScriptableObject data to JSON (secrets auto-redacted).
  unity_dump.py --bundles <apk>/assets/aa/Android --out DIR            Addressables bundles (typetrees kept -> easy)
  unity_dump.py --data <apk>/assets/bin/Data/data.unity3d --dummydll <il2cpp>/DummyDll --out DIR
        built-in data (typetrees stripped): script class resolved via MonoScript, fields via DummyDll TypeTreeGenerator.
  --only ClassA,ClassB   keep only those script classes
Output file: <out>/<container>__<ScriptClass>__<name>__<pathid>.json ; bundle_summary.json (object type counts)."""
import UnityPy, json, os, glob, collections, struct, argparse, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from redact import redact_obj
ap = argparse.ArgumentParser()
ap.add_argument('--bundles'); ap.add_argument('--data'); ap.add_argument('--dummydll')
ap.add_argument('--out', required=True); ap.add_argument('--only'); ap.add_argument('--unity', default='6000.0.63f1')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
only = set(a.only.split(',')) if a.only else None
def safe(o): return json.loads(json.dumps(o, default=str))
def save(cont, cls, tr, pid):
    nm = (tr.get('m_Name') or f'obj{pid}')
    fn = f'{cont[:30]}__{cls}__{nm}__{pid}.json'.replace('/', '_')[:180]
    json.dump(redact_obj(safe(tr)), open(os.path.join(a.out, fn), 'w'), ensure_ascii=False, indent=1)
summary = {}
if a.bundles:
    for f in sorted(glob.glob(os.path.join(a.bundles, '*.bundle'))):
        b = os.path.basename(f); cnt = collections.Counter(); n = 0
        try: env = UnityPy.load(f)
        except Exception as e: print('FAIL', b, e); continue
        for o in env.objects:
            cnt[o.type.name] += 1
            if o.type.name != 'MonoBehaviour': continue
            try: tr = o.read_typetree()
            except Exception: continue
            cls = ''
            try: cls = o.read().m_Script.read().m_ClassName
            except Exception: pass
            if only and cls not in only: continue
            save(b.split('_all_')[0], cls, tr, o.path_id); n += 1
        summary[b] = {'types': dict(cnt), 'mono_exported': n}; print(b, n, flush=True)
if a.data:
    from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
    env = UnityPy.load(a.data)
    g = TypeTreeGenerator(a.unity); g.load_local_dll_folder(a.dummydll); env.typetree_generator = g
    scr = {}
    for o in env.objects:
        if o.type.name == 'MonoScript':
            try: scr[o.path_id] = o.read(check_read=False).m_ClassName
            except Exception: pass
    n = 0; cnt = collections.Counter()
    for o in env.objects:
        if o.type.name != 'MonoBehaviour': continue
        # MonoBehaviour header: GameObject PPtr(12) + enabled(4) + Script PPtr: file_id@16 path_id@20
        cls = scr.get(struct.unpack_from('<q', o.get_raw_data(), 20)[0], '?'); cnt[cls] += 1
        if only and cls not in only: continue
        if not only and cls in ('Image','Button','Text','TextMeshProUGUI','LayoutElement','Toggle','StyleComponent'): continue  # UI noise
        try: tr = o.read_typetree()
        except Exception: continue
        save('data', cls, tr, o.path_id); n += 1
    summary['data.unity3d'] = {'script_classes': dict(cnt.most_common()), 'mono_exported': n}; print('data.unity3d', n)
json.dump(summary, open(os.path.join(a.out, 'bundle_summary.json'), 'w'), indent=1)
