"""Canonical re-export of StoryAgent from agents.story_agent.

Allows both:
    from agents.story import StoryAgent
    from agents.story_agent import StoryAgent
"""
from agents.story_agent import StoryAgent  # noqa: F401

__all__ = ["StoryAgent"]
