"""Shared dump.cs helpers: instance-field table of a class (incl. base classes). Import-only."""
import re, os
_cache = {}
def dump_path():
    w = os.environ.get('GRE_WORK', '.')
    for p in (os.environ.get('GRE_DUMP'), f'{w}/il2cpp/dump.cs', f'{w}/tools/out_perfare/dump.cs'):
        if p and os.path.isfile(p): return p
def _text(p):
    if p not in _cache: _cache[p] = open(p, errors='ignore').read()
    return _cache[p]
def _block(t, cls):
    ns, _, name = cls.rpartition('.')
    for n, c in ((re.escape(ns), name), ('', cls), (r'[^\n]*', name)):   # nested types print with ns ''; base classes may be unqualified
        m = re.search(r'// Namespace: %s\n(?:\[[^\n]*\n)*([^\n]*?\b(?:class|struct) %s(?=[ :<])[^\n]*)\n\{(.*?)\n\}\n' % (n, re.escape(c)), t, re.S)
        if m: return m.group(1), m.group(2)
    return None, ''
def fields(cls, path=None, depth=6):
    """{offset: (name, type)} for instance fields of cls and its base chain; {} if unknown."""
    p = path or dump_path()
    if not p or depth < 0: return {}
    t = _text(p); head, body = _block(t, cls)
    if head is None: return {}
    F = {}
    b = re.search(r':\s*([\w.<>`]+)', head.split('//')[0])
    if b and b.group(1) not in ('object', 'System.Object', 'ValueType'):
        F.update(fields(b.group(1), p, depth - 1))
    for ty, n, o in re.findall(r'\n\t(?:public|private|protected|internal)(?: readonly)? ([^\n(;=]+?) (\w+); // 0x([0-9A-F]+)', body):
        if not ty.startswith(('static', 'const')): F[int(o, 16)] = (n, ty.strip())
    return F
