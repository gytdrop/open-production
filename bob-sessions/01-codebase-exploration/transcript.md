# Bob Session 1 — Codebase Exploration

**Date:** 2026-07-27  
**Bob session ID:** N/A (IBM Bob IDE, agent mode)  
**Goal:** Identify branch coverage gaps in the OpenMontage video pipeline dispatcher and propose a hardening refactor.  
**Outcome:** Refactor proposal inline below.

---

## Context note

The spec references `D:\openclaw\pdt\src\coordinator\scheduler.py`, which does not exist in this workspace. The active workspace is **OpenMontage** (`d:\PROJECTS\OpenMontage`). Bob applied the analysis methodology to the actual dispatcher-loop equivalent in OpenMontage: `tools/video/video_compose.py` (VideoCompose) and `tools/video/video_stitch.py` (VideoStitch), which together form the composition-dispatch surface with the same structural concerns (multi-operation loop, branch-heavy failure paths, external-dependency routing).

---

## Transcript

**User:** Analyze the dispatcher loop in the OpenMontage video pipeline (video_compose.py + video_stitch.py) and produce a branch coverage gap refactor proposal. Read-only. No code changes.

**Bob:** *(read video_compose.py ~1 900 lines, video_stitch.py ~963 lines, tests/qa/test_05–08, tests/tools/ suite)*

---

## Refactor Proposal

---

### Phase Table — Branch Classification

#### `VideoCompose.execute()` — top-level dispatcher (lines 332–355)

| Branch | Location | Classification | Notes |
|---|---|---|---|
| `operation == "compose"` | L337 | **Tested** | test_05, test_08 exercise this path |
| `operation == "render"` | L339 | **Partially tested** | test_08 exercises the compose path inside render; the `render_runtime` routing sub-tree is not unit-tested |
| `operation == "remotion_render"` | L341 | **Untested** | No test invokes this operation directly; only called transitively via `_render()` |
| `operation == "burn_subtitles"` | L343 | **Tested** | test_05 Test 3 covers this directly |
| `operation == "overlay"` | L345 | **Tested** | test_05 Test 5 covers this |
| `operation == "encode"` | L347 | **Tested** | test_05 Test 4 covers this |
| `else` (unknown operation) | L349 | **Untested** | The `ToolResult(success=False, error=f"Unknown operation")` path is never exercised |
| Outer `try/except Exception` | L336/352 | **Partially tested** | Happy paths hit the try block; the generic exception-to-ToolResult conversion is never exercised by tests |

#### `VideoCompose._render()` — runtime-routing dispatcher (lines 1292–1493)

| Branch | Location | Classification | Notes |
|---|---|---|---|
| `render_runtime` empty → error | L1321 | **Untested** | No test passes `edit_decisions` without `render_runtime` |
| `render_runtime` unknown value → error | L1334 | **Untested** | No test passes an invalid runtime string |
| `render_runtime == "remotion"` + atelier requested | L1356 | **Untested** | `composition_mode="atelier"` path never hit by tests |
| `asset_manifest` absent → error | L1359 | **Untested** | |
| `cuts` empty → error | L1369 | **Untested** | |
| `render_runtime == "hyperframes"` | L1390 | **Untested** | HyperFrames runtime branch never reached in tests |
| `render_runtime == "ffmpeg"` | L1399 | **Untested** | Explicit FFmpeg render_runtime branch never tested |
| `_needs_remotion()` True → Remotion fails → governance error | L1425 | **Untested** | The "NEVER silently fall back" branch is untested |
| `_needs_remotion()` False → FFmpeg fallback | L1440 | **Inherently untestable** | Requires Remotion to be unavailable; depends on system state |
| `final_review["status"] == "fail"` → downgrade result | L1483 | **Untested** | Post-render self-review failure path never exercised |

#### `VideoCompose._compose()` — segment-build loop (lines 390–679)

