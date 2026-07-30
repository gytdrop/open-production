import os, re
import sys
sys.path.insert(0, "src")
from agents.base import BaseAgent
allowlist = set()
import inspect
src = inspect.getsource(BaseAgent._enforce_scope)
import re
m = re.search("always_ok\s*=\s*\{([^}]+)\}", src)
if m:
    for tok in re.findall("(\^"]+)", m.group(1)):
        allowlist.add(tok)
print("always_ok has", len(allowlist), "entries")
agents = sorted([f for f in os.listdir("src/agents") if f.endswith(".py") and f not in ("base.py", "__init__.py", "confirm_gate.py", "story.py", "script.py")])
leakage = {}
for fname in agents:
    path = "src/agents/" + fname
    src = open(path, encoding="utf-8").read()
    wf_match = re.search("WRITABLE_FIELDS[^=]*=\s*f?rozenset\(\s*\{([^}]*)\}", src)
    writable = set()
    if wf_match:
        for tok in re.findall("(\^"]+)", wf_match.group(1)):
            writable.add(tok)
    keys_emitted = set()
    for m2 in re.finditer("return\s*\{", src):
        start = m2.end()
        depth = 1
        i = start
        while i < len(src) and depth > 0:
            if src[i] == chr(123): depth += 1
            elif src[i] == chr(125): depth -= 1
            i += 1
        block = src[start:i-1]
        for k in re.findall("("[a-zA-Z_][a-zA-Z0-9_]*")\s*:", block):
            keys_emitted.add(k)
    needs_allow = keys_emitted - allowlist - {k.split(".")[-1] for k in writable} - {k for k in keys_emitted if k.startswith("_")}
    if needs_allow:
        leakage[fname] = needs_allow
print("=== Agents emitting keys NOT in always_ok and NOT in WRITABLE_FIELDS ===")
for f, ks in sorted(leakage.items()):
    print(f + ": " + str(sorted(ks)))
