"""Lightweight browser demo for general audiences.

This module wraps the existing Open Production flow in a tiny HTTP server so
people can interact with it from a browser instead of a terminal.

Two views are available via ?view= query parameter:
  ?view=guided  (default) — Guided Flow: step-by-step angle selection
  ?view=console           — Agent Console: live audit-event log
Both views accept ?production_id= and link to each other preserving it.
"""
from __future__ import annotations

# Allow ``python src/public_demo/server.py`` to launch the demo without
# requiring the user to also set PYTHONPATH or run via scripts/run_web_demo.py.
# We need both the repo root (for ``demo_flow``) and ``src/`` (for
# ``src.service.*`` / ``src.schema.*`` / ``src.transforms.*``) on sys.path.
import sys as _sys
from pathlib import Path as _Path
_HERE = _Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent  # src/public_demo -> src -> repo root
for _p in (str(_ROOT), str(_HERE)):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
del _p, _HERE, _ROOT

import json
import logging
import mimetypes
import os
import re as _re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger("open_production.demo_server")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
    logger.propagate = False

# Pattern used to validate production_id path components. Real IDs look like
# "prod_<12 hex>" / "studio_<12 hex>". The relaxed form below also accepts
# the legacy / synthetic IDs used in tests (e.g. "prod_abc123") while
# rejecting path-traversal sequences ("..", "/", "\") and oversized input.
_PRODUCTION_ID_RE = _re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,63}$")

from demo_flow import build_demo_report, generate_angles

# Optional ProductionService — used for the /api/production/* endpoints.
try:
    from src.service.production_service import ProductionNotFound, ProductionService
    _SVC_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SVC_AVAILABLE = False


DEFAULT_TOPIC = "The future of AI in creative industries"
DEFAULT_AUDIENCE = "educated_lay"
DEFAULT_TONE = "neutral"

_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
_STORAGE_DIR = _PROJECT_ROOT / "output" / "productions"
_PUBLIC_DEMO_DIR = _PROJECT_ROOT / "output" / "public-demo"

# Path to the compiled React app — built by `cd web && npm run build`
_DIST_DIR = _PROJECT_ROOT / "web" / "dist"
# Resolved once at import time so per-request static-serve checks reuse the same value.
_DIST_DIR_RESOLVED = _DIST_DIR.resolve()

# Configurable via env var. Default "*" keeps the existing demo behavior
# (Vite dev proxy + same-origin fetches). Set OPEN_PRODUCTION_CORS_ORIGIN to a
# single explicit origin (e.g. "https://app.example.com") when exposing the
# server beyond localhost.
_CORS_ORIGIN = os.environ.get("OPEN_PRODUCTION_CORS_ORIGIN", "*").strip() or "*"

_MIME_MAP: dict[str, str] = {
    ".html":  "text/html; charset=utf-8",
    ".js":    "application/javascript",
    ".css":   "text/css",
    ".json":  "application/json",
    ".ico":   "image/x-icon",
    ".png":   "image/png",
    ".svg":   "image/svg+xml",
    ".woff2": "font/woff2",
    ".woff":  "font/woff",
    ".ttf":   "font/ttf",
}


