"""Tests for ``agents.confirm_gate``.

Five tests covering both sinks per the Session 5 spec:
  1. ``TtyConfirmSink`` with stdin-mocked "1" → choice=options[0], declined=False.
  2. ``TtyConfirmSink`` with empty stdin → returns the default.
  3. ``TtyConfirmSink`` with "n" → declined=True.
  4. ``AutoConfirmSink(c="advocate")`` always returns choice="advocate".
  5. ``AutoConfirmSink`` with no choice arg falls back to request.default, then options[0].
"""
from __future__ import annotations

import pytest

from agents.confirm_gate import (
    AutoConfirmSink,
    ConfirmRequest,
    ConfirmResponse,
    TtyConfirmSink,
)


def _request(default: str | None = "skeptic") -> ConfirmRequest:
    return ConfirmRequest(
        summary="Which angle should guide the write?",
        options=["skeptic", "advocate", "contrarian"],
        default=default,
    )


# ---------------------------------------------------------------------------
# Test 1: numeric "1" picks the first option
# ---------------------------------------------------------------------------

def test_tty_sink_numeric_one_picks_first_option(monkeypatch):
    """Std-in "1" → choice=options[0], declined=False."""
    sink = TtyConfirmSink(prompt_input=lambda _: "1")
    resp = sink.ask(_request())
    assert resp.choice == "skeptic"
    assert resp.declined is False


# ---------------------------------------------------------------------------
# Test 2: empty input falls back to default
# ---------------------------------------------------------------------------

def test_tty_sink_empty_input_returns_default(monkeypatch):
    """Empty stdin → choice=request.default, declined=False."""
    sink = TtyConfirmSink(prompt_input=lambda _: "   ")
    resp = sink.ask(_request(default="advocate"))
    assert resp.choice == "advocate"
    assert resp.declined is False


# ---------------------------------------------------------------------------
# Test 3: "n" / "no" declines
# ---------------------------------------------------------------------------

def test_tty_sink_n_declines(monkeypatch):
    """Input "n" → declined=True, choice=""."""
    sink = TtyConfirmSink(prompt_input=lambda _: "n")
    resp = sink.ask(_request())
    assert resp.declined is True
    assert resp.choice == ""


# ---------------------------------------------------------------------------
# Test 4: AutoConfirmSink(c=...) always picks that choice
# ---------------------------------------------------------------------------

def test_auto_sink_explicit_choice_is_returned():
    """AutoConfirmSink(choice=\"advocate\") always returns choice=\"advocate\"."""
    sink = AutoConfirmSink(choice="advocate")
    resp = sink.ask(_request(default="skeptic"))
    assert resp.choice == "advocate"
    assert resp.declined is False

    # Same sink, different request — still picks the explicit choice.
    resp2 = sink.ask(_request(default="contrarian"))
    assert resp2.choice == "advocate"
    assert resp2.declined is False


# ---------------------------------------------------------------------------
# Test 5: AutoConfirmSink falls back to default then options[0]
# ---------------------------------------------------------------------------

def test_auto_sink_falls_back_to_default_then_first_option():
    """With no choice set, AutoConfirmSink uses request.default, then options[0]."""
    sink = AutoConfirmSink()  # no choice

    # Default present → returns the default.
    resp = sink.ask(_request(default="contrarian"))
    assert resp.choice == "contrarian"
    assert resp.declined is False

    # No default → falls back to options[0].
    resp2 = sink.ask(_request(default=None))
    assert resp2.choice == "skeptic"
    assert resp2.declined is False
