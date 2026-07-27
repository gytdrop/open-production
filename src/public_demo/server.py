"""Lightweight browser demo for general audiences.

This module wraps the existing Open Production flow in a tiny HTTP server so
people can interact with it from a browser instead of a terminal.
"""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from demo_flow import build_demo_report, generate_angles


DEFAULT_TOPIC = "The future of AI in creative industries"
DEFAULT_AUDIENCE = "educated_lay"
DEFAULT_TONE = "neutral"


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
    @media (max-width: 920px) {
      .hero, .grid, .angle-grid, .detail-grid, .stat-row {
        grid-template-columns: 1fr;
      }
      .title {
        font-size: clamp(2.4rem, 12vw, 4.6rem);
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div>
        <div class="eyebrow">Open Production | browser demo</div>
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
      show(storyPanel);
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


def render_index_html() -> str:
    """Return the landing page HTML."""
    return (
        INDEX_HTML
        .replace("{{DEFAULT_TOPIC}}", DEFAULT_TOPIC)
        .replace("{{DEFAULT_AUDIENCE}}", DEFAULT_AUDIENCE)
        .replace("{{DEFAULT_TONE}}", DEFAULT_TONE)
    )


def _json_response(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    raw = handler.rfile.read(length) if length else b"{}"
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        data = {}
    return data if isinstance(data, dict) else {}


def _normalize_payload(payload: dict) -> dict:
    topic = str(payload.get("topic") or DEFAULT_TOPIC).strip() or DEFAULT_TOPIC
    audience = str(payload.get("audience") or DEFAULT_AUDIENCE).strip() or DEFAULT_AUDIENCE
    tone = str(payload.get("tone") or DEFAULT_TONE).strip() or DEFAULT_TONE
    return {"topic": topic, "audience": audience, "tone": tone}


class DemoHTTPRequestHandler(BaseHTTPRequestHandler):
    """Serve the landing page and JSON demo endpoints."""

    server_version = "OpenProductionDemo/1.0"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler signature
        route = urlparse(self.path).path
        if route in {"/", "/index.html"}:
            html = render_index_html().encode("utf-8")
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
        _json_response(self, {"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler signature
        route = urlparse(self.path).path
        raw_payload = _read_json_body(self)
        payload = _normalize_payload(raw_payload)

        if route == "/api/reframe":
            try:
                angles = generate_angles(payload["topic"], payload["audience"], payload["tone"])
            except Exception as exc:  # pragma: no cover - defensive
                _json_response(self, {"error": str(exc)}, status=500)
                return
            _json_response(self, {"topic": payload["topic"], "audience": payload["audience"], "tone": payload["tone"], "angles": angles})
            return

        if route == "/api/finalize":
            chosen_angle_id = str((raw_payload.get("chosen_angle_id") or "")).strip()
            try:
                report = build_demo_report(
                    topic=payload["topic"],
                    audience=payload["audience"],
                    tone=payload["tone"],
                    chosen_angle_id=chosen_angle_id or None,
                )
            except Exception as exc:  # pragma: no cover - defensive
                _json_response(self, {"error": str(exc)}, status=500)
                return
            _json_response(self, report)
            return

        _json_response(self, {"error": "Not found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - stdlib signature
        """Keep the browser demo quiet unless something goes wrong."""


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Create the demo server."""
    return ThreadingHTTPServer((host, port), DemoHTTPRequestHandler)


def serve_forever(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the browser demo until interrupted."""
    server = make_server(host=host, port=port)
    print(f"Open Production browser demo running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
