"""Human-in-the-loop confirm gate.

Pattern (from hyperframes-motion-director): propose → wait for human
confirmation → produce. Open Production uses this between Stage 2
(creative reframing) and Stage 3 (gates) so the user picks which
angle guides the write. The user picking is the AI-as-creative-partner
moment.

Ships two ``ConfirmSink`` implementations:
  - ``TtyConfirmSink``: interactive — print + stdin read.
  - ``AutoConfirmSink``: deterministic — picks default / first option.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass
class ConfirmRequest:
    summary: str
    options: list[str]
    default: str | None


@dataclass
class ConfirmResponse:
    choice: str
    declined: bool


class ConfirmSink(Protocol):
    """Anything that can present a confirm request and collect a response."""

    def ask(self, request: ConfirmRequest) -> ConfirmResponse: ...


class TtyConfirmSink:
    """Interactive terminal sink. Prints options, reads stdin, returns choice.

    Falls back to ``request.default`` on empty/unparsable input, and to the
    default or first option on EOF / non-interactive stdin.
    """

    def __init__(
        self,
        prompt_input: Callable[[str], str] = input,
        out=sys.stdout,
    ) -> None:
        self._prompt_input = prompt_input
        self._out = out

    def ask(self, request: ConfirmRequest) -> ConfirmResponse:
        print(request.summary, file=self._out)
        for i, opt in enumerate(request.options, 1):
            print(f"  {i}. {opt}", file=self._out)
        if request.default:
            print(f"  Default: {request.default}", file=self._out)
        labels = "/".join(str(i) for i in range(1, len(request.options) + 1))
        prompt = f"Choose [{labels}/d/default]: "
        try:
            raw = self._prompt_input(prompt)
        except (EOFError, KeyboardInterrupt):
            raw = ""
        text = raw.strip().lower()
        if text in {"n", "no"}:
            return ConfirmResponse(choice="", declined=True)
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(request.options):
                return ConfirmResponse(choice=request.options[idx], declined=False)
        fallback = request.default or (request.options[0] if request.options else "")
        return ConfirmResponse(choice=fallback, declined=False)


class AutoConfirmSink:
    """Deterministic sink for tests + ``--no-confirm`` CI mode."""

    def __init__(self, choice: str | None = None) -> None:
        self.choice = choice

    def ask(self, request: ConfirmRequest) -> ConfirmResponse:
        chosen = self.choice or request.default or (request.options[0] if request.options else "")
        return ConfirmResponse(choice=chosen, declined=False)
