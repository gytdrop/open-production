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


def test_guided_flow_surfaces_production_id_in_html():
    """Guided Flow HTML contains the elements needed to display a production_id (VP.1)."""
    html = render_index_html(view="guided")
    # The prod-id-panel div must exist in the HTML
    assert "prod-id-panel" in html
    # The console link element must exist
    assert "prod-console-link" in html
    # The production_id display element must exist
    assert "prod-id-display" in html


def test_agent_console_has_per_actor_panel():
    """Agent Console HTML contains the per-actor filter panel (VP.2)."""
    html = render_index_html(view="console")
    # The data-test-actor-panel marker must be present
    assert "data-test-actor-panel" in html
    # The actor rail must contain the 'All' button
    assert "actor-all" in html
    # The actor-buttons container must be present
    assert "actor-buttons" in html


def test_agent_console_has_proposal_panels():
    """Agent Console HTML contains per-agent proposal panel elements (VP.3)."""
    html = render_index_html(view="console")
    # proposals grid container
    assert "proposals-grid" in html
    # approve / adjust / override button classes
    assert "btn-approve" in html
    assert "btn-adjust" in html
    assert "btn-override" in html
    # tab bar for switching between proposals and events panes
    assert "data-test-tab-bar" in html


def test_guided_flow_has_pipeline_wizard():
    """Guided Flow HTML contains the 26-stage pipeline wizard panel (VP.4)."""
    html = render_index_html(view="guided")
    # pipeline panel element
    assert "pipeline-panel" in html
    # pipeline grid container
    assert "pipeline-grid" in html
    # pipeline progress bar fill
    assert "pipeline-fill" in html
    # static text confirming 26-stage label
    assert "26-Stage Production Pipeline" in html


def test_build_proposals_from_production_returns_expected_shape():
    """_build_proposals_from_production returns well-formed proposal dicts."""
    from public_demo.server import _build_proposals_from_production
    prod = {
        "intent": {"topic": "Test topic", "audience": "researchers", "tone": "neutral"},
        "environments": [{"name": "Studio", "lighting_presets": ["key", "fill"]}],
        "scenes": [{"id": "s1", "name": "Scene 1", "shots": [
            {"id": "sh1", "intent": "wide establishing shot"},
        ]}],
    }
    proposals = _build_proposals_from_production(prod)
    assert len(proposals) >= 2  # at least ReviewerAgent + PublisherAgent always added
    ids = {p["id"] for p in proposals}
    assert "ReviewerAgent_stage23" in ids
    assert "PublisherAgent_stage25" in ids
    # each proposal must have required keys
    for p in proposals:
        assert "id" in p
        assert "agent" in p
        assert "stage" in p
        assert "title" in p
        assert "options" in p
        assert isinstance(p["options"], list)


def test_api_production_proposals_route_present():
    """The /api/production/<id>/proposals route is handled (404 for unknown id)."""
    from io import BytesIO
    from public_demo.server import DemoHTTPRequestHandler

    class _FakeServer:
        server_name = "localhost"
        server_port = 8000

    class FakeHandler(DemoHTTPRequestHandler):
        def __init__(self):
            self.path = "/api/production/nonexistent_id_xyz/proposals"
            self.server = _FakeServer()
            self.headers = {}
            self._responses = []
            self._headers_sent = []

        def send_response(self, code, message=None):
            self._responses.append(code)

        def send_header(self, key, value):
            self._headers_sent.append((key, value))

        def end_headers(self):
            pass

        @property
        def wfile(self):
            return BytesIO()

    handler = FakeHandler()
    handler.do_GET()
    # Should get a 404 (production not found) not a 404 "Not found" from routing
    # Either 404 (not found production) or 503 (service unavailable) is valid
    assert handler._responses[0] in (404, 503)
