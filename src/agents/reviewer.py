"""ReviewerAgent — evaluates generated outputs before they reach the user.

This agent never generates and never proposes. It only judges.
It runs between generation and delivery (Appendix J of open-production-plan.md).

Implements 5 check types:
  consistency_contract  — required/prohibited attributes vs ConsistencyContract
  brief_adherence       — does the shot serve its stated intent?
  technical_quality     — basic quality signal (mock: uses metadata score)
  continuity            — mood/color continuity vs adjacent shot spec
  stage_gate            — is this shot permitted at the current pipeline stage?

Verdict aggregation:
  pass  = all checks pass
  warn  = at least one warn, no fail
  fail  = at least one fail

Blocking threshold: score < 0.60 → blocking=True (do not deliver to user)
Warn threshold:     score < 0.75 → warn badge attached
"""
from __future__ import annotations

from agents.base import BaseAgent
from validation.gates import ConsistencyContractGate

# ---------------------------------------------------------------------------
# Constants (per Appendix J.2)
# ---------------------------------------------------------------------------

BLOCKING_THRESHOLD = 0.60
WARN_THRESHOLD = 0.75

CHECK_TYPES = (
    "consistency_contract",
    "brief_adherence",
    "technical_quality",
    "continuity",
    "stage_gate",
)

# Scores assigned to each verdict level for aggregation
_VERDICT_SCORE = {"pass": 1.0, "warn": 0.70, "fail": 0.20}


def _check_entry(check_type: str, result: str, detail: str, evidence: dict | None = None) -> dict:
    return {
        "check_type": check_type,
        "result": result,        # "pass" | "warn" | "fail"
        "detail": detail,
        "evidence": evidence or {},
    }


