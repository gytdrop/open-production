"""Minimal BaseAgent stub for the IBM submission scaffolding.

The real ``creative_reframing`` agent (built in Bob session 2) inherits from this.
Keep it tiny — no framework deps, no logging config, just the contract.
"""
from __future__ import annotations


class BaseAgent:
    """Abstract base agent. Subclasses implement ``run``."""

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, input: dict) -> dict:
        """Process ``input`` and return a result dict. Must be overridden."""
        raise NotImplementedError(f"{self.__class__.__name__}.run() must be implemented")