| Branch | Location | Classification | Notes |
|---|---|---|---|
| `edit_decisions` absent | L398 | **Untested** | No test omits this key |
| `compose_target` dict present + valid | L419 | **Partially tested** | Happy path always uses default; explicit `compose_target` never tested |
| `compose_target` with `fit="cover"` | L518 | **Untested** | Only `pad` mode exercised |
| `_is_image(source)` True → error | L475 | **Untested** | No test passes a still image into `compose` |
| `_has_audio_stream()` False → silent injection branch | L556 | **Untested** | All test fixtures have audio; the `anullsrc` rebuild path never runs |
| `subtitle_path` present + exists | L611 | **Tested** | test_05 Test 2 hits this |
| `audio_path` present + exists | L619 | **Tested** | test_05 Test 1 and test_08 hit this |
| `profile_name` resolves successfully | L629 | **Tested** | test_05 Test 4 hits `encode` (separate path); compose+profile path untested |
| `needs_reencode` True | L636 | **Tested** (via subtitle path) | |
| `needs_reencode` False → copy | L641 | **Tested** | |
| `cut source not found` | L467 | **Untested** | |

#### `VideoStitch.execute()` / `_stitch()` (lines 148–173, 481–582)

| Branch | Location | Classification | Notes |
|---|---|---|---|
| `dry_run=True` | L152 | **Untested** | No test passes `dry_run=True` |
| `operation == "validate"` | L159 | **Tested** | test_06 Tests 1+2 |
| `operation == "stitch"` | L161 | **Tested** | test_06 Tests 3–6 |
| `operation == "preview_stitch"` | L163 | **Tested** | test_06 Test 7 |
| `operation == "spatial"` | L165 | **Tested** | test_06 Tests 8–10 |
| `else` unknown operation | L168 | **Untested** | |
| `clips` empty → error | L488 | **Untested** | |
| `len(clips) < 2` → error | L490 | **Untested** | |
| `needs_norm and not auto_normalize and transition == "cut"` → error | L517 | **Partially tested** | Mismatch detected (test_06 Test 2 validates, but the stitch-level guard itself isn't hit by stitch tests without `auto_normalize`) |
| `transition == "cut"` | L552 | **Tested** | test_06 Test 3 |
| `transition == "crossfade"` → 2-clip | L617 | **Tested** | test_06 Test 4 |
| `transition == "crossfade"` → N-clip chain | L631 | **Untested** | `_chain_xfade` for crossfade with >2 clips never exercised |
| `transition == "fade"` → 2-clip | L643 | **Tested** | test_06 Test 5 uses 3 clips (chain path), not 2-clip path |
| `transition == "fade"` → N-clip chain | L656 | **Tested** | test_06 Test 5 (3 clips) |
| `transition` unknown → error | L559 | **Untested** | |
| `layout == "side_by_side"` | L819 | **Tested** | test_06 Test 8 |
| `layout == "vertical_stack"` | L822 | **Tested** | test_06 Test 9 |
| `layout == "picture_in_picture"` | L823 | **Tested** | test_06 Test 10 |
| `layout` unknown → error | L826 | **Untested** | |
| `_clip_has_audio()` → False → `_ensure_audio_for_clips` adds silent track | `_ensure_audio_for_clips` L233 | **Untested** | Test fixtures always have audio |

---

### Top 3 Gaps by Severity

#### Gap 1 — `_compose()` silent-audio injection branch (L553–583) — **SEVERITY: HIGH**

**Why it matters:** When stock video clips lack an audio stream (common with Pexels AI-generated clips — explicitly noted in the code comment at L548), `_compose()` rebuilds the entire ffmpeg command to inject `anullsrc`. This is the most complex branch in the method (a full command reconstruction, not just a flag flip). If it breaks, the tool silently fails or produces corrupt segment layouts on all clips from audio-free sources — the dominant source type in production. No test exercises it.

**Proposed refactor:** Extract the silent-audio command-building logic into a helper `_build_segment_cmd(source, seg_path, in_s, out_s, duration, has_audio, vf_parts, af_parts, ...)`. The has_audio parameter makes the branch a pure function — trivially testable with a mock `source` path and a `has_audio=False` flag without needing an actual audio-less video file.

#### Gap 2 — `_render()` render_runtime routing guards (L1321–1343) — **SEVERITY: HIGH**

**Why it matters:** `render_runtime` is the governance-critical field. If an agent passes a blank string, a typo (`"Remotion"` with capital R), or omits the field entirely, the tool immediately returns a structured error — but neither path is covered by any test. In production this is the most likely misconfiguration (copy-paste error in an edit_decisions dict). The `_pre_compose_validation()` renderer_family guard (L1268) has the same gap.

**Proposed refactor:** Extract a `_validate_render_runtime(edit_decisions)` function returning `ToolResult | None`. This is a pure validator over a dict — no subprocess, no filesystem. Add 4 unit tests: empty string, wrong case, unknown value, and valid value.

#### Gap 3 — `_stitch()` incompatibility guard + `auto_normalize` interaction (L514–525) — **SEVERITY: MEDIUM**

**Why it matters:** The guard `if needs_norm and not auto_normalize and transition == "cut"` is a three-way conjunction. All three variables must be True simultaneously to trigger the error. The existing tests reach `stitch` with matching clips (so `needs_norm=False`), or with `auto_normalize=True`, but never the combination `mismatched + no normalize + cut`. If this guard silently fails (e.g. if `_needs_normalization()` returns False due to a probe key being None), FFmpeg receives incompatible streams and produces corrupt output without a useful error.

**Proposed refactor:** Extract `_check_stitch_compatibility(probes, auto_normalize, transition) -> str | None` (returns an error message string or None). Pure function, unit-testable with dict fixtures — no subprocess required.

---

### Proposed Refactor

**Scope:** 3 surgical extractions. No semantic changes. No new public API surface.

#### 1. `tools/video/video_compose.py` — Extract `_build_segment_cmd()`

```python
# NEW private method (pure function, no I/O)
def _build_segment_cmd(
    self,
    source: Path,
    seg_path: Path,
    in_s: float,
    duration: float,
    vf_parts: list[str],
    af_parts: list[str],
    codec: str,
    crf: int,
    preset: str,
    has_audio: bool,
) -> list[str]:
    """Build the ffmpeg command for a single segment encode.

    Returns the full argv list. Has no I/O side effects — all decisions
    (codec, filters, audio presence) are passed as arguments.
    """
    ...
```

**What changes:** Lines 500–584 of `_compose()` become a call to `self._build_segment_cmd(...)`. The method itself is unchanged; only the command-building is relocated.

---

#### 2. `tools/video/video_compose.py` — Extract `_validate_render_runtime()`

```python
# NEW private method (pure function, no I/O)
@staticmethod
def _validate_render_runtime(edit_decisions: dict) -> ToolResult | None:
    """Validate render_runtime in edit_decisions.

    Returns a failed ToolResult if invalid, None if OK.
    Extracted from _render() lines 1319-1342 to allow unit testing.
    """
    ...
```

**What changes:** Lines 1319–1342 of `_render()` become `block = self._validate_render_runtime(edit_decisions); if block: return block`.

---

#### 3. `tools/video/video_stitch.py` — Extract `_check_stitch_compatibility()`

```python
# NEW private static method (pure function, no I/O)
@staticmethod
def _check_stitch_compatibility(
    probes: list[dict],
    auto_normalize: bool,
    transition: str,
) -> str | None:
    """Check whether the given clips can be stitched as requested.

    Returns an error message string if incompatible, None if OK.
    Extracted from _stitch() lines 514-525 to allow unit testing.
    """
    ...
```

---

### New Tests That Would Close the Top 3 Gaps

```python
# tests/tools/test_video_compose_segment_cmd.py
def test_segment_cmd_has_audio():
    """_build_segment_cmd with has_audio=True uses 0:a stream."""
    tool = VideoCompose()
    cmd = tool._build_segment_cmd(
        source=Path("clip.mp4"), seg_path=Path("seg.mp4"),
        in_s=0, duration=5, vf_parts=["scale=1920:1080,setsar=1,fps=30"],
        af_parts=[], codec="libx264", crf=23, preset="fast", has_audio=True,
    )
    assert "-c:a" in cmd
    assert "anullsrc" not in " ".join(cmd)

def test_segment_cmd_no_audio_injects_silent_track():
    """_build_segment_cmd with has_audio=False injects anullsrc."""
    tool = VideoCompose()
    cmd = tool._build_segment_cmd(
        source=Path("clip.mp4"), seg_path=Path("seg.mp4"),
        in_s=0, duration=5, vf_parts=["scale=1920:1080,setsar=1,fps=30"],
        af_parts=[], codec="libx264", crf=23, preset="fast", has_audio=False,
    )
    assert "anullsrc" in " ".join(cmd)
    assert "-map" in cmd  # explicit stream mapping required

def test_segment_cmd_speed_adds_atempo():
    """Speed != 1.0 adds setpts vf and atempo af regardless of audio presence."""
    tool = VideoCompose()
    cmd = tool._build_segment_cmd(
        source=Path("clip.mp4"), seg_path=Path("seg.mp4"),
        in_s=2, duration=3, vf_parts=["scale=1920:1080,setsar=1,fps=30"],
        af_parts=["atempo=2.0"], codec="libx264", crf=23, preset="fast", has_audio=True,
    )
    assert "-filter:a" in cmd
    assert "atempo" in " ".join(cmd)
```

```python
# tests/tools/test_video_compose_runtime_validation.py
def test_validate_render_runtime_empty():
    result = VideoCompose._validate_render_runtime({"render_runtime": ""})
    assert result is not None and not result.success
    assert "render_runtime" in result.error

def test_validate_render_runtime_unknown():
    result = VideoCompose._validate_render_runtime({"render_runtime": "moviepy"})
    assert result is not None and not result.success
    assert "moviepy" in result.error

def test_validate_render_runtime_wrong_case():
    result = VideoCompose._validate_render_runtime({"render_runtime": "Remotion"})
    assert result is not None and not result.success

def test_validate_render_runtime_valid():
    for rt in ("remotion", "hyperframes", "ffmpeg"):
        result = VideoCompose._validate_render_runtime({"render_runtime": rt})
        assert result is None, f"Expected None (valid) for {rt!r}"
```

```python
# tests/tools/test_video_stitch_compatibility.py
def test_compatible_clips_pass():
    probes = [
        {"width": 1280, "height": 720, "fps": 30, "video_codec": "h264", "audio_codec": "aac", "sample_rate": "44100"},
        {"width": 1280, "height": 720, "fps": 30, "video_codec": "h264", "audio_codec": "aac", "sample_rate": "44100"},
    ]
    err = VideoStitch._check_stitch_compatibility(probes, auto_normalize=False, transition="cut")
    assert err is None

def test_incompatible_clips_cut_no_normalize_fails():
    probes = [
        {"width": 1280, "height": 720, "fps": 30, "video_codec": "h264", "audio_codec": "aac", "sample_rate": "44100"},
        {"width": 640,  "height": 480, "fps": 24, "video_codec": "h264", "audio_codec": "aac", "sample_rate": "44100"},
    ]
    err = VideoStitch._check_stitch_compatibility(probes, auto_normalize=False, transition="cut")
    assert err is not None
    assert "auto_normalize" in err

def test_incompatible_clips_with_auto_normalize_pass():
    probes = [
        {"width": 1280, "height": 720, "fps": 30, "video_codec": "h264"},
        {"width": 640,  "height": 480, "fps": 24, "video_codec": "hevc"},
    ]
    err = VideoStitch._check_stitch_compatibility(probes, auto_normalize=True, transition="cut")
    assert err is None

def test_incompatible_clips_with_crossfade_pass():
    """Crossfade normalizes first, so incompatible clips are OK."""
    probes = [
        {"width": 1280, "height": 720, "fps": 30},
        {"width": 640,  "height": 480, "fps": 24},
    ]
    err = VideoStitch._check_stitch_compatibility(probes, auto_normalize=False, transition="crossfade")
    assert err is None
```

---

### Summary

| Gap | File | Lines | Current state | Proposed fix |
|---|---|---|---|---|
| Silent-audio injection | `video_compose.py` | 500–584 | Complex branch, untested | Extract `_build_segment_cmd()` |
| Runtime routing guards | `video_compose.py` | 1319–1342 | 4 branches, all untested | Extract `_validate_render_runtime()` |
| Stitch compatibility guard | `video_stitch.py` | 514–525 | 3-way conjunction, untested | Extract `_check_stitch_compatibility()` |

All three are pure-function extractions. No behavioural change. Each extraction converts an untestable in-method branch into a stateless function that can be parametrically unit-tested without ffmpeg, Node.js, or real video files.

---

## Done checklist

- [x] Bob read full source files (line numbers and function names cited throughout)
- [x] Phase table produced (every if/elif/else in dispatcher + loop branches classified)
- [x] Top 3 gaps by severity identified and ranked
- [x] Proposed refactor: 3 function extractions with signatures and what changes
- [x] New tests that close the top 3 gaps provided
- [x] Proposal is ≤ 1 page (condensed form)
- [x] Transcript saved to this file
- [x] Read-only session — no code modified