class ReviewerAgent(BaseAgent):
    """Evaluates a GenerationResult against the production state.

    Input dict keys:
        shot_id (str)              — identifier of the shot being reviewed
        generation_result (dict)   — must contain 'attributes' list and optionally
                                     'quality_score' float and 'metadata' dict
        production (dict)          — full production state (characters list with
                                     consistency_contract fields)
        check_types (list[str])    — subset of CHECK_TYPES to run; defaults to all

    Output dict keys:
        verdict   str          "pass" | "warn" | "fail"
        score     float        0.0–1.0 aggregate
        checks    list[dict]   one entry per check run
        blocking  bool         True = do not deliver to user
        suggestion_layer dict | None
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset()  # reviewer never writes production state

    def __init__(self) -> None:
        super().__init__(name="reviewer_agent")
        self._cc_gate = ConsistencyContractGate()

    def run(self, input: dict) -> dict:  # noqa: A002
        shot_id = input.get("shot_id", "unknown")
        generation_result = input.get("generation_result") or {}
        production = input.get("production") or {}
        requested = input.get("check_types") or list(CHECK_TYPES)

        checks: list[dict] = []

        for check_type in requested:
            if check_type == "consistency_contract":
                checks.extend(self._check_consistency_contract(generation_result, production))
            elif check_type == "brief_adherence":
                checks.append(self._check_brief_adherence(generation_result, production))
            elif check_type == "technical_quality":
                checks.append(self._check_technical_quality(generation_result))
            elif check_type == "continuity":
                checks.append(self._check_continuity(generation_result, production))
            elif check_type == "stage_gate":
                checks.append(self._check_stage_gate(generation_result, production))
            # unknown check_types are silently skipped (K.11 rule 4: never raises)

        verdict, score = self._aggregate(checks)
        # A "fail" verdict is always blocking, regardless of average score
        blocking = (verdict == "fail") or (score < BLOCKING_THRESHOLD)
        suggestion_layer = self._build_suggestion(checks) if not blocking and score < WARN_THRESHOLD else None

        return {
            "verdict": verdict,
            "score": round(score, 3),
            "checks": checks,
            "blocking": blocking,
            "suggestion_layer": suggestion_layer,
            "shot_id": shot_id,
        }

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_consistency_contract(
        self, generation_result: dict, production: dict
    ) -> list[dict]:
        """Run ConsistencyContractGate for each character in the production."""
        entries: list[dict] = []
        characters = production.get("characters") or []

        for char in characters:
            contract = char.get("consistency_contract")
            if not contract:
                continue  # no contract = no enforcement (J.3 step 2)
            ok, reason = self._cc_gate.check(contract, generation_result)
            result = "pass" if ok else "fail"
            entries.append(_check_entry(
                "consistency_contract", result,
                f"character '{char.get('name', char.get('id', '?'))}': {reason}",
                {"character_id": char.get("id"), "reason": reason},
            ))

        if not entries:
            entries.append(_check_entry(
                "consistency_contract", "pass",
                "No consistency contracts defined — check skipped.",
            ))
        return entries

    def _check_brief_adherence(self, generation_result: dict, production: dict) -> dict:
        """Rule-based brief adherence (prototype per J.4)."""
        metadata = generation_result.get("metadata") or {}
        intent = production.get("intent") or {}
        shot_intent = generation_result.get("shot_intent", "")
        framing = metadata.get("framing", "")
        tone = intent.get("tone", "")
        creative_direction = production.get("creative_direction", "")

        issues: list[str] = []
        # Flagrant contradiction: "no wide shots" in intent but extreme_wide framing
        if "no wide" in shot_intent.lower() and "wide" in framing.lower():
            issues.append(f"shot_intent forbids wide shots but framing='{framing}'")
        # Mood mismatch: contrarian direction vs warm advocate mood
        mood = metadata.get("mood", "")
        if "contrarian" in creative_direction.lower() and "warm" in mood.lower():
            issues.append(f"creative_direction=contrarian conflicts with mood='{mood}'")

        if issues:
            return _check_entry("brief_adherence", "warn",
                                 "; ".join(issues), {"issues": issues})
        return _check_entry("brief_adherence", "pass",
                             "No brief adherence violations detected.")

    def _check_technical_quality(self, generation_result: dict) -> dict:
        """Mock technical quality: reads quality_score from generation metadata."""
        score = float(generation_result.get("quality_score", 0.85))
        if score < 0.40:
            return _check_entry("technical_quality", "fail",
                                 f"quality_score={score:.2f} is below minimum threshold (0.40).",
                                 {"quality_score": score})
        if score < 0.65:
            return _check_entry("technical_quality", "warn",
                                 f"quality_score={score:.2f} is below recommended threshold (0.65).",
                                 {"quality_score": score})
        return _check_entry("technical_quality", "pass",
                             f"quality_score={score:.2f} passes threshold.",
                             {"quality_score": score})

    def _check_continuity(self, generation_result: dict, production: dict) -> dict:
        """Lighting colour temperature continuity check (J.5)."""
        metadata = generation_result.get("metadata") or {}
        prev = production.get("previous_shot_metadata") or {}
        cur_k = metadata.get("color_temp_k")
        prev_k = prev.get("color_temp_k")

        if cur_k is not None and prev_k is not None:
            diff = abs(float(cur_k) - float(prev_k))
            if diff > 500:
                return _check_entry(
                    "continuity", "warn",
                    f"Lighting jump: {prev_k}K → {cur_k}K (diff={diff}K > 500K threshold).",
                    {"color_temp_k_diff": diff},
                )
        return _check_entry("continuity", "pass",
                             "No continuity violations detected.")

    def _check_stage_gate(self, generation_result: dict, production: dict) -> dict:
        """Verify the production state permits generation at this stage."""
        state = production.get("state", "DRAFT")
        permitted_states = {"DRAFT", "IN_REVIEW", "APPROVED"}
        if state not in permitted_states:
            return _check_entry(
                "stage_gate", "fail",
                f"Production state='{state}' does not permit generation. "
                f"Permitted: {sorted(permitted_states)}",
                {"state": state},
            )
        return _check_entry("stage_gate", "pass",
                             f"Production state='{state}' permits generation.")

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate(checks: list[dict]) -> tuple[str, float]:
        if not checks:
            return "pass", 1.0
        verdicts = [c["result"] for c in checks]
        if "fail" in verdicts:
            verdict = "fail"
        elif "warn" in verdicts:
            verdict = "warn"
        else:
            verdict = "pass"
        score = sum(_VERDICT_SCORE.get(v, 0.5) for v in verdicts) / len(verdicts)
        return verdict, score

    @staticmethod
    def _build_suggestion(checks: list[dict]) -> dict | None:
        warn_checks = [c for c in checks if c["result"] == "warn"]
        if not warn_checks:
            return None
        return {
            "type": "suggestion",
            "issues": [c["detail"] for c in warn_checks],
            "action": "Review the flagged items and adjust parameters before re-generating.",
        }