def _serve_static(handler: "DemoHTTPRequestHandler", path: str) -> bool:
    """Try to serve a file from web/dist/. Returns True if served, False otherwise.

    Any path that doesn't map to an existing file returns index.html (SPA fallback).
    Only called for non-/api paths.
    """
    if not _DIST_DIR.exists():
        return False  # dist not built yet — fall through to legacy HTML handler

    # Reject any path that contains .. segments before even resolving it.
    # pathlib.PurePosixPath preserves the .. segments literally.
    if ".." in Path(path).parts:
        file_path = _DIST_DIR / "index.html"
    else:
        file_path = _DIST_DIR / path.lstrip("/")
        # Resolve to prevent directory traversal outside _DIST_DIR.
        try:
            file_path = file_path.resolve().relative_to(_DIST_DIR_RESOLVED)
        except (ValueError, OSError):
            file_path = _DIST_DIR / "index.html"

    if not file_path.is_file():
        # SPA fallback — React Router handles the route client-side
        file_path = _DIST_DIR / "index.html"

    suffix = file_path.suffix.lower()
    mime = _MIME_MAP.get(suffix) or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    data = file_path.read_bytes()

    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", mime)
    handler.send_header("Content-Length", str(len(data)))
    # Cache assets forever (they're content-addressed); HTML is no-cache
    if suffix == ".html":
        handler.send_header("Cache-Control", "no-cache")
        handler.send_header("X-Content-Type-Options", "nosniff")
        handler.send_header("Referrer-Policy", "no-referrer")
    else:
        handler.send_header("Cache-Control", "public, max-age=31536000, immutable")
    handler.send_header("Access-Control-Allow-Origin", _CORS_ORIGIN)
    handler.end_headers()
    handler.wfile.write(data)
    return True


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Open Production</title>
  <style>
    :root {
      --bg: #07111f;
      --panel: rgba(10, 18, 33, 0.82);
      --panel-border: rgba(137, 181, 255, 0.18);
      --text: #f5f7fb;
      --muted: #9db0cc;
      --accent: #7fd4c1;
      --accent-strong: #f0b85d;
      --danger: #ff7a7a;
      --shadow: 0 20px 70px rgba(0, 0, 0, 0.35);
      --radius: 24px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Gill Sans", "Trebuchet MS", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(127, 212, 193, 0.18), transparent 34%),
        radial-gradient(circle at top right, rgba(240, 184, 93, 0.18), transparent 28%),
        linear-gradient(160deg, #08111f 0%, #0c1a2f 48%, #060a13 100%);
    }
    .shell {
      width: min(1160px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }
    .hero {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 22px;
      align-items: end;
      margin-bottom: 22px;
    }
    .title {
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: clamp(2.8rem, 6vw, 5.6rem);
      line-height: 0.95;
      margin: 10px 0 14px;
      letter-spacing: -0.04em;
    }
    .eyebrow {
      display: inline-flex;
      gap: 10px;
      align-items: center;
      padding: 8px 14px;
      border-radius: 999px;
      border: 1px solid var(--panel-border);
      background: rgba(255, 255, 255, 0.06);
      color: #d8e6ff;
      font-size: 0.95rem;
      letter-spacing: 0.02em;
    }
    .lede {
      max-width: 68ch;
      font-size: 1.08rem;
      line-height: 1.7;
      color: var(--muted);
      margin: 0;
    }
    .stat-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 22px;
    }
    .stat {
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stat b {
      display: block;
      font-size: 1.02rem;
      margin-bottom: 4px;
      color: #ffffff;
    }
    .stat span {
      color: var(--muted);
      font-size: 0.95rem;
      line-height: 1.45;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      box-shadow: var(--shadow);
      border-radius: var(--radius);
      backdrop-filter: blur(16px);
    }
    .form-panel {
      padding: 20px;
      margin-bottom: 18px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.8fr 1fr 1fr;
      gap: 14px;
      align-items: end;
    }
    label {
      display: block;
      font-size: 0.9rem;
      letter-spacing: 0.02em;
      color: #d6e3fa;
      margin-bottom: 8px;
    }
    input, select, button, textarea {
      width: 100%;
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      background: rgba(255, 255, 255, 0.08);
      color: var(--text);
      padding: 14px 15px;
      font: inherit;
    }
    textarea {
      min-height: 82px;
      resize: vertical;
    }
    input::placeholder, textarea::placeholder {
      color: #8fa2bf;
    }
    button {
      cursor: pointer;
      transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
    }
    button:hover {
      transform: translateY(-1px);
    }
    .primary {
      background: linear-gradient(135deg, #7fd4c1, #a7c8ff);
      color: #03101b;
      border: none;
      font-weight: 700;
      box-shadow: 0 14px 30px rgba(127, 212, 193, 0.22);
    }
    .secondary {
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
    }
    .panel-title {
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: 1.45rem;
      margin: 0 0 6px;
    }
    .panel-copy {
      color: var(--muted);
      margin: 0 0 18px;
      line-height: 1.6;
    }
    .hidden { display: none; }
    .angles {
      padding: 20px;
      margin-bottom: 18px;
    }
    .angle-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }
    .card {
      padding: 18px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
      height: 100%;
    }
    .card h3 {
      margin: 0 0 6px;
      font-size: 1.15rem;
    }
    .badge {
      display: inline-flex;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      background: rgba(127, 212, 193, 0.14);
      color: #c0f4e7;
      margin-bottom: 12px;
    }
    .card p, .card li {
      color: #d7e3f7;
      line-height: 1.55;
    }
    .card ul {
      margin: 10px 0 0;
      padding-left: 18px;
    }
    .card .meta {
      color: var(--muted);
      font-size: 0.95rem;
    }
    .story {
      padding: 20px;
      margin-bottom: 18px;
    }
    .summary {
      padding: 16px 18px;
      border-radius: 18px;
      background: rgba(127, 212, 193, 0.08);
      border: 1px solid rgba(127, 212, 193, 0.14);
      line-height: 1.65;
      color: #edf7ff;
    }
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 16px;
    }
    .detail {
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .detail .num {
      display: block;
      font-size: 1.7rem;
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      color: #ffffff;
      margin-bottom: 4px;
    }
    .audit {
      margin-top: 16px;
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .audit pre {
      margin: 12px 0 0;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 280px;
      overflow: auto;
      color: #dce9ff;
      font-size: 0.92rem;
      line-height: 1.55;
    }
    .prod-id-panel {
      margin-top: 14px;
      padding: 14px 18px;
      border-radius: 18px;
      background: rgba(127, 212, 193, 0.07);
      border: 1px solid rgba(127, 212, 193, 0.20);
    }
    .prod-id-panel .label { color: var(--muted); font-size: 0.88rem; margin-bottom: 6px; }
    .prod-id-panel code { background: rgba(255,255,255,0.09); border-radius: 8px; padding: 3px 10px; font-size: 0.92rem; letter-spacing: 0.01em; }
    .prod-id-panel .console-link {
      display: inline-block; margin-top: 10px;
      padding: 8px 18px; border-radius: 999px;
      background: rgba(127, 212, 193, 0.14);
      border: 1px solid rgba(127, 212, 193, 0.30);
      color: #c0f4e7; text-decoration: none; font-size: 0.9rem;
    }
    .prod-id-panel .console-link:hover { background: rgba(127, 212, 193, 0.22); }
    .footer {
      margin-top: 18px;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.6;
    }
    .button-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    .status {
      margin-top: 12px;
      color: var(--accent);
      min-height: 1.3em;
    }
    .selected {
      outline: 2px solid rgba(127, 212, 193, 0.55);
      background: rgba(127, 212, 193, 0.11);
    }
    /* ---- pipeline wizard ---- */
    .pipeline {
      padding: 20px;
      margin-bottom: 18px;
    }
    .pipeline-toggle {
      display: flex; align-items: center; justify-content: space-between;
      cursor: pointer; user-select: none; margin-bottom: 0;
    }
    .pipeline-toggle-arrow { color: var(--muted); font-size: 1.1rem; transition: transform 0.2s; }
    .pipeline-toggle-arrow.open { transform: rotate(90deg); }
    .pipeline-body { display: none; margin-top: 14px; }
    .pipeline-body.open { display: block; }
    .pipeline-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 8px;
    }
    .stage-tile {
      display: flex; align-items: flex-start; gap: 8px;
      padding: 10px 12px; border-radius: 14px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.07);
      font-size: 0.85rem;
    }
    .stage-tile.s-done {
      background: rgba(127,212,193,0.09);
      border-color: rgba(127,212,193,0.22);
    }
    .stage-tile.s-active {
      background: rgba(240,184,93,0.1);
      border-color: rgba(240,184,93,0.28);
    }
    .stage-tile.s-future {
      opacity: 0.45;
    }
    .stage-num {
      flex-shrink: 0; width: 20px; height: 20px;
      border-radius: 50%; display: flex; align-items: center; justify-content: center;
      font-size: 0.72rem; font-weight: 700;
      background: rgba(255,255,255,0.1); color: var(--muted);
    }
    .stage-tile.s-done .stage-num { background: rgba(127,212,193,0.25); color: #c0f4e7; }
    .stage-tile.s-active .stage-num { background: rgba(240,184,93,0.28); color: #fde8a0; }
    .stage-info { flex: 1; }
    .stage-name { color: var(--text); font-weight: 600; line-height: 1.3; }
    .stage-note { color: var(--muted); font-size: 0.78rem; margin-top: 2px; line-height: 1.35; }
    .pipeline-progress-bar {
      height: 4px; border-radius: 2px; background: rgba(255,255,255,0.08);
      margin-bottom: 14px; overflow: hidden;
    }
    .pipeline-progress-fill {
      height: 100%; border-radius: 2px;
      background: linear-gradient(90deg, #7fd4c1, #a7c8ff);
      transition: width 0.4s ease;
    }
    @media (max-width: 920px) {
      .hero, .grid, .angle-grid, .detail-grid, .stat-row {
        grid-template-columns: 1fr;
      }
      .title {
        font-size: clamp(2.4rem, 12vw, 4.6rem);
      }
      .pipeline-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
      <a href="{{CONSOLE_LINK}}" style="padding:7px 16px;border-radius:999px;border:1px solid rgba(137,181,255,0.18);background:rgba(255,255,255,0.07);color:#7fd4c1;text-decoration:none;font-size:0.93rem;">Agent Console &#8594;</a>
    </div>
    <section class="hero">
      <div>
        <div class="eyebrow">Open Production | Guided Flow</div>
        <h1 class="title">AI as a creative partner for public-facing writing</h1>
        <p class="lede">
          Tell the system what you want. It suggests three creative angles, lets
          you pick one, then checks claims and metadata before anything is
          treated as ready to publish. You never need to touch the terminal.
        </p>
        <div class="stat-row">
          <div class="stat">
            <b>1. State your intent</b>
            <span>Topic, audience, and tone in plain language.</span>
          </div>
          <div class="stat">
            <b>2. Pick an angle</b>
            <span>Skeptic, advocate, or contrarian.</span>
          </div>
          <div class="stat">
            <b>3. Review the gate results</b>
            <span>Every decision is captured in the audit trail.</span>
          </div>
        </div>
      </div>
      <div class="panel" style="padding:20px;">
        <div class="panel-title">What this feels like</div>
        <p class="panel-copy" style="margin-bottom:0;">
          A guided conversation, not a command line. The browser shows the
          choices, the rationale, and the outcome in one place.
        </p>
      </div>
    </section>

    <section class="panel form-panel">
      <div class="panel-title">Start a demo</div>
      <p class="panel-copy">Try the sample topic or replace it with your own. When you submit, Open Production will show three angles first.</p>
      <form id="demo-form">
        <div class="grid">
          <div>
            <label for="topic">Topic</label>
            <textarea id="topic" name="topic" placeholder="Example: The future of AI in healthcare">{{DEFAULT_TOPIC}}</textarea>
          </div>
          <div>
            <label for="audience">Audience</label>
            <select id="audience" name="audience">
              <option value="educated_lay" selected>General public</option>
              <option value="students">Students</option>
              <option value="researchers">Researchers</option>
            </select>
          </div>
          <div>
            <label for="tone">Tone</label>
            <select id="tone" name="tone">
              <option value="neutral" selected>Neutral</option>
              <option value="warm">Warm</option>
              <option value="confident">Confident</option>
              <option value="playful">Playful</option>
            </select>
          </div>
        </div>
        <div class="button-row">
          <button class="primary" type="submit">Show creative angles</button>
          <button class="secondary" type="button" id="sample-button">Load sample topic</button>
          <button class="secondary" type="button" id="reset-button">Reset</button>
        </div>
        <div class="status" id="status"></div>
      </form>
    </section>

    <section class="panel angles hidden" id="angles-panel">
      <div class="panel-title">Choose a creative angle</div>
      <p class="panel-copy">Pick the frame that feels most useful. The chosen angle becomes the guide for the rest of the run.</p>
      <div class="angle-grid" id="angle-grid"></div>
    </section>

    <section class="panel story hidden" id="story-panel">
      <div class="panel-title">Result</div>
      <div class="summary" id="summary"></div>
      <div class="detail-grid">
        <div class="detail"><span class="num" id="accepted-count">0</span>accepted claims</div>
        <div class="detail"><span class="num" id="rejected-count">0</span>rejected claims</div>
        <div class="detail"><span class="num" id="contradiction-count">0</span>contradictions</div>
      </div>
      <div class="prod-id-panel hidden" id="prod-id-panel">
        <div class="label">Production created</div>
        <code id="prod-id-display"></code>
        <br/>
        <a class="console-link" id="prod-console-link" href="#">Open in Agent Console &#8594;</a>
      </div>
      <div class="audit">
        <div class="panel-title" style="font-size:1.1rem;">Audit trail</div>
        <p class="panel-copy" style="margin-bottom:0;">The browser keeps the decision log visible so the result stays traceable.</p>
        <div class="button-row">
          <button class="secondary" type="button" id="download-audit">Download audit JSON</button>
          <button class="secondary" type="button" id="start-over">Start over</button>
        </div>
        <pre id="audit-log"></pre>
      </div>
    </section>

    <!-- pipeline wizard: shown after a run completes -->
    <section class="panel pipeline hidden" id="pipeline-panel">
      <div class="pipeline-toggle" id="pipeline-toggle">
        <div class="panel-title" style="margin:0;">26-Stage Production Pipeline</div>
        <span class="pipeline-toggle-arrow open" id="pipeline-arrow">&#9658;</span>
      </div>
      <div class="pipeline-body open" id="pipeline-body">
        <p class="panel-copy" style="margin:8px 0 12px;">
          Each stage maps to a dedicated agent or gate. Completed stages are highlighted. Stages beyond the current demo scope are dimmed.
        </p>
        <div class="pipeline-progress-bar">
          <div class="pipeline-progress-fill" id="pipeline-fill" style="width:0%"></div>
        </div>
        <div class="pipeline-grid" id="pipeline-grid"></div>
      </div>
    </section>

    <div class="footer">
      Built on the same Open Production core used in the terminal demo. The browser is the public face; the audit trail is the proof.
    </div>
  </main>

  <script>
    const DEFAULT_TOPIC = "{{DEFAULT_TOPIC}}";
    const DEFAULT_AUDIENCE = "{{DEFAULT_AUDIENCE}}";
    const DEFAULT_TONE = "{{DEFAULT_TONE}}";

    const form = document.getElementById("demo-form");
    const topicField = document.getElementById("topic");
    const audienceField = document.getElementById("audience");
    const toneField = document.getElementById("tone");
    const statusEl = document.getElementById("status");
    const anglesPanel = document.getElementById("angles-panel");
    const angleGrid = document.getElementById("angle-grid");
    const storyPanel = document.getElementById("story-panel");
    const summaryEl = document.getElementById("summary");
    const auditLogEl = document.getElementById("audit-log");
    const acceptedEl = document.getElementById("accepted-count");
    const rejectedEl = document.getElementById("rejected-count");
    const contradictionEl = document.getElementById("contradiction-count");
    const downloadButton = document.getElementById("download-audit");
    const startOverButton = document.getElementById("start-over");
    const sampleButton = document.getElementById("sample-button");
    const resetButton = document.getElementById("reset-button");

    let latestAngles = [];
    let latestRun = null;
    let currentPayload = null;

    function setStatus(message) {
      statusEl.textContent = message || "";
    }

    function show(element) {
      element.classList.remove("hidden");
    }

    function hide(element) {
      element.classList.add("hidden");
    }

    function readPayload() {
      const topic = topicField.value.trim() || DEFAULT_TOPIC;
      return {
        topic,
        audience: audienceField.value || DEFAULT_AUDIENCE,
        tone: toneField.value || DEFAULT_TONE,
      };
    }

    function renderAngles(angles) {
      latestAngles = angles;
      angleGrid.innerHTML = "";
      angles.forEach((angle) => {
        const card = document.createElement("article");
        card.className = "card";
        card.dataset.angleId = angle.id;
        card.innerHTML = `
          <div class="badge">${angle.id}</div>
          <h3>${angle.name}</h3>
          <p>${angle.summary}</p>
          <div class="meta">Why it matters</div>
          <p style="margin-top:6px;">${angle.risk_focus}</p>
          <div class="meta">Questions to address</div>
          <ul>
            ${angle.questions_to_address.map((q) => `<li>${q}</li>`).join("")}
          </ul>
          <div class="button-row">
            <button class="primary" type="button">Use this angle</button>
          </div>
        `;
        card.querySelector("button").addEventListener("click", () => finalizeRun(angle.id));
        angleGrid.appendChild(card);
      });
      show(anglesPanel);
    }

    // ---- pipeline stage definitions (all 26) ----
    const PIPELINE_STAGES = [
      { n:  1, name: "Idea / Intent",        agent: "IntentDocument",          note: "Topic, audience, tone captured." },
      { n:  2, name: "Research",             agent: "ResearchAgent",            note: "Source validation gate." },
      { n:  3, name: "References",           agent: "Reference",               note: "SHA-256 provenance." },
      { n:  4, name: "Moodboard",            agent: "MoodboardAgent",          note: "MoodSpec on scenes." },
      { n:  5, name: "Creative Direction",   agent: "CreativeReframing",       note: "3 angles + ConfirmGate." },
      { n:  6, name: "Story",               agent: "StoryAgent",               note: "Narrative structure locked." },
      { n:  7, name: "Script",              agent: "ScriptAgent",              note: "Genre-keyed scene templates." },
      { n:  8, name: "Characters",          agent: "CharacterDirectorAgent",   note: "Commit to production doc." },
      { n:  9, name: "Locations",           agent: "EnvironmentArtistAgent",   note: "Environment write-back." },
      { n: 10, name: "Shot Planning",       agent: "ShotPlanningAgent",        note: "Ordered shot list." },
      { n: 11, name: "Storyboard",          agent: "StoryboardArtistAgent",    note: "ASCII blocking diagrams." },
      { n: 12, name: "Timeline",            agent: "Timeline",                 note: "Scene order assembly." },
      { n: 13, name: "Camera",              agent: "ShotDesignerAgent",        note: "3 camera proposals." },
      { n: 14, name: "Lighting",            agent: "ShotDesignerAgent",        note: "Lighting specs." },
      { n: 15, name: "Assets",              agent: "AssetLibraryAgent",        note: "Inventory + gap detection." },
      { n: 16, name: "Generation",          agent: "GenerationAgent",          note: "GenerationPlugin contract." },
      { n: 17, name: "Editing",             agent: "EditorAgent",              note: "3 cut assemblies." },
      { n: 18, name: "Animation",           agent: "AnimationDirectorAgent",   note: "Motion spec + lock gate." },
      { n: 19, name: "Voice",               agent: "VoiceDirectorAgent",       note: "Per-line emotion/pace." },
      { n: 20, name: "Music",               agent: "MusicComposerAgent",       note: "Narrative-keyed cue briefs." },
      { n: 21, name: "Sound",               agent: "SoundDesignerAgent",       note: "Ambient/SFX palette." },
      { n: 22, name: "Color",               agent: "ColoristAgent",            note: "3 color grade proposals." },
      { n: 23, name: "Review / QA",         agent: "ReviewerAgent",            note: "5 check types, blocking threshold." },
      { n: 24, name: "Iteration",           agent: "ProductionService",        note: "Branching + snapshot." },
      { n: 25, name: "Publishing",          agent: "PublisherAgent",           note: "PublicationGate readiness." },
      { n: 26, name: "Archive",             agent: "ProductionService",        note: "production.json + audit.jsonl." },
    ];

    // Stages exercised by the demo run (research gate + creative direction + env + shot plan + review/qa)
    const DEMO_DONE_STAGES = new Set([1, 2, 5, 9, 10, 23]);
    // Stage currently active in the demo (evidence gates + publication)
    const DEMO_ACTIVE_STAGES = new Set([3, 25]);

    function renderPipeline(doneStages, activeStages) {
      const grid = document.getElementById("pipeline-grid");
      const fill = document.getElementById("pipeline-fill");
      const donePct = Math.round((doneStages.size / 26) * 100);
      fill.style.width = donePct + "%";
      grid.innerHTML = "";
      PIPELINE_STAGES.forEach(stage => {
        const isDone = doneStages.has(stage.n);
        const isActive = !isDone && activeStages.has(stage.n);
        const cls = isDone ? "s-done" : isActive ? "s-active" : "s-future";
        const div = document.createElement("div");
        div.className = "stage-tile " + cls;
        div.innerHTML =
          "<div class='stage-num'>" + (isDone ? "&#10003;" : stage.n) + "</div>" +
          "<div class='stage-info'>" +
            "<div class='stage-name'>" + stage.name + "</div>" +
            "<div class='stage-note'>" + stage.note + "</div>" +
          "</div>";
        grid.appendChild(div);
      });
    }

    // pipeline toggle
    document.getElementById("pipeline-toggle").addEventListener("click", () => {
      const body = document.getElementById("pipeline-body");
      const arrow = document.getElementById("pipeline-arrow");
      body.classList.toggle("open");
      arrow.classList.toggle("open");
    });

    function renderRun(result) {
      latestRun = result;
      summaryEl.textContent = result.summary;
      acceptedEl.textContent = String(result.accepted_claims);
      rejectedEl.textContent = String(result.rejected_claims);
      contradictionEl.textContent = String(result.contradictions.length);
      auditLogEl.textContent = JSON.stringify(result.audit_entries, null, 2);
      downloadButton.onclick = () => {
        const blob = new Blob([JSON.stringify(result.audit_entries, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "open-production-audit.json";
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 500);
      };
      // VP.1 — surface production_id and console link
      const pidPanel = document.getElementById("prod-id-panel");
      const pidDisplay = document.getElementById("prod-id-display");
      const consoleLink = document.getElementById("prod-console-link");
      if (result.production_id) {
        pidDisplay.textContent = result.production_id;
        consoleLink.href = "/?view=console&production_id=" + result.production_id;
        pidPanel.classList.remove("hidden");
      } else {
        pidPanel.classList.add("hidden");
      }
      show(storyPanel);
      // Render pipeline wizard
      const doneStages = new Set(DEMO_DONE_STAGES);
      if (result.research_result && result.research_result.gate_passed) doneStages.add(2);
      if (result.env_result && result.env_result.proposals) doneStages.add(9);
      if (result.shot_plan_result && result.shot_plan_result.shots) doneStages.add(10);
      if (result.reviewer_results && result.reviewer_results.length) doneStages.add(23);
      if (result.accepted_claims > 0) doneStages.add(25);
      renderPipeline(doneStages, DEMO_ACTIVE_STAGES);
      show(document.getElementById("pipeline-panel"));
    }

    async function showAngles(payload) {
      setStatus("Generating creative angles...");
      hide(storyPanel);
      try {
        const response = await fetch("/api/reframe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          throw new Error("The demo could not generate angles.");
        }
        const data = await response.json();
        currentPayload = payload;
        renderAngles(data.angles);
        setStatus("Pick an angle to continue.");
      } catch (error) {
        setStatus(error.message);
      }
    }

    async function finalizeRun(angleId) {
      if (!currentPayload) {
        setStatus("Start with the form first.");
        return;
      }
      setStatus("Running the evidence gates...");
      angleGrid.querySelectorAll(".card").forEach((card) => {
        card.classList.toggle("selected", card.dataset.angleId === angleId);
      });
      try {
        const response = await fetch("/api/finalize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...currentPayload, chosen_angle_id: angleId }),
        });
        if (!response.ok) {
          throw new Error("The final demo run did not complete.");
        }
        const data = await response.json();
        renderRun(data);
        setStatus("Done. The audit trail is ready.");
      } catch (error) {
        setStatus(error.message);
      }
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      showAngles(readPayload());
    });

    sampleButton.addEventListener("click", () => {
      topicField.value = DEFAULT_TOPIC;
      audienceField.value = DEFAULT_AUDIENCE;
      toneField.value = DEFAULT_TONE;
      setStatus("Sample topic loaded.");
    });

    resetButton.addEventListener("click", () => {
      topicField.value = DEFAULT_TOPIC;
      audienceField.value = DEFAULT_AUDIENCE;
      toneField.value = DEFAULT_TONE;
      hide(anglesPanel);
      hide(storyPanel);
      hide(document.getElementById("pipeline-panel"));
      angleGrid.innerHTML = "";
      auditLogEl.textContent = "";
      summaryEl.textContent = "";
      acceptedEl.textContent = "0";
      rejectedEl.textContent = "0";
      contradictionEl.textContent = "0";
      currentPayload = null;
      setStatus("Ready for a new run.");
    });

    startOverButton.addEventListener("click", () => {
      resetButton.click();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    topicField.value = DEFAULT_TOPIC;
    audienceField.value = DEFAULT_AUDIENCE;
    toneField.value = DEFAULT_TONE;
    setStatus("Enter a topic and choose a direction.");
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Director's Canvas HTML (view=canvas) — View 1 of the 5 views
# ---------------------------------------------------------------------------

CANVAS_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Director's Canvas — Open Production</title>
  <style>
    :root {
      --bg: #07111f; --panel: rgba(10,18,33,0.82);
      --panel-border: rgba(137,181,255,0.18);
      --text: #f5f7fb; --muted: #9db0cc;
      --accent: #7fd4c1; --radius: 20px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh;
      font-family: "Gill Sans","Trebuchet MS",sans-serif;
      color: var(--text);
      background: linear-gradient(160deg,#08111f 0%,#0c1a2f 48%,#060a13 100%);
    }
    .shell { width: min(1200px,calc(100% - 32px)); margin: 0 auto; padding: 20px 0 48px; }
    .topbar {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 20px; flex-wrap: wrap; gap: 10px;
    }
    .view-nav { display: flex; gap: 8px; flex-wrap: wrap; }
    .view-link {
      padding: 6px 14px; border-radius: 999px;
      border: 1px solid var(--panel-border);
      background: rgba(255,255,255,0.07);
      color: var(--accent); text-decoration: none; font-size: 0.88rem;
    }
    .view-link:hover { background: rgba(127,212,193,0.12); }
    .view-link.active { background: rgba(127,212,193,0.18); border-color: var(--accent); }
    h1 { font-size: 1.6rem; margin: 0; }
    .subtitle { color: var(--muted); font-size: 0.88rem; margin: 3px 0 0; }
    .canvas {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
    }
    .scene-card {
      background: var(--panel); border: 1px solid var(--panel-border);
      border-radius: var(--radius); padding: 16px; min-height: 180px;
    }
    .scene-title {
      font-size: 1.0rem; font-weight: 700; margin: 0 0 10px;
      padding-bottom: 8px; border-bottom: 1px solid var(--panel-border);
      color: var(--accent);
    }
    .shot-card {
      background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px; padding: 10px 12px; margin-bottom: 8px; cursor: pointer;
    }
    .shot-card:hover { background: rgba(127,212,193,0.08); }
    .shot-title { font-size: 0.88rem; font-weight: 600; }
    .shot-meta { color: var(--muted); font-size: 0.78rem; margin-top: 3px; }
    .badge {
      display: inline-block; padding: 2px 8px; border-radius: 999px;
      font-size: 0.72rem; font-weight: 600; margin-left: 6px;
    }
    .b-draft { background: rgba(240,184,93,0.15); color: #fde8a0; }
    .b-approved { background: rgba(127,212,193,0.15); color: #c0f4e7; }
    .empty { color: var(--muted); font-style: italic; font-size: 0.9rem; padding: 20px 0; }
    .prod-id { color: var(--muted); font-size: 0.8rem; margin-bottom: 16px; }
    .footer { margin-top: 24px; color: var(--muted); font-size: 0.85rem; }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <div>
        <h1>Director's Canvas</h1>
        <p class="subtitle">Spatial overview of scenes and shots — production <code>{{PROD_ID_LABEL}}</code></p>
      </div>
      <nav class="view-nav">
        <a class="view-link active" href="{{CANVAS_LINK}}">Director's Canvas</a>
        <a class="view-link" href="{{GUIDED_LINK}}">Guided Flow</a>
        <a class="view-link" href="{{CONSOLE_LINK}}">Agent Console</a>
      </nav>
    </div>

    <p class="prod-id" id="prod-meta">Loading production…</p>

    <div class="canvas" id="canvas">
      <div class="empty">Loading scenes…</div>
    </div>

    <div class="footer">
      Director's Canvas — Open Production. All views read from the same Production state.
    </div>
  </main>
  <script>
    const PROD_ID = "{{PROD_ID_JS}}";

    async function loadCanvas() {
      const meta = document.getElementById("prod-meta");
      const canvas = document.getElementById("canvas");
      if (!PROD_ID) {
        meta.textContent = "No production_id. Start a production from Guided Flow.";
        canvas.innerHTML = '<div class="empty">Open a production from Guided Flow to see its scenes here.</div>';
        return;
      }
      try {
        const r = await fetch("/api/production/" + PROD_ID + "/status");
        if (!r.ok) { meta.textContent = "Production not found."; return; }
        const prod = await r.json();
        meta.textContent = (prod.title || "Untitled") + " · " + (prod.state || "DRAFT") + " · " + PROD_ID;
        const scenes = prod.scenes || [];
        if (!scenes.length) {
          canvas.innerHTML = '<div class="empty">No scenes yet. Add scenes via Guided Flow or the API.</div>';
          return;
        }
        canvas.innerHTML = scenes.map(scene => {
          const shots = scene.shots || [];
          const shotCards = shots.length
            ? shots.map(s =>
                "<div class='shot-card'>" +
                  "<div class='shot-title'>" + (s.title || s.id) +
                    "<span class='badge " + (s.status === "approved" ? "b-approved" : "b-draft") + "'>" + (s.status || "draft") + "</span>" +
                  "</div>" +
                  "<div class='shot-meta'>" + (s.intent || "") + "</div>" +
                "</div>"
              ).join("")
            : "<div class='shot-card'><div class='shot-meta' style='font-style:italic;'>No shots yet</div></div>";
          return "<div class='scene-card'>" +
            "<div class='scene-title'>" + (scene.title || scene.id) + "</div>" +
            shotCards +
            "</div>";
        }).join("");
      } catch(e) {
        canvas.innerHTML = "<div class='empty'>Could not load canvas.</div>";
      }
    }

    loadCanvas();
    setInterval(loadCanvas, 8000);
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Agent Console HTML (view=console)
# ---------------------------------------------------------------------------

CONSOLE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agent Console — Open Production</title>
  <style>
    :root {
      --bg: #07111f; --panel: rgba(10,18,33,0.82);
      --panel-border: rgba(137,181,255,0.18);
      --text: #f5f7fb; --muted: #9db0cc;
      --accent: #7fd4c1; --radius: 24px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh;
      font-family: "Gill Sans","Trebuchet MS",sans-serif;
      color: var(--text);
      background: linear-gradient(160deg,#08111f 0%,#0c1a2f 48%,#060a13 100%);
    }
    .shell { width: min(1100px,calc(100% - 32px)); margin: 0 auto; padding: 28px 0 48px; }
    .topbar {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
    }
    .view-link {
      padding: 8px 18px; border-radius: 999px;
      border: 1px solid var(--panel-border);
      background: rgba(255,255,255,0.07);
      color: var(--accent); text-decoration: none; font-size: 0.95rem;
    }
    .view-link:hover { background: rgba(127,212,193,0.12); }
    h1 { font-size: 1.9rem; margin: 0; }
    .subtitle { color: var(--muted); margin: 4px 0 0; font-size: 0.97rem; }
    .panel {
      background: var(--panel); border: 1px solid var(--panel-border);
      border-radius: var(--radius); padding: 20px; margin-bottom: 18px;
    }
    .panel-title { font-size: 1.2rem; margin: 0 0 12px; }
    .status-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 18px; }
    .stat { padding: 12px 16px; border-radius: 16px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); }
    .stat b { display: block; font-size: 1.5rem; color: #fff; }
    .stat span { color: var(--muted); font-size: 0.9rem; }
    /* ---- main two-column layout ---- */
    .console-layout { display: grid; grid-template-columns: 220px 1fr; gap: 16px; }
    .actor-rail {
      background: var(--panel); border: 1px solid var(--panel-border);
      border-radius: var(--radius); padding: 16px; align-self: start;
    }
    .actor-rail-title { font-size: 0.88rem; font-weight: 600; color: var(--muted); letter-spacing: 0.04em; text-transform: uppercase; margin: 0 0 10px; }
    .actor-btn {
      display: flex; align-items: center; justify-content: space-between;
      width: 100%; padding: 8px 10px; margin-bottom: 4px;
      border-radius: 12px; border: 1px solid transparent;
      background: rgba(255,255,255,0.04); color: var(--text);
      cursor: pointer; font: inherit; font-size: 0.88rem; text-align: left;
    }
    .actor-btn:hover { background: rgba(127,212,193,0.08); }
    .actor-btn.active { background: rgba(127,212,193,0.13); border-color: rgba(127,212,193,0.25); color: #c0f4e7; }
    .actor-badge { background: rgba(255,255,255,0.1); border-radius: 999px; padding: 1px 7px; font-size: 0.76rem; }
    /* ---- right column: tabs + panes ---- */
    .tab-bar { display: flex; gap: 4px; margin-bottom: 14px; flex-wrap: wrap; }
    .tab-btn {
      padding: 6px 14px; border-radius: 999px; border: 1px solid var(--panel-border);
      background: rgba(255,255,255,0.05); color: var(--muted);
      cursor: pointer; font: inherit; font-size: 0.88rem;
    }
    .tab-btn.active { background: rgba(127,212,193,0.15); border-color: rgba(127,212,193,0.3); color: #c0f4e7; }
    .tab-pane { display: none; }
    .tab-pane.active { display: block; }
    /* ---- event list ---- */
    .event-list { list-style: none; margin: 0; padding: 0; }
    .event-item {
      display: grid; grid-template-columns: 160px 1fr auto;
      gap: 10px; align-items: baseline;
      padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
      font-size: 0.93rem;
    }
    .event-item.hidden { display: none; }
    .event-item:last-child { border-bottom: none; }
    .evt-ts { color: var(--muted); font-size: 0.82rem; font-variant-numeric: tabular-nums; }
    .evt-gate { color: #a7c8ff; }
    .evt-status { padding: 3px 9px; border-radius: 999px; font-size: 0.8rem; }
    .s-accepted,.s-publish_ok,.s-contract_passed { background: rgba(127,212,193,0.15); color: #c0f4e7; }
    .s-rejected,.s-publish_rejected,.s-contract_violated,.s-production_blocked { background: rgba(255,122,122,0.15); color: #ffb3b3; }
    .s-contradiction_detected { background: rgba(240,184,93,0.15); color: #fde8a0; }
    /* ---- per-agent proposal panels ---- */
    .proposals-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(300px,1fr)); gap: 14px; }
    .proposal-card {
      background: rgba(255,255,255,0.04); border: 1px solid var(--panel-border);
      border-radius: 18px; padding: 16px;
    }
    .proposal-card.state-approved { border-color: rgba(127,212,193,0.4); background: rgba(127,212,193,0.06); }
    .proposal-card.state-adjusted { border-color: rgba(240,184,93,0.4); background: rgba(240,184,93,0.06); }
    .proposal-card.state-overridden { border-color: rgba(255,122,122,0.35); background: rgba(255,122,122,0.05); }
    .proposal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; flex-wrap: wrap; gap: 6px; }
    .proposal-agent { font-size: 0.8rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); }
    .proposal-stage { font-size: 0.78rem; padding: 2px 8px; border-radius: 999px; background: rgba(167,200,255,0.12); color: #a7c8ff; }
    .proposal-title { font-size: 1.0rem; font-weight: 600; margin: 0 0 6px; color: var(--text); }
    .proposal-summary { font-size: 0.88rem; color: var(--muted); margin-bottom: 12px; line-height: 1.5; }
    .proposal-options { display: flex; flex-direction: column; gap: 5px; margin-bottom: 12px; }
    .option-row {
      display: flex; align-items: center; gap: 8px;
      padding: 7px 10px; border-radius: 10px; cursor: pointer;
      background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);
      font-size: 0.85rem; color: var(--text); transition: background 0.15s;
    }
    .option-row:hover { background: rgba(127,212,193,0.09); }
    .option-row.selected { background: rgba(127,212,193,0.14); border-color: rgba(127,212,193,0.28); }
    .option-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.2); flex-shrink: 0; }
    .option-row.selected .option-dot { background: #7fd4c1; }
    .proposal-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .btn-approve {
      flex: 1; padding: 8px 12px; border-radius: 12px; border: none;
      background: rgba(127,212,193,0.18); color: #c0f4e7;
      cursor: pointer; font: inherit; font-size: 0.85rem; font-weight: 600;
    }
    .btn-approve:hover { background: rgba(127,212,193,0.28); }
    .btn-adjust {
      flex: 1; padding: 8px 12px; border-radius: 12px;
      border: 1px solid rgba(240,184,93,0.25); background: rgba(240,184,93,0.08); color: #fde8a0;
      cursor: pointer; font: inherit; font-size: 0.85rem;
    }
    .btn-adjust:hover { background: rgba(240,184,93,0.15); }
    .btn-override {
      padding: 8px 12px; border-radius: 12px;
      border: 1px solid rgba(255,122,122,0.22); background: rgba(255,122,122,0.06); color: #ffb3b3;
      cursor: pointer; font: inherit; font-size: 0.85rem;
    }
    .btn-override:hover { background: rgba(255,122,122,0.14); }
    .proposal-status-bar {
      font-size: 0.78rem; padding: 4px 10px; border-radius: 999px;
      display: inline-block; margin-top: 8px; font-weight: 600;
    }
    .ps-pending { background: rgba(255,255,255,0.08); color: var(--muted); }
    .ps-approved { background: rgba(127,212,193,0.18); color: #c0f4e7; }
    .ps-adjusted { background: rgba(240,184,93,0.18); color: #fde8a0; }
    .ps-overridden { background: rgba(255,122,122,0.18); color: #ffb3b3; }
    .adjust-area { display: none; margin-top: 10px; }
    .adjust-area.open { display: block; }
    .adjust-input {
      width: 100%; border-radius: 10px; border: 1px solid rgba(255,255,255,0.14);
      background: rgba(255,255,255,0.07); color: var(--text);
      padding: 8px 12px; font: inherit; font-size: 0.85rem; resize: vertical; min-height: 60px;
    }
    .btn-confirm-adjust {
      margin-top: 6px; padding: 7px 14px; border-radius: 10px; border: none;
      background: rgba(240,184,93,0.22); color: #fde8a0;
      cursor: pointer; font: inherit; font-size: 0.83rem;
    }
    /* ---- empty / footer ---- */
    .empty { color: var(--muted); font-style: italic; }
    .footer { margin-top: 18px; color: var(--muted); font-size: 0.9rem; }
    @media(max-width:700px) {
      .status-row { grid-template-columns: repeat(2,1fr); }
      .event-item { grid-template-columns: 1fr; }
      .console-layout { grid-template-columns: 1fr; }
      .proposals-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <div>
        <h1>Agent Console</h1>
        <p class="subtitle">Proposal panels &amp; audit log — production <code>{{PROD_ID_LABEL}}</code></p>
      </div>
      <a class="view-link" href="{{GUIDED_LINK}}">&#8592; Switch to Guided Flow</a>
    </div>

    <div class="status-row" id="status-row">
      <div class="stat"><b id="s-state">—</b><span>state</span></div>
      <div class="stat"><b id="s-events">—</b><span>audit events</span></div>
      <div class="stat"><b id="s-proposals">—</b><span>proposals</span></div>
      <div class="stat"><b id="s-title">—</b><span>production title</span></div>
    </div>

    <div class="console-layout" data-test-actor-panel="true">
      <!-- left: actor filter rail -->
      <aside class="actor-rail">
        <p class="actor-rail-title">Actors</p>
        <button class="actor-btn active" id="actor-all" data-actor="">All</button>
        <div id="actor-buttons"></div>
      </aside>

      <!-- right: tabbed panes -->
      <div>
        <div class="tab-bar" data-test-tab-bar="true">
          <button class="tab-btn active" data-tab="proposals">Agent Proposals</button>
          <button class="tab-btn" data-tab="events">Audit Events</button>
        </div>

        <!-- proposals pane -->
        <div class="tab-pane active" id="pane-proposals">
          <div class="proposals-grid" id="proposals-grid" data-test-proposals-grid="true">
            <p class="empty">Loading proposals…</p>
          </div>
        </div>

        <!-- events pane -->
        <div class="tab-pane" id="pane-events">
          <div class="panel">
            <div class="panel-title">Recent Events (last 20)</div>
            <ul class="event-list" id="event-list">
              <li class="empty">Loading…</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      Agent Console — Open Production. Proposals and events auto-refresh every 5 s.
      <a class="view-link" style="margin-left:12px;" href="{{GUIDED_LINK}}">Go to Guided Flow</a>
    </div>
  </main>
  <script>
    const PROD_ID = "{{PROD_ID_JS}}";
    const REFRESH_MS = 5000;

    // ---- tab switching ----
    document.querySelectorAll(".tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        const pane = document.getElementById("pane-" + btn.dataset.tab);
        if (pane) pane.classList.add("active");
      });
    });

    // ---- helpers ----
    function statusClass(s) {
      const safe = (s || "").replace(/[^a-z0-9_]/g,"");
      return "evt-status s-" + safe;
    }

    // ---- status header ----
    async function fetchStatus() {
      if (!PROD_ID) return;
      try {
        const r = await fetch("/api/production/" + PROD_ID + "/status");
        if (!r.ok) return;
        const d = await r.json();
        document.getElementById("s-state").textContent = d.state || "—";
        document.getElementById("s-title").textContent = (d.title || d.name || "untitled").slice(0,28);
      } catch(_) {}
    }

    // ---- actor filter ----
    let _selectedActor = "";

    function applyActorFilter(actor) {
      _selectedActor = actor;
      document.getElementById("actor-all").classList.toggle("active", actor === "");
      document.querySelectorAll(".actor-btn[data-actor]").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.actor === actor && actor !== "");
      });
      document.querySelectorAll("#event-list li[data-actor]").forEach(li => {
        if (!actor || li.dataset.actor === actor) li.classList.remove("hidden");
        else li.classList.add("hidden");
      });
      // also filter proposal cards
      document.querySelectorAll(".proposal-card[data-agent]").forEach(card => {
        if (!actor || card.dataset.agent === actor) card.style.display = "";
        else card.style.display = "none";
      });
    }

    document.getElementById("actor-all").addEventListener("click", () => applyActorFilter(""));

    function updateActorRail(agents) {
      const container = document.getElementById("actor-buttons");
      const existing = new Set(Array.from(container.querySelectorAll(".actor-btn")).map(b => b.dataset.actor));
      agents.forEach(({actor, count}) => {
        if (existing.has(actor)) {
          const btn = container.querySelector('.actor-btn[data-actor="' + actor + '"]');
          if (btn) btn.querySelector(".actor-badge").textContent = count;
          return;
        }
        const btn = document.createElement("button");
        btn.className = "actor-btn";
        btn.dataset.actor = actor;
        btn.innerHTML = actor.replace(/_?agent$/i,"").slice(0,16) + '<span class="actor-badge">' + count + '</span>';
        btn.addEventListener("click", () => applyActorFilter(actor));
        container.appendChild(btn);
      });
    }

    // ---- proposal state (client-side: pending | approved | adjusted | overridden) ----
    const _proposalState = {};   // keyed by proposal_id
    const _proposalChoice = {};  // keyed by proposal_id → chosen option index

    function getState(pid) { return _proposalState[pid] || "pending"; }

    function setCardState(card, state, note) {
      const pid = card.dataset.proposalId;
      _proposalState[pid] = state;
      card.className = "proposal-card state-" + state;
      const bar = card.querySelector(".proposal-status-bar");
      if (bar) {
        bar.className = "proposal-status-bar ps-" + state;
        bar.textContent = state.charAt(0).toUpperCase() + state.slice(1) + (note ? " — " + note : "");
      }
    }

    function buildProposalCard(p) {
      const pid = p.id || (p.agent + "_" + p.stage);
      const state = getState(pid);
      const chosenIdx = _proposalChoice[pid] !== undefined ? _proposalChoice[pid] : 0;
      const options = p.options || [];

      const optionsHtml = options.map((opt, i) =>
        "<div class='option-row" + (i === chosenIdx ? " selected" : "") + "' data-idx='" + i + "'>" +
          "<span class='option-dot'></span>" +
          "<span>" + (opt.label || opt.name || opt.summary || JSON.stringify(opt)).slice(0,80) + "</span>" +
        "</div>"
      ).join("");

      const card = document.createElement("div");
      card.className = "proposal-card state-" + state;
      card.dataset.proposalId = pid;
      card.dataset.agent = p.agent || "system";
      card.innerHTML =
        "<div class='proposal-header'>" +
          "<span class='proposal-agent'>" + (p.agent || "agent").replace(/_?agent$/i,"") + "</span>" +
          "<span class='proposal-stage'>Stage " + (p.stage || "?") + "</span>" +
        "</div>" +
        "<div class='proposal-title'>" + (p.title || p.agent) + "</div>" +
        "<div class='proposal-summary'>" + (p.summary || "").slice(0,140) + "</div>" +
        (options.length ? "<div class='proposal-options'>" + optionsHtml + "</div>" : "") +
        "<div class='proposal-actions'>" +
          "<button class='btn-approve' data-test-approve='true'>Approve</button>" +
          "<button class='btn-adjust'>Adjust…</button>" +
          "<button class='btn-override'>Override</button>" +
        "</div>" +
        "<div class='adjust-area' id='adj-" + pid + "'>" +
          "<textarea class='adjust-input' placeholder='Describe your adjustment…'></textarea>" +
          "<button class='btn-confirm-adjust'>Confirm adjustment</button>" +
        "</div>" +
        "<span class='proposal-status-bar ps-" + state + "'>" +
          (state.charAt(0).toUpperCase() + state.slice(1)) +
        "</span>";

      // option selection
      card.querySelectorAll(".option-row").forEach(row => {
        row.addEventListener("click", () => {
          _proposalChoice[pid] = parseInt(row.dataset.idx, 10);
          card.querySelectorAll(".option-row").forEach(r => r.classList.toggle("selected", r === row));
        });
      });

      // approve
      card.querySelector(".btn-approve").addEventListener("click", () => {
        const chosen = options[_proposalChoice[pid] || 0];
        setCardState(card, "approved", chosen ? (chosen.label || chosen.name || "option " + ((_proposalChoice[pid]||0)+1)) : undefined);
        logAction(p, "approved", _proposalChoice[pid] || 0);
      });

      // adjust
      const adjArea = card.querySelector(".adjust-area");
      card.querySelector(".btn-adjust").addEventListener("click", () => {
        adjArea.classList.toggle("open");
      });
      card.querySelector(".btn-confirm-adjust").addEventListener("click", () => {
        const note = card.querySelector(".adjust-input").value.trim() || "adjusted";
        setCardState(card, "adjusted", note.slice(0,40));
        adjArea.classList.remove("open");
        logAction(p, "adjusted", null, note);
      });

      // override
      card.querySelector(".btn-override").addEventListener("click", () => {
        setCardState(card, "overridden");
        logAction(p, "overridden");
      });

      return card;
    }

    function logAction(proposal, action, optionIdx, note) {
      // POST to /api/production/<id>/approve — best-effort, no UI feedback needed
      if (!PROD_ID) return;
      const body = {
        proposal_id: proposal.id || (proposal.agent + "_" + proposal.stage),
        agent: proposal.agent,
        stage: proposal.stage,
        action: action,
        option_index: optionIdx !== null && optionIdx !== undefined ? optionIdx : null,
        note: note || null,
      };
      fetch("/api/production/" + PROD_ID + "/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).catch(() => {});
    }

    // ---- fetch proposals ----
    let _lastProposalIds = new Set();

    async function fetchProposals() {
      const grid = document.getElementById("proposals-grid");
      if (!PROD_ID) {
        grid.innerHTML = '<p class="empty">No production_id. Open from Guided Flow.</p>';
        return;
      }
      try {
        const r = await fetch("/api/production/" + PROD_ID + "/proposals");
        if (!r.ok) { grid.innerHTML = '<p class="empty">No proposals yet.</p>'; return; }
        const data = await r.json();
        const proposals = data.proposals || [];
        document.getElementById("s-proposals").textContent = proposals.length;
        if (!proposals.length) { grid.innerHTML = '<p class="empty">No proposals available yet. Run the demo first.</p>'; return; }

        // build actor rail from proposals
        const agentCounts = {};
        proposals.forEach(p => { const a = p.agent || "system"; agentCounts[a] = (agentCounts[a]||0) + 1; });
        updateActorRail(Object.entries(agentCounts).map(([actor,count]) => ({actor,count})));

        // only re-render cards that are new (preserve user interactions on existing)
        const currentIds = new Set(proposals.map(p => p.id || (p.agent + "_" + p.stage)));
        const newIds = [...currentIds].filter(id => !_lastProposalIds.has(id));
        if (newIds.size === 0 && _lastProposalIds.size > 0) return; // nothing new

        // full render when something changed
        grid.innerHTML = "";
        proposals.forEach(p => {
          const card = buildProposalCard(p);
          grid.appendChild(card);
        });
        _lastProposalIds = currentIds;
        applyActorFilter(_selectedActor);
      } catch(_) {
        grid.innerHTML = '<p class="empty">Could not load proposals.</p>';
      }
    }

    // ---- audit event log ----
    async function fetchLog() {
      const list = document.getElementById("event-list");
      if (!PROD_ID) {
        list.innerHTML = '<li class="empty">No production_id in URL. Open from Guided Flow.</li>';
        return;
      }
      try {
        const r = await fetch("/api/production/" + PROD_ID + "/log");
        if (!r.ok) { list.innerHTML = '<li class="empty">Could not load events.</li>'; return; }
        const entries = await r.json();
        document.getElementById("s-events").textContent = entries.length;
        if (!entries.length) { list.innerHTML = '<li class="empty">No events yet.</li>'; return; }
        // update actor rail from log too
        const agentCounts = {};
        entries.forEach(e => { const a = e.actor || "system"; agentCounts[a] = (agentCounts[a]||0) + 1; });
        updateActorRail(Object.entries(agentCounts).map(([actor,count]) => ({actor,count})));
        const last20 = entries.slice(-20).reverse();
        list.innerHTML = last20.map(e => {
          const ts = (e.ts || "").slice(11,19);
          const gate = e.gate_name || e.action_type || "event";
          const status = e.decision_status || e.action_type || "";
          const reason = e.reason ? (" — " + e.reason.slice(0,60)) : "";
          const actor = e.actor || "system";
          const hidden = (_selectedActor && actor !== _selectedActor) ? " hidden" : "";
          return "<li class='event-item" + hidden + "' data-actor='" + actor + "'>" +
            "<span class='evt-ts'>" + ts + "</span>" +
            "<span class='evt-gate'>" + gate + reason + "</span>" +
            "<span class='" + statusClass(status) + "'>" + status + "</span>" +
            "</li>";
        }).join("");
      } catch(_) {
        list.innerHTML = '<li class="empty">Error loading events.</li>';
      }
    }

    async function refresh() { await fetchStatus(); await fetchProposals(); await fetchLog(); }
    refresh();
    setInterval(refresh, REFRESH_MS);
  </script>
</body>
</html>
"""


def render_index_html(view: str = "guided", production_id: str = "") -> str:
    """Return the landing page HTML for the requested view.

    Args:
        view: "guided" (default), "console", or "canvas"
        production_id: optional production ID to thread through the page
    """
    pid = production_id or ""
    if view == "console":
        guided_qs = f"?view=guided&production_id={pid}" if pid else "?view=guided"
        label = pid if pid else "(none)"
        return (
            CONSOLE_HTML
            .replace("{{PROD_ID_LABEL}}", label)
            .replace("{{PROD_ID_JS}}", pid)
            .replace("{{GUIDED_LINK}}", guided_qs)
        )
    if view == "canvas":
        guided_qs = f"?view=guided&production_id={pid}" if pid else "?view=guided"
        console_qs = f"?view=console&production_id={pid}" if pid else "?view=console"
        canvas_qs = f"?view=canvas&production_id={pid}" if pid else "?view=canvas"
        label = pid if pid else "(none)"
        return (
            CANVAS_HTML
            .replace("{{PROD_ID_LABEL}}", label)
            .replace("{{PROD_ID_JS}}", pid)
            .replace("{{GUIDED_LINK}}", guided_qs)
            .replace("{{CONSOLE_LINK}}", console_qs)
            .replace("{{CANVAS_LINK}}", canvas_qs)
        )
    # Default: guided flow (existing page, extended with view-switcher link)
    console_qs = f"?view=console&production_id={pid}" if pid else "?view=console"
    html = (
        INDEX_HTML
        .replace("{{DEFAULT_TOPIC}}", DEFAULT_TOPIC)
        .replace("{{DEFAULT_AUDIENCE}}", DEFAULT_AUDIENCE)
        .replace("{{DEFAULT_TONE}}", DEFAULT_TONE)
        .replace("{{CONSOLE_LINK}}", console_qs)
        .replace("{{PROD_ID_JS}}", pid)
    )
    return html


def _json_response(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    """Send a JSON response with appropriate headers.

    Always sets Cache-Control: no-store and CORS headers so the Vite dev
    proxy and any same-origin fetch work without additional configuration.
    """
    try:
        body = json.dumps(payload, default=str).encode("utf-8")
    except (TypeError, ValueError):
        body = b'{"error": "serialization failed"}'
        status = 500
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Access-Control-Allow-Origin", _CORS_ORIGIN)
    handler.end_headers()
    handler.wfile.write(body)


class _InvalidJsonBody(ValueError):
    """Raised when the request body cannot be parsed as a JSON object."""


class _BodyTooLarge(ValueError):
    """Raised when Content-Length exceeds the configured cap."""


# Hard upper bound for any request body (1 MB). Bodies larger than this are
# rejected with HTTP 413 instead of being silently truncated.
MAX_BODY_BYTES = 1_048_576


def _validate_production_id(prod_id):
    """Return prod_id if it is safe to use as a filesystem path component.

    Production IDs are generated as "<prefix>_<12 hex>" (see
    ``production_service._id``). Anything containing path separators,
    parent-traversal sequences, or characters outside the safe alphabet is
    rejected so it can never reach ``Path(storage_dir) / prod_id`` operations.
    """
    if not isinstance(prod_id, str) or not _PRODUCTION_ID_RE.match(prod_id):
        raise ValueError(
            "production_id must match [A-Za-z][A-Za-z0-9_-]{2,63}; "
            f"got {prod_id!r}"
        )
    return prod_id


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    """Read and parse the JSON request body as a dict.

    Raises:
        _InvalidJsonBody: if the body is not a valid JSON object. Callers
            should catch this and return HTTP 400 so the client knows the
            payload was rejected, instead of silently defaulting.

    Reads exactly Content-Length bytes when the header is present.
    If Content-Length is missing or zero, returns an empty dict.
    Caps body at 1 MB to prevent memory exhaustion from malformed requests.
"""
    raw_length = handler.headers.get("Content-Length", "0") or "0"
    try:
        length = int(raw_length)
    except ValueError:
        length = 0
    if length < 0:
        raise _InvalidJsonBody("negative Content-Length")
    if length > MAX_BODY_BYTES:
        raise _BodyTooLarge(
            f"request body of {length} bytes exceeds limit of {MAX_BODY_BYTES}"
        )
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    try:
        decoded = raw.decode("utf-8") if raw else "{}"
        data = json.loads(decoded or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise _InvalidJsonBody(f"request body is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise _InvalidJsonBody("request body must be a JSON object")
    return data

# Per-field length caps to prevent unbounded input from reaching downstream
# LLM calls or filesystem path components. Mirrors the schema limits enforced
# by ``ProductionService.init`` (title[:200]).
MAX_TOPIC_LEN = 400
MAX_AUDIENCE_LEN = 64
MAX_TONE_LEN = 64
MAX_ANGLE_ID_LEN = 64


def _normalize_payload(payload: dict) -> dict:
    """Coerce request payload into bounded strings with safe defaults.

    Empty / non-string values fall back to the demo defaults. Strings longer
    than the field cap are truncated so a single oversized field cannot blow
    up downstream LLM prompts or audit-trail entries.
    """
    def _clean(value, default, cap):
        s = str(value).strip() if value is not None else ""
        if not s:
            s = default
        return s[:cap]

    topic = _clean(payload.get("topic"), DEFAULT_TOPIC, MAX_TOPIC_LEN)
    audience = _clean(payload.get("audience"), DEFAULT_AUDIENCE, MAX_AUDIENCE_LEN)
    tone = _clean(payload.get("tone"), DEFAULT_TONE, MAX_TONE_LEN)
    return {"topic": topic, "audience": audience, "tone": tone}


# ---------------------------------------------------------------------------
# Production API helpers
# ---------------------------------------------------------------------------

def _get_service(production_id: str | None = None) -> ProductionService | None:
    """Return a ProductionService rooted at the directory that owns production_id.

    Search order: output/public-demo, output/productions.
    Falls back to output/productions for new productions (creates it if absent).
    Returns None when ProductionService is not importable.
    """
    if not _SVC_AVAILABLE:
        return None
    if production_id:
        for parent in [_PUBLIC_DEMO_DIR, _STORAGE_DIR]:
            try:
                if parent.exists() and (parent / production_id).is_dir():
                    return ProductionService(storage_dir=parent)
            except OSError:
                continue
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return ProductionService(storage_dir=_STORAGE_DIR)


def _api_production_status(production_id: str) -> tuple[int, Any]:
    svc = _get_service(production_id)
    if svc is None:
        return 503, {"error": "ProductionService not available"}
    try:
        status = svc.status(production_id)
        return 200, status
    except LookupError:
        return 404, {"error": f"Production {production_id!r} not found"}
    except Exception as exc:
        logger.exception("status(%s) failed", production_id)
        return 500, {"error": "Internal server error"}


def _api_production_log(production_id: str) -> tuple[int, Any]:
    svc = _get_service(production_id)
    if svc is None:
        return 503, {"error": "ProductionService not available"}
    try:
        entries = svc.log(production_id)
        return 200, entries
    except LookupError:
        return 404, {"error": f"Production {production_id!r} not found"}
    except Exception as exc:
        logger.exception("log(%s) failed", production_id)
        return 500, {"error": "Internal server error"}


def _build_proposals_from_production(prod_dict: dict) -> list[dict]:
    """Derive a list of per-agent proposal objects from a Production status dict.

    Each entry is shaped for the Agent Console proposal panel:
      { id, agent, stage, title, summary, options: [{label}] }
    """
    proposals: list[dict] = []

    def _add(agent: str, stage: int, title: str, summary: str, options: list[str]) -> None:
        proposals.append({
            "id": f"{agent}_stage{stage}",
            "agent": agent,
            "stage": stage,
            "title": title,
            "summary": summary,
            "options": [{"label": o} for o in options],
        })

    # Stage 1 — intent
    intent = prod_dict.get("intent") or {}
    if intent:
        _add("IntentDocument", 1, "Production Intent",
             f"Topic: {str(intent.get('topic', ''))[:80]}",
             [f"Audience: {intent.get('audience','—')}", f"Tone: {intent.get('tone','—')}"])

    # Stage 5 — creative reframing (angles stored in reframing field if present)
    reframing = prod_dict.get("creative_reframing") or {}
    angles = reframing.get("angles") or []
    if angles:
        _add("CreativeReframing", 5, "Creative Angles",
             "Choose the narrative frame for this production.",
             [f"{a.get('id','')}: {a.get('name','')}" for a in angles[:3]])

    # Stage 9 — environments
    envs = prod_dict.get("environments") or []
    for env in envs[:3]:
        presets = env.get("lighting_presets") or []
        _add("EnvironmentArtistAgent", 9, f"Environment: {env.get('name','Location')}",
             f"Lighting presets and time-of-day variants for {env.get('name','Primary Location')}.",
             presets[:3] if presets else ["interior natural", "golden hour", "night"])

    # Stage 10 — shots (first scene)
    scenes = prod_dict.get("scenes") or []
    for scene in scenes[:1]:
        shots = scene.get("shots") or []
        if shots:
            _add("ShotPlanningAgent", 10, f"Shot Plan: {scene.get('name', scene.get('id','Scene'))}",
                 f"{len(shots)} shots planned for this scene.",
                 [f"Shot {s.get('id','')}: {str(s.get('intent',''))[:60]}" for s in shots[:3]])

    # Stage 23 — reviewer (fake "approve the quality verdict" proposal)
    _add("ReviewerAgent", 23, "Quality Review Gate",
         "Reviewer ran 5 check types. Approve the final verdict to continue.",
         ["Accept verdict (proceed)", "Reject verdict (revise)", "Override (force-pass)"])

    # Stage 25 — publisher
    _add("PublisherAgent", 25, "Publication Manifest",
         "Choose the publication format for delivery.",
         ["Platform-native", "Multi-platform", "Archive"])

    return proposals


def _api_production_proposals(production_id: str) -> tuple[int, Any]:
    svc = _get_service(production_id)
    if svc is None:
        return 503, {"error": "ProductionService not available"}
    try:
        prod_dict = svc.status(production_id)
        proposals = _build_proposals_from_production(prod_dict)
        return 200, {"production_id": production_id, "proposals": proposals}
    except LookupError:
        return 404, {"error": f"Production {production_id!r} not found"}
    except Exception as exc:
        logger.exception("proposals(%s) failed", production_id)
        return 500, {"error": "Internal server error"}


def _api_production_approve(production_id: str, body: dict) -> tuple[int, Any]:
    """Record an approve/adjust/override decision.  Best-effort — no state mutation needed."""
    action = str(body.get("action") or "approved")
    agent = str(body.get("agent") or "unknown")
    stage = body.get("stage")
    note = str(body.get("note") or "")
    return 200, {
        "ok": True,
        "production_id": production_id,
        "agent": agent,
        "stage": stage,
        "action": action,
        "note": note,
    }


class DemoHTTPRequestHandler(BaseHTTPRequestHandler):
    """Serve the landing page and JSON demo endpoints."""

    server_version = "OpenProductionDemo/1.0"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler signature
        parsed = urlparse(self.path)
        route = parsed.path
        qs = parse_qs(parsed.query)

        if route in {"/", "/index.html"}:
            # If the React dist build exists, serve it instead of the legacy HTML page
            if _DIST_DIR.exists():
                if _serve_static(self, "/index.html"):
                    return
            view = (qs.get("view") or ["guided"])[0]
            production_id = (qs.get("production_id") or [""])[0]
            html = render_index_html(view=view, production_id=production_id).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html)
            return
        if route == "/healthz":
            _json_response(self, {"ok": True})
            return
        # /api/production/<id>/status
        if route.startswith("/api/production/") and route.endswith("/status"):
            parts = route.strip("/").split("/")  # ['api','production','<id>','status']
            if len(parts) == 4:
                try:
                    prod_id = _validate_production_id(parts[2])
                except ValueError as exc:
                    _json_response(self, {"error": "invalid_production_id", "detail": str(exc)}, status=400)
                    return
                status_code, body = _api_production_status(prod_id)
                _json_response(self, body, status=status_code)
                return
        # /api/production/<id>/log
        if route.startswith("/api/production/") and route.endswith("/log"):
            parts = route.strip("/").split("/")
            if len(parts) == 4:
                try:
                    prod_id = _validate_production_id(parts[2])
                except ValueError as exc:
                    _json_response(self, {"error": "invalid_production_id", "detail": str(exc)}, status=400)
                    return
                status_code, body = _api_production_log(prod_id)
                _json_response(self, body, status=status_code)
                return
        # /api/production/<id>/proposals
        if route.startswith("/api/production/") and route.endswith("/proposals"):
            parts = route.strip("/").split("/")
            if len(parts) == 4:
                try:
                    prod_id = _validate_production_id(parts[2])
                except ValueError as exc:
                    _json_response(self, {"error": "invalid_production_id", "detail": str(exc)}, status=400)
                    return
                status_code, body = _api_production_proposals(prod_id)
                _json_response(self, body, status=status_code)
                return
        # Non-/api path → try to serve the compiled React app from web/dist/
        if not route.startswith("/api"):
            if _serve_static(self, route):
                return
        _json_response(self, {"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler signature
        route = urlparse(self.path).path
        try:
            raw_payload = _read_json_body(self)
        except _BodyTooLarge as exc:
            _json_response(self, {"error": "payload_too_large", "detail": str(exc)}, status=413)
            return
        except _InvalidJsonBody as exc:
            _json_response(self, {"error": "invalid_json", "detail": str(exc)}, status=400)
            return
        payload = _normalize_payload(raw_payload)

        if route == "/api/reframe":
            try:
                angles = generate_angles(payload["topic"], payload["audience"], payload["tone"])
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("/api/reframe failed")
                _json_response(self, {"error": "Internal server error"}, status=500)
                return
            _json_response(self, {"topic": payload["topic"], "audience": payload["audience"], "tone": payload["tone"], "angles": angles})
            return

        if route == "/api/finalize":
            chosen_angle_id = str((raw_payload.get("chosen_angle_id") or "")).strip()[:MAX_ANGLE_ID_LEN]
            try:
                report = build_demo_report(
                    topic=payload["topic"],
                    audience=payload["audience"],
                    tone=payload["tone"],
                    chosen_angle_id=chosen_angle_id or None,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("/api/finalize failed")
                _json_response(self, {"error": "Internal server error"}, status=500)
                return
            _json_response(self, report)
            return

        # /api/production/<id>/approve
        if route.startswith("/api/production/") and route.endswith("/approve"):
            parts = route.strip("/").split("/")
            if len(parts) == 4:
                try:
                    prod_id = _validate_production_id(parts[2])
                except ValueError as exc:
                    _json_response(self, {"error": "invalid_production_id", "detail": str(exc)}, status=400)
                    return
                status_code, resp_body = _api_production_approve(prod_id, raw_payload)
                _json_response(self, resp_body, status=status_code)
                return

        _json_response(self, {"error": "Not found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - stdlib signature
        """Suppress routine per-request access logs to keep demo output clean.

        Errors (4xx, 5xx) are routed to the module logger so they are never
        silently swallowed.
        """
        # format string starts with the status code token; pull it out to decide
        # whether this is worth logging.  The stdlib passes e.g.
        # "GET / HTTP/1.1" 200 - or "POST /api/finalize HTTP/1.1" 500 -.
        # We only suppress 1xx/2xx/3xx.
        try:
            msg = format % args
            code = int(msg.split(chr(34))[2].split()[0]) if chr(34) in msg else 0
            if code >= 400:
                logger.warning("http %s", msg)
        except Exception:
            pass

    def log_error(self, format: str, *args: Any) -> None:  # noqa: A003 - stdlib signature
        """Always route server errors through the module logger."""
        try:
            logger.error(format, *args)
        except Exception:
            logger.exception("log_error format failed")

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib handler signature
        """Handle CORS preflight requests so the Vite dev proxy works correctly."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", _CORS_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Create the demo server."""
    return ThreadingHTTPServer((host, port), DemoHTTPRequestHandler)


def serve_forever(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the browser demo until interrupted."""
    server = make_server(host=host, port=port)
    logger.info("Open Production browser demo running at http://%s:%s", host, port)
    logger.info("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    serve_forever()
