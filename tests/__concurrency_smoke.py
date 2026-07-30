import sys, threading, shutil
from pathlib import Path
import tempfile

# Resolve repo root + src directory relative to this file so the script
# works regardless of the CWD it is launched from.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_SRC = _ROOT / 'src'
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
del _p
d = Path(tempfile.mkdtemp())
from src.service.production_service import ProductionService
from src.schema.production_document import IntentDocument

svc = ProductionService(storage_dir=d)
p = svc.init('concurrent test', intent=IntentDocument(topic='X'))

errors = []
def save_loop():
    for i in range(50):
        try:
            svc.save(p)
        except Exception as exc:
            errors.append(('save', type(exc).__name__, str(exc)[:80]))
            return

def status_loop():
    for i in range(50):
        try:
            svc.status(p.id)
        except Exception as exc:
            errors.append(('status', type(exc).__name__, str(exc)[:80]))

t1 = threading.Thread(target=save_loop)
t2 = threading.Thread(target=status_loop)
t1.start(); t2.start(); t1.join(); t2.join()
print('Errors:', errors)
print('Production state:', p.state)
print('Productions on disk:', len(svc.list_productions()))
shutil.rmtree(d, ignore_errors=True)