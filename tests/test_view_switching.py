"""Tests for ?view= routing and Agent Console page.

Covers:
- render_index_html(view="guided") returns 200 with "Guided Flow" content
- render_index_html(view="console") returns 200 with "Agent Console" content
- production_id threads through the view-switcher link in both directions
"""
from __future__ import annotations

from public_demo.server import render_index_html


def test_guided_view_contains_guided_flow():
    """?view=guided (default) renders the Guided Flow page."""
    html = render_index_html(view="guided")
    assert "Guided Flow" in html
    assert "Show creative angles" in html
    assert "Agent Console" in html  # must contain link to console


def test_console_view_contains_agent_console():
    """?view=console renders the Agent Console page."""
    html = render_index_html(view="console")
    assert "Agent Console" in html
    assert "Switch to Guided Flow" in html or "Guided Flow" in html


def test_production_id_preserved_in_guided_to_console_link():
    """Guided Flow page embeds the production_id in the Agent Console link."""
    pid = "prod_abc123"
    html = render_index_html(view="guided", production_id=pid)
    # The console link must include the production_id
    assert f"production_id={pid}" in html
    assert "view=console" in html


def test_production_id_preserved_in_console_to_guided_link():
    """Agent Console page embeds the production_id in the Guided Flow link."""
    pid = "prod_def456"
    html = render_index_html(view="console", production_id=pid)
    # The guided link must include the production_id
    assert f"production_id={pid}" in html
    assert "view=guided" in html


def test_default_view_is_guided():
    """render_index_html() with no args defaults to the Guided Flow view."""
    html = render_index_html()
    assert "Guided Flow" in html
    assert "Show creative angles" in html
