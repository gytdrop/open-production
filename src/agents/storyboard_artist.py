"""StoryboardArtistAgent — generates ASCII compositional frames for approved shots.

Scope contract (Appendix K.2 of open-production-plan.md):
  Can write:  Shot.storyboard_frame
  Cannot write: Shot.camera, Shot.lighting, Shot.characters

The storyboard artist draws what was decided, not what should be decided.
If CameraSpec is incomplete, draws with available parameters and flags missing ones.
"""
from __future__ import annotations

from agents.base import BaseAgent

# ---------------------------------------------------------------------------
# Framing → ASCII frame template map
# ---------------------------------------------------------------------------

_ASCII_FRAMES: dict[str, str] = {
    "extreme_close": (
        "┌─────────────────┐\n"
        "│   [FACE / DETAIL │\n"
        "│    EXTREME CLOSE│\n"
        "│      UP SHOT   ]│\n"
        "└─────────────────┘"
    ),
    "close": (
        "┌─────────────────┐\n"
        "│  [CHARACTER      │\n"
        "│   HEAD &         │\n"
        "│   SHOULDERS]     │\n"
        "└─────────────────┘"
    ),
    "medium_close": (
        "┌─────────────────┐\n"
        "│  [CHARACTER     │\n"
        "│   CHEST-UP]     │\n"
        "│                 │\n"
        "└─────────────────┘"
    ),
    "medium": (
        "┌─────────────────┐\n"
        "│  [CHARACTER     │\n"
        "│   WAIST-UP]     │\n"
        "│   /background/  │\n"
        "└─────────────────┘"
    ),
    "medium_wide": (
        "┌─────────────────┐\n"
        "│ [CHAR] [CHAR]   │\n"
        "│  full figure    │\n"
        "│  /location/     │\n"
        "└─────────────────┘"
    ),
    "wide": (
        "┌─────────────────┐\n"
        "│  /environment/  │\n"
        "│ [fig]  [fig]    │\n"
        "│  full setting   │\n"
        "└─────────────────┘"
    ),
    "extreme_wide": (
        "┌─────────────────┐\n"
        "│ /landscape/env/ │\n"
        "│   [tiny fig]    │\n"
        "│  establishing   │\n"
        "└─────────────────┘"
    ),
}

_DEFAULT_FRAME = (
    "┌─────────────────┐\n"
    "│  [SUBJECT]      │\n"
    "│  /background/   │\n"
    "│  (framing TBD)  │\n"
    "└─────────────────┘"
)


class StoryboardArtistAgent(BaseAgent):
    """Generates a compositional ASCII frame for an approved shot.

    Input dict:
        shot_id (str)                — identifier
        camera (dict)                — CameraSpec-like dict with 'framing', 'angle', 'movement'
        characters (list[dict])      — character reference dicts (names/ids)
        location (str)               — location name
        intent (str)                 — one-sentence shot intent

    Output dict:
        composition_description (str)  — verbal description of the frame
        blocking_diagram (str)         — ASCII frame
        frame_elements (list[str])     — what is in the frame
        negative_space (str)           — where the eye goes first
        missing_specs (list[str])      — flagged missing CameraSpec fields
    """

    WRITABLE_FIELDS: frozenset[str] = frozenset({"Shot.storyboard_frame"})
    DIAGNOSTIC_KEYS: frozenset[str] = frozenset({
        "blocking_diagram",
        "composition_description",
        "frame_elements",
        "negative_space",
        "missing_specs",
    })

    def __init__(self) -> None:
        super().__init__(name="storyboard_artist_agent")

    def run(self, input: dict) -> dict:  # noqa: A002
        camera = input.get("camera") or {}
        characters = input.get("characters") or []
        location = str(input.get("location") or "unspecified location")
        intent = str(input.get("intent") or "")

        # Detect missing specs
        missing: list[str] = []
        if not camera:
            missing.append("camera spec not provided")
        framing = str(camera.get("framing") or "")
        angle = str(camera.get("angle") or "eye_level")
        movement = str(camera.get("movement") or "static")
        if not framing:
            missing.append("camera.framing not specified")

        # Build ASCII blocking diagram
        blocking = _ASCII_FRAMES.get(framing, _DEFAULT_FRAME)

        # Build frame elements
        char_names = [c.get("name", c.get("id", "character")) for c in characters]
        elements: list[str] = []
        if char_names:
            elements.extend(char_names)
        elements.append(location)
        if angle != "eye_level":
            elements.append(f"{angle} angle")
        if movement != "static":
            elements.append(f"camera {movement}")

        # Composition description
        char_str = ", ".join(char_names) if char_names else "subject"
        framing_label = framing.replace("_", " ") if framing else "unspecified framing"
        description = (
            f"{framing_label.title()} shot of {char_str} at {location}. "
            f"Camera angle: {angle}. Movement: {movement}."
        )
        if intent:
            description += f" Intent: {intent}."

        # Negative space — where the eye goes first
        if framing in ("extreme_close", "close", "medium_close"):
            negative_space = "Eye drawn immediately to the character's face/expression."
        elif framing in ("medium", "medium_wide"):
            negative_space = "Eye drawn to the character(s), background provides context."
        else:
            negative_space = "Eye drawn across the environment; characters are in context."

        result: dict = {
            "composition_description": description,
            "blocking_diagram": blocking,
            "frame_elements": elements,
            "negative_space": negative_space,
        }
        if missing:
            result["missing_specs"] = missing
        return result
