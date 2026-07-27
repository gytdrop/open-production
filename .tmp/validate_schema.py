import json, os
with open(r'D:\IBM Project\Open_Production\docs\schema\production-document.schema.json') as f:
    s = json.load(f)
print('schema loaded OK')
print('top-level required:', s.get('required'))
defs = s.get('$defs', {})
print('defs:', list(defs.keys()))
print('size:', os.path.getsize(r'D:\IBM Project\Open_Production\docs\schema\production-document.schema.json'), 'bytes')
print('count of definitions:', len(defs))
