import sys
from pathlib import Path as _Path
_HERE = _Path(__file__).resolve().parent
_ROOT = _HERE.parent
_SRC = _ROOT / 'src'
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
del _p
from src.agents.creative_reframing import CreativeReframing
from src.tools.llm_client import MockLLMClient

# Use json.dumps for safe quoting
import json
CASES = [
    ('garbage',        'sdlfjsldkjf'),
    ('empty',          ''),
    ('null',           'null'),
    ('list-not-dict',  '[1,2]'),
    ('wrong-key',      json.dumps({'foo': 1})),
    ('wrong-angles',   json.dumps({'angles': 'oops'})),
    ('partial',        json.dumps({'angles': [{'id': 'skeptic'}]})),
    ('missing-fields', json.dumps({'angles': [{'id': 'x', 'name': 'X'}]})),
    ('only-2-angles',  json.dumps({'angles': [
        {'id': 'skeptic', 'name': 'S', 'summary': 's', 'questions_to_address': ['a'], 'risk_focus': 'r'},
        {'id': 'advocate', 'name': 'A', 'summary': 'a', 'questions_to_address': ['a'], 'risk_focus': 'r'}
    ]})),
]
for label, response in CASES:
    try:
        a = CreativeReframing(llm=MockLLMClient(response=response))
        out = a.run({'topic': 'AI'})
        ids = [x['id'] for x in out['angles']]
        print(label, '->', len(out['angles']), 'angles', ids)
    except Exception as exc:
        print(label, '-> RAISED', type(exc).__name__, str(exc)[:80])