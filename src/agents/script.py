"""Canonical re-export of ScriptAgent from agents.script_agent.

Allows both:
    from agents.script import ScriptAgent
    from agents.script_agent import ScriptAgent
"""
from agents.script_agent import ScriptAgent  # noqa: F401

__all__ = ["ScriptAgent"]
