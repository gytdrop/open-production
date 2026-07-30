"""Crew demonstration script — runs all 6 live agents in sequence.

Demonstrates the production crew model (§26 differentiator #3) by running:
  1. CreativeReframing     — proposes 3 creative angles
  2. ShotDesignerAgent     — designs camera/lighting for a shot
  3. CharacterDirectorAgent— proposes 3 visual interpretations of Elena
  4. StoryboardArtistAgent — generates an ASCII frame for the designed shot
  5. ReviewerAgent         — evaluates the shot against a ConsistencyContract
  6. EditorAgent           — proposes 3 cut assemblies

Records every agent action in a ProductionService audit trail.

Usage: python examples/run_crew_demo.py
Output: output/crew_demo/crew_audit.jsonl (6+ entries)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agents.character_director import CharacterDirectorAgent
from agents.creative_reframing import CreativeReframing
from agents.editor import EditorAgent
from agents.reviewer import ReviewerAgent
from agents.shot_designer import ShotDesignerAgent
from agents.storyboard_artist import StoryboardArtistAgent
from tools.llm_client import ResearchMockLLMClient
from schema.production_document import AuditEntry, IntentDocument, utc_now_iso
from service.production_service import ProductionService

TOPIC = "The cost of AI-generated content on human creative work"
AUDIENCE = "educated_lay"
TONE = "contrarian"

OUT_DIR = ROOT / "output" / "crew_demo"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_entry(agent_name: str, operation: str, result: dict) -> dict:
    """Build a structured crew log entry."""
    return {
        "ts": _now(),
        "actor": agent_name,
        "operation": operation,
        "decision_status": result.get("verdict", result.get("severity", "proposed")),
        "summary": _summarise(agent_name, result),
        "payload": result,
    }


def _summarise(agent: str, result: dict) -> str:
    if agent == "creative_reframing":
        angles = result.get("angles", [])
        return f"Proposed {len(angles)} angles: {', '.join(a['id'] for a in angles)}"
    if agent == "shot_designer_agent":
        proposals = result.get("proposals", [])
        return f"Proposed {len(proposals)} shot setups: {', '.join(p['label'] for p in proposals)}"
    if agent == "character_director_agent":
        proposals = result.get("proposals", [])
        return f"Proposed {len(proposals)} character interpretations"
    if agent == "storyboard_artist_agent":
        return f"Storyboard: {result.get('composition_description', '')[:60]}..."
    if agent == "reviewer_agent":
        return f"Verdict={result.get('verdict')} score={result.get('score')} blocking={result.get('blocking')}"
    if agent == "editor_agent":
        proposals = result.get("proposals", [])
        return f"Proposed {len(proposals)} cut assemblies: {', '.join(p['label'] for p in proposals)}"
    return str(result)[:80]


def _new_evt_id() -> str:
    import uuid
    return f"evt_{uuid.uuid4().hex[:12]}"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audit: list[dict] = []

    # ── Bootstrap a ProductionService for character write-back (Stage 8) ───
    svc = ProductionService(storage_dir=OUT_DIR / "service")
    prod = svc.init(
        name=TOPIC[:80],
        intent=IntentDocument(topic=TOPIC, audience=AUDIENCE, tone=TONE),
    )

    print(f"\n{'='*60}")
    print("Open Production — Crew Demo")
    print(f"Topic: {TOPIC}")
    print(f"{'='*60}\n")

    # ── Agent 1: CreativeReframing ──────────────────────────────────────────
    print("[1/6] CreativeReframing — proposing 3 angles...")
    llm = ResearchMockLLMClient()
    agent1 = CreativeReframing(llm=llm)
    result1 = agent1.run({"topic": TOPIC, "audience": AUDIENCE, "tone": TONE})
    entry1 = _log_entry("creative_reframing", "propose_angles", result1)
    audit.append(entry1)
    chosen_angle = result1["angles"][0]
    print(f"   → Angles: {', '.join(a['id'] for a in result1['angles'])}")
    print(f"   → Chosen: {chosen_angle['id']} — {chosen_angle['summary']}\n")

    # ── Agent 2: ShotDesignerAgent ──────────────────────────────────────────
    print("[2/6] ShotDesignerAgent — designing opening shot...")
    agent2 = ShotDesignerAgent()
    result2 = agent2.run({
        "shot_id": "shot-001",
        "shot_intent": "contrarian opening — technology as unseen threat",
        "production_brief": {"tone": TONE, "creative_direction": chosen_angle["id"]},
    })
    entry2 = _log_entry("shot_designer_agent", "design_shot", result2)
    audit.append(entry2)
    chosen_shot = result2["proposals"][0]
    print(f"   → Proposals: {', '.join(p['label'] for p in result2['proposals'])}")
    print(f"   → Chosen: {chosen_shot['label']} — {chosen_shot['rationale']}\n")

    # ── Agent 3: CharacterDirectorAgent ────────────────────────────────────
    print("[3/6] CharacterDirectorAgent — creating character 'Elena'...")
    agent3 = CharacterDirectorAgent()
    result3 = agent3.run({
        "operation": "create",
        "character_name": "Elena",
        "narrative_role": "protagonist",
        "script_excerpt": "Elena stares at the screen, then slowly closes her laptop.",
        "production_brief": {"tone": TONE},
    })
    entry3 = _log_entry("character_director_agent", "create_character", result3)
    audit.append(entry3)
    chosen_char = result3["proposals"][0]
    print(f"   → Visual: {chosen_char['visual_description'][:80]}")
    print(f"   → Invariants: {chosen_char['costume_invariants']}")

    # ── Stage 8 write-back: commit approved character to ProductionService ──
    commit_result = agent3.run({
        "operation": "commit",
        "character_name": "Elena",
        "narrative_role": "protagonist",
        "approved_proposal": chosen_char,
    })
    char_dict = commit_result["character"]
    char_id = commit_result["character_id"]
    # Persist via apply_event (decision event carries the new character in payload)
    commit_entry = AuditEntry(
        id=_new_evt_id(),
        ts=utc_now_iso(),
        actor="character_director_agent",
        action_type="decision",
        payload={"operation": "commit_character", "character": char_dict},
        reason=commit_result["rationale"],
    )
    prod = svc.apply_event(prod, commit_entry)
    # Update Production.characters in-memory and save
    from dataclasses import replace
    prod = replace(prod, characters=list(prod.characters) + [
        __import__("schema.production_document", fromlist=["Character"]).Character(
            id=char_dict["id"],
            name=char_dict["name"],
            role=char_dict.get("role"),
        )
    ])
    svc.save(prod)
    print(f"   → Character '{char_dict['name']}' committed to ProductionService (id={char_id})\n")

    # ── Agent 4: StoryboardArtistAgent ─────────────────────────────────────
    print("[4/6] StoryboardArtistAgent — drawing ASCII storyboard...")
    agent4 = StoryboardArtistAgent()
    result4 = agent4.run({
        "shot_id": "shot-001",
        "camera": chosen_shot["camera"],
        "characters": [{"id": "char-elena", "name": "Elena"}],
        "location": "Elena's home office",
        "intent": chosen_shot.get("label", ""),
    })
    entry4 = _log_entry("storyboard_artist_agent", "draw_storyboard", result4)
    audit.append(entry4)
    print(f"   → {result4['composition_description'][:80]}")
    print(f"   → Frame:\n{result4['blocking_diagram']}\n")

    # ── Agent 5: ReviewerAgent ─────────────────────────────────────────────
    print("[5/6] ReviewerAgent — evaluating shot against ConsistencyContract...")
    agent5 = ReviewerAgent()
    contract = {
        "required_attributes": ["laptop", "indoor_setting"],
        "prohibited_attributes": ["outdoor"],
        "variance_tolerance": 0.15,
    }
    generation_result = {
        "attributes": ["laptop", "indoor_setting", "natural_light"],
        "quality_score": 0.88,
        "metadata": {"framing": chosen_shot["camera"]["framing"], "color_temp_k": 5400},
        "shot_intent": chosen_shot.get("label", ""),
    }
    production_state = {
        "state": "DRAFT",
        "characters": [{"id": "char-elena", "name": "Elena", "consistency_contract": contract}],
        "creative_direction": chosen_angle["id"],
    }
    result5 = agent5.run({
        "shot_id": "shot-001",
        "generation_result": generation_result,
        "production": production_state,
    })
    entry5 = _log_entry("reviewer_agent", "review_shot", result5)
    audit.append(entry5)
    print(f"   → Verdict: {result5['verdict'].upper()} | Score: {result5['score']} | Blocking: {result5['blocking']}")
    for c in result5["checks"]:
        print(f"      [{c['result'].upper()}] {c['check_type']}: {c['detail'][:60]}")
    print()

    # ── Agent 6: EditorAgent ───────────────────────────────────────────────
    print("[6/6] EditorAgent — proposing cut assemblies...")
    agent6 = EditorAgent()
    shots = [
        {"id": "shot-001", "intent": "wide establishing, contrarian tone"},
        {"id": "shot-002", "intent": "medium close — Elena's hands on keyboard"},
        {"id": "shot-003", "intent": "insert — laptop screen, AI-generated text scrolling"},
    ]
    result6 = agent6.run({
        "scene_id": "scene-001",
        "shots": shots,
        "narrative_intent": "contemplative, unsettling",
        "target_duration_sec": 45.0,
    })
    entry6 = _log_entry("editor_agent", "propose_cuts", result6)
    audit.append(entry6)
    for p in result6["proposals"]:
        print(f"   → {p['label']}: {p['total_duration_sec']}s — {p['rationale'][:60]}")
    print()

    # ── Write audit trail ──────────────────────────────────────────────────
    audit_path = OUT_DIR / "crew_audit.jsonl"
    with open(audit_path, "w", encoding="utf-8") as fh:
        for entry in audit:
            fh.write(json.dumps(entry) + "\n")

    print(f"{'='*60}")
    print(f"Crew demo complete. {len(audit)} audit entries written to:")
    print(f"  {audit_path}")
    print(f"  ProductionService: {svc.storage_dir / prod.id / 'production.json'}")
    print(f"  Characters in production: {len(prod.characters)}")
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
