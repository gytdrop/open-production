import sys, json, pathlib, tempfile
sys.path.insert(0, r"src")
import jsonschema
from jsonschema import Draft202012Validator
schema = json.loads(pathlib.Path("docs/schema/production-document.schema.json").read_text(encoding="utf-8"))
validator = Draft202012Validator(schema)

from src.service.production_service import ProductionService
from src.schema.production_document import IntentDocument
d = pathlib.Path(tempfile.mkdtemp())
svc = ProductionService(storage_dir=d)
prod = svc.init("test schema", intent=IntentDocument(topic="X"))
prod_dict = svc.status(prod.id)
print("Top-level fields:", sorted(prod_dict.keys()))
print("Field types:")
for k, v in prod_dict.items():
    print("  ", k, "=", type(v).__name__)
print()
print("Validation errors:")
errors = sorted(validator.iter_errors(prod_dict), key=lambda e: list(e.relative_path))
for e in errors[:10]:
    path = "/".join(str(p) for p in e.relative_path) or "<root>"
    print("  at", path, ":", e.message[:120])