"""Verify Codex scaffolding: every Python file parses, gates work, Makefile uses tabs."""
import ast
import sys
from pathlib import Path

ROOT = Path(r"D:\IBM Project\Open_Production")
PY_FILES = [
    ROOT / "src" / "agents" / "base.py",
    ROOT / "src" / "tools" / "llm_client.py",
    ROOT / "src" / "validation" / "gates.py",
    ROOT / "tests" / "conftest.py",
    ROOT / "scripts" / "run_demo.py",
]

# 1. ast.parse on every Python file
for p in PY_FILES:
    src = p.read_text(encoding="utf-8")
    ast.parse(src)
    print(f"[OK] ast.parse: {p.relative_to(ROOT)} ({len(src.splitlines())} lines)")

# 2. Smoke-test the gate classes (matches Codex's ALL_CONTRACTS_OK claim)
sys.path.insert(0, str(ROOT / "src"))
from validation.gates import EvidenceGate, ConsistencyGate, PublicationGate  # noqa: E402
from agents.base import BaseAgent  # noqa: E402
from tools.llm_client import MockLLMClient  # noqa: E402

eg = EvidenceGate()
assert eg.process({"source_ids": ["s1"]})["status"] == "accepted"
assert eg.process({"source_ids": []})["status"] == "rejected"
assert eg.process({})["status"] == "rejected"
print("[OK] EvidenceGate")

cg = ConsistencyGate()
claims = [
    {"fact_id": "f1", "conclusion": "yes"},
    {"fact_id": "f1", "conclusion": "no"},
    {"fact_id": "f2", "conclusion": "yes"},
    {"fact_id": "f2", "conclusion": "yes"},  # same conclusion, no contradiction
]
assert len(cg.find_contradictions(claims)) == 1
assert cg.find_contradictions([]) == []
print("[OK] ConsistencyGate")

pg = PublicationGate()
ok, msg = pg.check({"doi": "x", "authors": "y", "date": "z"})
assert ok and msg == "ok"
ok, msg = pg.check({"doi": "x", "authors": "y"})
assert (not ok) and "date" in msg
print("[OK] PublicationGate")

ba = BaseAgent("test")
try:
    ba.run({})
except NotImplementedError:
    pass
else:
    raise AssertionError("BaseAgent.run should raise NotImplementedError")
print("[OK] BaseAgent")

ml = MockLLMClient()
assert ml.complete("hi") != ml.response  # default response: a three-angle JSON fallback
ml_pinned = MockLLMClient(response='hello world')
assert ml_pinned.complete("hi") == 'hello world'  # pinned response: returned verbatim
print("[OK] MockLLMClient")

# 3. Verify Makefile uses tabs (not spaces)
mk = (ROOT / "Makefile").read_bytes()
text = mk.decode("utf-8")
# Check that body lines start with a tab, not spaces
for i, line in enumerate(text.splitlines()[1:], start=2):
    if line and line[0] == " ":
        print(f"[FAIL] Makefile line {i} uses spaces, not tabs: {line!r}")
        sys.exit(1)
print("[OK] Makefile uses tabs")

print("\nALL_CONTRACTS_OK")