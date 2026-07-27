"""Workspace renderer for the Open Production browser demo."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_TOPIC = "The future of AI in creative industries"
DEFAULT_AUDIENCE = "educated_lay"
DEFAULT_TONE = "neutral"


def _now_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _stage(
    stage_id: str,
    name: str,
    phase: str,
    status: str,
    owner: str,
    gate: str,
    summary: str,
) -> dict[str, Any]:
    return {
        "id": stage_id,
        "name": name,
        "phase": phase,
        "status": status,
        "owner": owner,
        "gate": gate,
        "summary": summary,
    }


def _asset(
    asset_id: str,
    name: str,
    asset_type: str,
    status: str,
    provenance: str,
    used_in: list[str],
) -> dict[str, Any]:
    return {
        "id": asset_id,
        "name": name,
        "type": asset_type,
        "status": status,
        "provenance": provenance,
        "used_in": used_in,
        "approved_by": "Project lead",
        "created": "2026-07-27",
    }


def _proposal(
    proposal_id: str,
    title: str,
    summary: str,
    rationale: str,
    impact: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "id": proposal_id,
        "title": title,
        "summary": summary,
        "rationale": rationale,
        "impact": impact,
        "confidence": confidence,
    }


def _clip(
    clip_id: str,
    label: str,
    start: int,
    duration: int,
    status: str,
    note: str,
) -> dict[str, Any]:
    return {
        "id": clip_id,
        "label": label,
        "start": start,
        "duration": duration,
        "status": status,
        "note": note,
    }


def _node(
    node_id: str,
    label: str,
    kind: str,
    x: int,
    y: int,
    status: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "kind": kind,
        "x": x,
        "y": y,
        "status": status,
        "detail": detail,
    }


def build_bootstrap_state() -> dict[str, Any]:
    """Build the initial state for the browser workspace."""
    pipeline = [
        _stage("idea", "Idea", "Discovery", "locked", "Creative Director", "Intent must parse", "Capture the production intent."),
        _stage("research", "Research", "Discovery", "locked", "Producer", "At least 3 sources", "Collect references, facts, and constraints."),
        _stage("references", "References", "Discovery", "locked", "Environment Artist", "Style tokens extractable", "Assemble the visual and tonal references."),
        _stage("moodboard", "Moodboard", "Discovery", "locked", "Storyboard Artist", "Mood is clear", "Collapse references into a single visual language."),
        _stage("creative_direction", "Creative Direction", "Direction", "active", "Creative Director", "Direction locked", "Choose the creative frame before the build begins."),
        _stage("story", "Story", "Direction", "ready", "Creative Director", "Structure locked", "Define the story spine."),
        _stage("script", "Script", "Direction", "ready", "Scriptwriter", "Script locked", "Write the line-level plan."),
        _stage("characters", "Characters", "Direction", "ready", "Character Director", "Consistency contract set", "Lock recurring people and performances."),
        _stage("locations", "Locations", "Direction", "ready", "Environment Artist", "Location spec set", "Define the places that hold the story."),
        _stage("shot_planning", "Shot Planning", "Direction", "ready", "Storyboard Artist", "Shot count locked", "Turn the script into a shot list."),
        _stage("storyboard", "Storyboard", "Direction", "ready", "Storyboard Artist", "Compositions locked", "Pin the visual composition for every shot."),
        _stage("timeline", "Timeline", "Build", "ready", "Editor", "Sequence locked", "Order the shots into a cut."),
        _stage("camera", "Camera", "Build", "pending", "Shot Designer", "Specs locked per shot", "Define lens, framing, and motion."),
        _stage("lighting", "Lighting", "Build", "pending", "Shot Designer", "Specs locked per shot", "Define the mood and visibility."),
        _stage("assets", "Assets", "Build", "pending", "Producer", "All assets resolved", "Resolve the remaining media and references."),
        _stage("generation", "Generation", "Execution", "pending", "Shot Designer", "Pre-flight checks passed", "Produce the first usable renders."),
        _stage("editing", "Editing", "Execution", "pending", "Editor", "Rough cut approved", "Shape pacing and transitions."),
        _stage("sound_design", "Sound Design", "Execution", "pending", "Sound Designer", "Palette approved", "Build the sound language."),
        _stage("music", "Music", "Execution", "pending", "Music Composer", "Cue map approved", "Compose the score and cue placements."),
        _stage("voice", "Voice", "Execution", "pending", "Voice Director", "Voice profile approved", "Finalize voice performance and delivery."),
        _stage("performance", "Performance", "Execution", "pending", "Reviewer", "Performance approved", "Check movement, timing, and emotional fit."),
        _stage("color", "Color", "Execution", "pending", "Colorist", "Look approved", "Grade the scenes into a shared mood."),
        _stage("packaging", "Packaging", "Delivery", "pending", "Producer", "Publish manifest ready", "Prepare deliverables and export targets."),
        _stage("review", "Review", "Delivery", "pending", "Reviewer", "Sign-off complete", "Run the final human approval pass."),
        _stage("publishing", "Publishing", "Delivery", "pending", "Producer", "Rights cleared", "Queue publication and distribution."),
        _stage("handoff", "Handoff", "Delivery", "pending", "Producer", "Handoff summary ready", "Package the production for collaboration."),
    ]

    assets = [
        _asset(
            "asset_brand_kit",
            "Open Production brand kit",
            "Brand Kit",
            "approved",
            "Defined from the product plan; used as the source of tone and palette.",
            ["Director's Canvas", "Agent Console", "Node Graph"],
        ),
        _asset(
            "asset_reference_board",
            "Reference board",
            "Visual Source",
            "approved",
            "Synthesized from the Director's Canvas references and moodboard notes.",
            ["Director's Canvas", "Timeline Editor"],
        ),
        _asset(
            "asset_character_library",
            "Character library entry",
            "Character",
            "approved",
            "Drafted from the creative direction and script notes.",
            ["Agent Console", "Node Graph"],
        ),
        _asset(
            "asset_camera_preset",
            "Camera preset stack",
            "Camera Preset",
            "proposed",
            "Derived from the storyboard and shot planning pass.",
            ["Timeline Editor", "Node Graph"],
        ),
        _asset(
            "asset_lighting_preset",
            "Lighting preset",
            "Lighting Preset",
            "proposed",
            "Generated from the moodboard and scene mood tokens.",
            ["Director's Canvas", "Agent Console"],
        ),
        _asset(
            "asset_script_deck",
            "Script deck",
            "Script",
            "approved",
            "Written from the current creative frame; line edits stay editable.",
            ["Guided Production Flow", "Timeline Editor"],
        ),
        _asset(
            "asset_publish_manifest",
            "Publish manifest",
            "Manifest",
            "pending",
            "Created when the user reaches the final gate.",
            ["Guided Production Flow", "Node Graph"],
        ),
    ]

    agents = [
        {
            "id": "creative_director",
            "name": "Creative Director",
            "role": "Owns intent, tone, and style consistency",
            "linked_stage": "creative_direction",
            "status": "proposal",
            "selected_proposal_id": "systems_story",
            "override_note": "",
            "messages": [
                {"who": "Creative Director", "text": "I will frame the production before anything is generated."},
                {"who": "You", "text": "Keep the production process visible at every step."},
            ],
            "proposals": [
                _proposal(
                    "systems_story",
                    "The Systems Story",
                    "Open Production should feel like a studio operating system rather than a prompt tool.",
                    "It aligns the interface with the product plan's core claim: the process is the product.",
                    "Moves the workspace from feature tour to production model demonstration.",
                    0.97,
                ),
                _proposal(
                    "director_s_canvas",
                    "Director's Canvas First",
                    "Lead with the spatial canvas so the user sees the full production at a glance.",
                    "The plan repeatedly emphasizes a spatial overview as the default professional surface.",
                    "Makes the workspace feel controllable and editorial from the first screen.",
                    0.91,
                ),
                _proposal(
                    "approval_rhythm",
                    "Approval Rhythm",
                    "Treat every AI action as a proposal and make the approval loop visually explicit.",
                    "The plan says human override is always available and autonomy must be earned.",
                    "Makes trust, not raw generation, the product promise.",
                    0.94,
                ),
            ],
        },
        {
            "id": "producer",
            "name": "Producer",
            "role": "Owns schedule, gates, and handoffs",
            "linked_stage": "timeline",
            "status": "ready",
            "selected_proposal_id": "stage_pack",
            "override_note": "",
            "messages": [
                {"who": "Producer", "text": "I am sequencing the work so the user can keep moving."},
                {"who": "You", "text": "Do not hide any approval gate."},
            ],
            "proposals": [
                _proposal(
                    "stage_pack",
                    "Stage Pack",
                    "Bundle the five primary views into one polished launch path.",
                    "A coherent demo is easier to evaluate than disconnected feature fragments.",
                    "Keeps the workspace moving from brief to review without dead ends.",
                    0.89,
                ),
            ],
        },
        {
            "id": "storyboard_artist",
            "name": "Storyboard Artist",
            "role": "Owns spatial composition and shot ordering",
            "linked_stage": "storyboard",
            "status": "proposal",
            "selected_proposal_id": "spatial_cards",
            "override_note": "",
            "messages": [
                {"who": "Storyboard Artist", "text": "I am turning the brief into a spatial board and a shot rhythm."},
            ],
            "proposals": [
                _proposal(
                    "spatial_cards",
                    "Spatial Cards",
                    "Use cards, notes, and shot tiles to keep the Director's Canvas readable.",
                    "The plan favors spatial planning early and exact sequencing later.",
                    "Keeps references and shots close enough to see relationships without forcing a grid.",
                    0.92,
                ),
            ],
        },
        {
            "id": "reviewer",
            "name": "Reviewer",
            "role": "Owns quality checks and human approval gates",
            "linked_stage": "review",
            "status": "proposal",
            "selected_proposal_id": "fail_closed",
            "override_note": "",
            "messages": [
                {"who": "Reviewer", "text": "I only approve when the evidence is visible."},
            ],
            "proposals": [
                _proposal(
                    "fail_closed",
                    "Fail Closed",
                    "Block any publish action until the model, the pipeline, and the approvals all line up.",
                    "The plan treats human approval as a gate, not a decoration.",
                    "Prevents the UI from implying silent automation.",
                    0.98,
                ),
            ],
        },
        {
            "id": "publisher",
            "name": "Publisher",
            "role": "Owns publish manifests and delivery targets",
            "linked_stage": "publishing",
            "status": "pending",
            "selected_proposal_id": "manifest_first",
            "override_note": "",
            "messages": [
                {"who": "Publisher", "text": "I prepare the manifest first, then I let the user decide where it goes."},
            ],
            "proposals": [
                _proposal(
                    "manifest_first",
                    "Manifest First",
                    "Make publish settings explicit before export or handoff.",
                    "The plan treats publish manifests as first-class production artifacts.",
                    "Keeps rights, targets, and approvals visible instead of hidden in a modal.",
                    0.95,
                ),
            ],
        },
    ]

    guided_steps = [
        {
            "id": "idea",
            "label": "What's your idea?",
            "status": "done",
            "agent": "Creative Director",
            "gate": "Intent must be parseable",
            "hint": "Start with a topic, audience, tone, and a production outcome.",
        },
        {
            "id": "pick_references",
            "label": "Pick references",
            "status": "done",
            "agent": "Reference Curator",
            "gate": "References must be visible",
            "hint": "Collect visual and tonal anchors before the crew locks direction.",
        },
        {
            "id": "meet_your_crew",
            "label": "Meet your crew",
            "status": "active",
            "agent": "Creative Director",
            "gate": "One direction proposal must be approved",
            "hint": "Pick or override the direction before the pipeline advances.",
        },
        {
            "id": "plan_shots",
            "label": "Plan shots",
            "status": "ready",
            "agent": "Storyboard Artist",
            "gate": "Shot list must be locked",
            "hint": "Translate the brief into scenes, shots, and motion intent.",
        },
        {
            "id": "generate",
            "label": "Generate",
            "status": "ready",
            "agent": "Reviewer",
            "gate": "Human approval required",
            "hint": "Only finalize once the workspace, the audit snapshot, and the gates align.",
        },
    ]

    canvas_cards = [
        {
            "id": "brief_card",
            "kind": "brief",
            "title": "Intent document",
            "summary": "A locked brief stays editable until the director approves it.",
            "x": 24,
            "y": 28,
            "w": 250,
            "h": 156,
            "accent": "accent",
            "linked": "creative_director",
        },
        {
            "id": "reference_card",
            "kind": "reference",
            "title": "Reference board",
            "summary": "Mood and style tokens stay attached to the same production state.",
            "x": 310,
            "y": 62,
            "w": 250,
            "h": 156,
            "accent": "accent2",
            "linked": "asset_reference_board",
        },
        {
            "id": "crew_card",
            "kind": "crew",
            "title": "Crew proposals",
            "summary": "Every AI action is a proposal until a human approves it.",
            "x": 598,
            "y": 24,
            "w": 250,
            "h": 156,
            "accent": "accent3",
            "linked": "creative_director",
        },
        {
            "id": "timeline_card",
            "kind": "timeline",
            "title": "Timeline spine",
            "summary": "Shots, voice, music, and effects all point at the same cut.",
            "x": 186,
            "y": 294,
            "w": 280,
            "h": 156,
            "accent": "muted",
            "linked": "timeline",
        },
        {
            "id": "publish_card",
            "kind": "publish",
            "title": "Publish manifest",
            "summary": "Rights, targets, and approvals are visible before delivery.",
            "x": 534,
            "y": 286,
            "w": 280,
            "h": 156,
            "accent": "accent2",
            "linked": "asset_publish_manifest",
        },
    ]

    timeline_tracks = [
        {
            "id": "video",
            "label": "Video",
            "color": "var(--accent)",
            "clips": [
                _clip("video_hook", "Hook", 0, 5, "locked", "Open with the production operating system promise."),
                _clip("video_crew", "Crew briefing", 5, 5, "approved", "Show the approval loop and the production model."),
                _clip("video_canvas", "Director's Canvas", 10, 6, "draft", "Anchor the spatial overview in the center of the demo."),
            ],
        },
        {
            "id": "voice",
            "label": "Voice",
            "color": "var(--accent2)",
            "clips": [
                _clip("voice_intro", "Narration", 0, 5, "approved", "Explain the production workflow in plain language."),
                _clip("voice_gate", "Approval prompt", 9, 4, "draft", "Ask the user to approve or override the AI proposal."),
            ],
        },
        {
            "id": "music",
            "label": "Music",
            "color": "var(--accent3)",
            "clips": [
                _clip("music_bed", "Ambient bed", 0, 12, "draft", "Keep the workspace calm, clear, and focused."),
            ],
        },
        {
            "id": "effects",
            "label": "Effects",
            "color": "var(--warning)",
            "clips": [
                _clip("fx_calls", "Callouts", 2, 8, "draft", "Use subtle callouts for approvals and gate states."),
            ],
        },
    ]

    graph_nodes = [
        _node("intent_document", "Intent Document", "brief", 48, 48, "locked", "The shared starting point for all views."),
        _node("reference_board", "Reference Board", "asset", 314, 52, "locked", "References feed the production state, not a separate silo."),
        _node("creative_brief", "Creative Brief", "decision", 574, 46, "active", "The current direction proposal being evaluated."),
        _node("crew_proposals", "Crew Proposals", "agent", 826, 54, "proposal", "AI crew writes proposals, humans approve them."),
        _node("storyboard", "Storyboard", "plan", 142, 284, "ready", "Shot composition and scene ordering live here."),
        _node("timeline", "Timeline", "sequence", 404, 280, "ready", "The sequence is shared across every view."),
        _node("assets", "Asset Library", "asset", 678, 278, "proposed", "Every asset carries provenance and usage history."),
        _node("review_gate", "Review Gate", "evaluation", 826, 290, "proposal", "Nothing publishes without a visible human decision."),
        _node("publish_manifest", "Publish Manifest", "delivery", 506, 510, "pending", "The delivery contract is explicit before export."),
        _node("audit_trail", "Audit Trail", "log", 226, 506, "locked", "The browser keeps the decision log visible."),
    ]

    graph_edges = [
        {"from": "intent_document", "to": "reference_board"},
        {"from": "reference_board", "to": "creative_brief"},
        {"from": "creative_brief", "to": "crew_proposals"},
        {"from": "creative_brief", "to": "storyboard"},
        {"from": "storyboard", "to": "timeline"},
        {"from": "timeline", "to": "assets"},
        {"from": "assets", "to": "review_gate"},
        {"from": "review_gate", "to": "publish_manifest"},
        {"from": "timeline", "to": "audit_trail"},
        {"from": "audit_trail", "to": "publish_manifest"},
    ]

    provenance = [
        {
            "id": "prov_01",
            "title": "Plan import",
            "actor": "System",
            "detail": "Loaded the Open Production plan and seeded the shared production model.",
        },
        {
            "id": "prov_02",
            "title": "Creative direction active",
            "actor": "Creative Director",
            "detail": "The first live proposal is the systems story framing.",
        },
        {
            "id": "prov_03",
            "title": "Canvas cards positioned",
            "actor": "Storyboard Artist",
            "detail": "Scenes and notes are laid out as spatial cards, not a fixed form.",
        },
        {
            "id": "prov_04",
            "title": "Timeline seeded",
            "actor": "Producer",
            "detail": "Tracks were created for video, voice, music, and effects.",
        },
        {
            "id": "prov_05",
            "title": "Asset library populated",
            "actor": "Asset System",
            "detail": "Brand kit, reference board, and publish manifest are visible to the inspector.",
        },
        {
            "id": "prov_06",
            "title": "Human approval required",
            "actor": "Reviewer",
            "detail": "No publish action can proceed without an explicit approval decision.",
        },
    ]

    script_lines = [
        {
            "id": "script_01",
            "scene": "Opening",
            "speaker": "Narrator",
            "text": "Open Production turns a brief into a shared production state.",
            "locked": True,
        },
        {
            "id": "script_02",
            "scene": "Brief",
            "speaker": "Creative Director",
            "text": "The plan is the source of truth; every view is a read-write window onto the same model.",
            "locked": True,
        },
        {
            "id": "script_03",
            "scene": "Crew",
            "speaker": "Agent Console",
            "text": "AI proposes the move, human approves or overrides it, and the audit trail stays visible.",
            "locked": False,
        },
        {
            "id": "script_04",
            "scene": "Timeline",
            "speaker": "Editor",
            "text": "Change a shot in one view and the sequence updates everywhere else.",
            "locked": False,
        },
        {
            "id": "script_05",
            "scene": "Publish",
            "speaker": "Reviewer",
            "text": "Publication only happens after the manifest and the approvals are in place.",
            "locked": False,
        },
    ]

    return {
        "version": 1,
        "saved_at": _now_label(),
        "current_view": "director_canvas",
        "selected_stage_id": "creative_direction",
        "selected_asset_id": "asset_brand_kit",
        "selected_agent_id": "creative_director",
        "selected_node_id": "creative_brief",
        "selected_scene_id": "brief_card",
        "selected_clip_id": "video_hook",
        "selected_provenance_id": "prov_01",
        "selection_kind": "asset",
        "selection_id": "asset_brand_kit",
        "production": {
            "id": "op-launch-001",
            "title": "Open Production launch workspace",
            "subtitle": "One production model. Five views. Human approval at every gate.",
            "status": "Awaiting approval",
            "current_stage_id": "creative_direction",
            "branch": "main",
            "saved_label": "Saved locally",
            "approval_state": "Proposal pending",
            "version_note": "main / director's choice",
            "brief_summary": "The workspace is seeded from the Open Production plan and is ready for approval-driven exploration.",
        },
        "brief": {
            "topic": DEFAULT_TOPIC,
            "audience": DEFAULT_AUDIENCE,
            "tone": DEFAULT_TONE,
            "length": "90 seconds",
            "format": "16:9 master + 9:16 cutdown",
            "creative_angle": "systems_story",
            "objective": "Show a production workspace where every decision is visible, approved, and reversible.",
            "constraints_text": "No silent automation.\nNo auto-publish.\nEvery AI move needs a visible approval or override.",
            "references_text": "Figma canvas\nDaVinci Resolve timeline\nComfyUI node graph",
        },
        "views": [
            {
                "id": "director_canvas",
                "label": "Director's Canvas",
                "tag": "Spatial overview",
                "description": "A freeform surface for scenes, notes, and references.",
            },
            {
                "id": "guided_flow",
                "label": "Guided Production Flow",
                "tag": "Beginner path",
                "description": "A step-by-step flow with explicit approvals at every gate.",
            },
            {
                "id": "timeline_editor",
                "label": "Timeline Editor",
                "tag": "Sequence",
                "description": "Editable tracks for video, voice, music, and effects.",
            },
            {
                "id": "agent_console",
                "label": "Agent Console",
                "tag": "AI crew",
                "description": "The crew proposes, the human approves, and nothing is hidden.",
            },
            {
                "id": "node_graph",
                "label": "Node Graph",
                "tag": "Expert view",
                "description": "A visible DAG of the same production model.",
            },
        ],
        "pipeline": pipeline,
        "guided_flow": {
            "active_step_id": "meet_your_crew",
            "steps": guided_steps,
            "helper": "Use the guided flow to approve a direction, then move the same state into planning, timeline, and review.",
        },
        "canvas": {
            "title": "Director's Canvas",
            "note": "Scenes are containers. Cards are movable ideas. Everything updates the same model.",
            "cards": canvas_cards,
            "version_tree": [
                {"id": "main", "label": "main / director's choice", "status": "current"},
                {"id": "branch-contrarian", "label": "branch / contrarian take", "status": "available"},
            ],
            "story_points": [
                "Intent",
                "References",
                "Crew briefing",
                "Timeline",
                "Publish",
            ],
        },
        "timeline": {
            "tracks": timeline_tracks,
            "note": "Edit starts, durations, and ordering without breaking the rest of the workspace.",
            "units": 24,
        },
        "script": {
            "title": "Script excerpt",
            "lines": script_lines,
        },
        "assets": assets,
        "agents": agents,
        "graph": {
            "title": "Production DAG",
            "nodes": graph_nodes,
            "edges": graph_edges,
        },
        "provenance": provenance,
        "audit_log": [
            {"ts": _now_label(), "kind": "bootstrap", "message": "Workspace loaded with a shared production model."},
            {"ts": _now_label(), "kind": "state", "message": "Director's Canvas is the default view."},
        ],
        "final_report": None,
        "filters": {"asset_query": ""},
        "notifications": [
            {"ts": _now_label(), "kind": "info", "message": "Production model loaded. Switch views without losing state."},
        ],
    }


@lru_cache(maxsize=1)
def _load_template() -> str:
    path = Path(__file__).with_name("workspace.html")
    return path.read_text(encoding="utf-8")


def render_workspace_html() -> str:
    """Render the browser workspace template with embedded bootstrap state."""
    template = _load_template()
    state_json = json.dumps(build_bootstrap_state(), ensure_ascii=False)
    return template.replace("__BOOTSTRAP_STATE__", state_json)

