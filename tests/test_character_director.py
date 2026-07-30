"""Tests for CharacterDirectorAgent — Appendix K.3."""
from __future__ import annotations

from agents.character_director import CharacterDirectorAgent


def test_create_returns_three_proposals():
    agent = CharacterDirectorAgent()
    out = agent.run({"operation": "create", "narrative_role": "protagonist",
                     "character_name": "Elena", "script_excerpt": "She steps forward."})
    assert len(out["proposals"]) == 3


def test_create_proposals_have_required_fields():
    agent = CharacterDirectorAgent()
    out = agent.run({"operation": "create", "narrative_role": "antagonist",
                     "character_name": "Victor"})
    for p in out["proposals"]:
        assert "visual_description" in p
        assert "distinctive_features" in p
        assert "costume_invariants" in p
        assert "suggested_anchors" in p


def test_review_passes_consistent_result():
    agent = CharacterDirectorAgent()
    contract = {"required_attributes": ["red_scarf"], "prohibited_attributes": []}
    result = {"attributes": ["red_scarf", "silver_locket"]}
    out = agent.run({"operation": "review", "character_id": "char-001",
                     "generation_result": result, "consistency_contract": contract})
    assert out["consistent"] is True
    assert out["severity"] == "pass"


def test_review_fails_on_missing_required():
    agent = CharacterDirectorAgent()
    contract = {"required_attributes": ["red_scarf"], "prohibited_attributes": []}
    result = {"attributes": ["silver_locket"]}  # red_scarf missing
    out = agent.run({"operation": "review", "character_id": "char-001",
                     "generation_result": result, "consistency_contract": contract})
    assert out["consistent"] is False
    assert out["severity"] == "fail"
    assert any("red_scarf" in issue for issue in out["issues"])


def test_review_no_contract_passes():
    """K.11: agent with no consistency_contract returns consistent=True."""
    agent = CharacterDirectorAgent()
    out = agent.run({"operation": "review", "character_id": "char-x",
                     "generation_result": {"attributes": []},
                     "consistency_contract": {}})
    assert out["consistent"] is True


def test_create_safe_on_empty_input():
    """run({}) must not raise (K.11 rule 4)."""
    agent = CharacterDirectorAgent()
    out = agent.run({})
    assert "proposals" in out
    assert len(out["proposals"]) == 3


# ---------------------------------------------------------------------------
# commit operation — Stage 8 service write-back
# ---------------------------------------------------------------------------

def test_commit_returns_character_dict():
    agent = CharacterDirectorAgent()
    proposal = {
        "visual_description": "Sharp eyes, worn jacket.",
        "distinctive_features": ["sharp cheekbones", "alert posture"],
        "costume_invariants": ["worn jacket"],
        "suggested_anchors": ["medium shot"],
    }
    out = agent.run({
        "operation": "commit",
        "character_name": "Elena",
        "narrative_role": "protagonist",
        "approved_proposal": proposal,
    })
    assert "character" in out
    assert "character_id" in out
    assert "rationale" in out


def test_commit_character_has_required_fields():
    agent = CharacterDirectorAgent()
    proposal = {
        "distinctive_features": ["sharp cheekbones"],
        "costume_invariants": ["worn jacket"],
    }
    out = agent.run({
        "operation": "commit",
        "character_name": "Elena",
        "narrative_role": "protagonist",
        "approved_proposal": proposal,
    })
    char = out["character"]
    assert char["name"] == "Elena"
    assert char["role"] == "protagonist"
    assert "id" in char
    assert char["id"].startswith("char_")
    assert "consistency_contract" in char


def test_commit_character_id_uses_provided_id():
    agent = CharacterDirectorAgent()
    out = agent.run({
        "operation": "commit",
        "character_name": "Victor",
        "narrative_role": "antagonist",
        "approved_proposal": {},
        "character_id": "char_abc12345",
    })
    assert out["character_id"] == "char_abc12345"
    assert out["character"]["id"] == "char_abc12345"


def test_commit_generates_id_when_absent():
    agent = CharacterDirectorAgent()
    out = agent.run({
        "operation": "commit",
        "character_name": "Unknown",
        "approved_proposal": {},
    })
    assert out["character_id"].startswith("char_")


def test_commit_consistency_contract_has_required_attributes():
    agent = CharacterDirectorAgent()
    proposal = {"distinctive_features": ["red_scarf", "sharp_eyes"]}
    out = agent.run({
        "operation": "commit",
        "character_name": "Elena",
        "narrative_role": "protagonist",
        "approved_proposal": proposal,
    })
    cc = out["character"]["consistency_contract"]
    assert "red_scarf" in cc["required_attributes"]
    assert "sharp_eyes" in cc["required_attributes"]


def test_commit_consistency_contract_reviewer_checklist_from_invariants():
    agent = CharacterDirectorAgent()
    proposal = {
        "distinctive_features": [],
        "costume_invariants": ["worn jacket", "dark trousers"],
    }
    out = agent.run({
        "operation": "commit",
        "character_name": "Elena",
        "narrative_role": "protagonist",
        "approved_proposal": proposal,
    })
    cc = out["character"]["consistency_contract"]
    assert "worn jacket" in cc["reviewer_checklist"]
    assert "dark trousers" in cc["reviewer_checklist"]


def test_commit_safe_on_minimal_input():
    """run({operation: commit}) must not raise on missing keys."""
    agent = CharacterDirectorAgent()
    out = agent.run({"operation": "commit"})
    assert "character" in out
    assert out["character"]["name"] == "Unknown"


def test_commit_rationale_mentions_name_and_role():
    agent = CharacterDirectorAgent()
    out = agent.run({
        "operation": "commit",
        "character_name": "Marcus",
        "narrative_role": "supporting",
        "approved_proposal": {},
    })
    assert "Marcus" in out["rationale"]
    assert "supporting" in out["rationale"]
