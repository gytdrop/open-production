"""BaseAgent - the bounded-scope contract every production crew agent must honour.

K.11 rules enforced here:
  1. Single-method interface: run(input: dict) -> dict.
  2. WRITABLE_FIELDS enforcement: if the subclass declares WRITABLE_FIELDS, any
     output key not in that set raises ScopeViolation before the result reaches
     the caller.  Keys starting with '_' are always allowed (internal metadata).
  3. DIAGNOSTIC_KEYS contract: subclasses MAY declare DIAGNOSTIC_KEYS as a
     frozenset of plain-string keys that the agent is allowed to emit as
     advisory output (e.g. "verdict", "score", "checks").  Anything not in
     WRITABLE_FIELDS, DIAGNOSTIC_KEYS, or starting with '_' is rejected.
  4. Never raises on empty input: run({}) is always safe (subclass responsibility,
     but BaseAgent.run() itself does not raise on missing keys).

The previous implementation hardcoded a 70+-key `always_ok` allowlist inside
_enforce_scope, which decoupled scope enforcement from the WRITABLE_FIELDS
contract and made every new agent / diagnostic key a hand-edit to base.py.
That approach is replaced here: the contract is the source of truth.
"""
from __future__ import annotations


class ScopeViolation(RuntimeError):
    """Raised when an agent attempts to write a field outside its declared scope."""


class BaseAgent:
    """Abstract base agent. Subclasses implement ``run``.

    Subclasses declare scope by overriding two class-level frozensets:

      WRITABLE_FIELDS  : frozenset[str]
          Dotted production-state paths the agent may write, e.g.
          {"Shot.camera", "Scene.color_look"}.  Anything in this set is
          allowed in the output dict (verbatim).

      DIAGNOSTIC_KEYS  : frozenset[str] | None
          Plain-string keys the agent may emit as advisory / read-only output,
          e.g. {"verdict", "score", "checks"}.  Keys in this set bypass the
          WRITABLE_FIELDS check.

    Skipping enforcement:
      - WRITABLE_FIELDS = None  => no scope enforcement at all (legacy agents).
      - WRITABLE_FIELDS = frozenset() with DIAGNOSTIC_KEYS = None
        => no production writes allowed; any output key triggers ScopeViolation.
    """

    # Subclasses override these.  None means "no enforcement" (legacy / read-only).
    WRITABLE_FIELDS: frozenset[str] | None = None
    DIAGNOSTIC_KEYS: frozenset[str] | None = None

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, input: dict) -> dict:  # noqa: A002
        """Process ``input`` and return a result dict. Must be overridden."""
        raise NotImplementedError(f"{self.__class__.__name__}.run() must be implemented")

    def _enforce_scope(self, output: dict) -> dict:
        """Validate ``output`` against the agent's declared scope.

        Allowed keys in the output dict:
          - Any key starting with '_' (internal / debugging metadata).
          - Any key in self.__class__.WRITABLE_FIELDS (dotted production state).
          - Any key in self.__class__.DIAGNOSTIC_KEYS (advisory / read-only).

        Also enforces K.11 Rule 5: every dict in a 'proposals' list must contain a
        'rationale' key.  A proposal without a rationale raises ScopeViolation.
        """
        declared_writable = self.__class__.WRITABLE_FIELDS
        declared_diag = self.__class__.DIAGNOSTIC_KEYS

        # Skip scope enforcement entirely when WRITABLE_FIELDS is None.
        if declared_writable is None:
            return output

        allowed: set[str] = set(declared_writable or ())
        if declared_diag is not None:
            allowed |= set(declared_diag)

        violations = [
            k for k in output
            if not k.startswith("_") and k not in allowed
        ]
        if violations:
            raise ScopeViolation(
                f"{self.__class__.__name__} attempted to write fields outside its "
                f"declared scope: {violations!r}. "
                f"Declared WRITABLE_FIELDS: {sorted(declared_writable or [])!r}. "
                f"Declared DIAGNOSTIC_KEYS: {sorted(declared_diag or [])!r}. "
                "Add the key to DIAGNOSTIC_KEYS (advisory) or WRITABLE_FIELDS "
                "(production state) on the subclass."
            )

        # K.11 Rule 5: rationale must be present in every proposal dict.
        for proposal in output.get("proposals") or []:
            if isinstance(proposal, dict) and "rationale" not in proposal:
                raise ScopeViolation(
                    f"{self.__class__.__name__} returned a proposal without a 'rationale' key. "
                    f"K.11 Rule 5: rationale is mandatory in every proposal. "
                    f"Proposal keys: {sorted(proposal.keys())!r}"
                )
        return output
