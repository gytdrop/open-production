"""Tests for production LLM provider selection and HTTP request formatting."""
from __future__ import annotations

import json

from tools import llm_client


_PROVIDER_VARIABLES = (
    "OPENAI_API_KEY",
    "MINIMAX_API_KEY",
    "MINIMAX_BASE_URL",
    "MINIMAX_MODEL",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
)


def _clear_provider_variables(monkeypatch) -> None:
    for variable in _PROVIDER_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_default_client_uses_mock_without_provider_configuration(monkeypatch):
    _clear_provider_variables(monkeypatch)

    client = llm_client.get_default_client()

    assert isinstance(client, llm_client.MockLLMClient)


def test_default_client_selects_minimax(monkeypatch):
    _clear_provider_variables(monkeypatch)
    monkeypatch.setenv("MINIMAX_API_KEY", "minimax-key")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.minimax.test/v1")
    monkeypatch.setenv("MINIMAX_MODEL", "minimax-model")

    client = llm_client.get_default_client()

    assert isinstance(client, llm_client.HTTPChatCompletionsClient)
    assert client.base_url == "https://api.minimax.test/v1/chat/completions"
    assert client.model == "minimax-model"


def test_http_client_builds_chat_completions_request(monkeypatch):
    captured = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"real response"}}]}'

    def fake_urlopen(api_request, timeout):
        captured["request"] = api_request
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setattr(llm_client.request, "urlopen", fake_urlopen)
    client = llm_client.HTTPChatCompletionsClient(
        api_key="secret",
        base_url="https://api.minimax.test/v1",
        model="minimax-model",
        timeout=12,
    )

    result = client.complete("Create three angles", system="Be concise")

    api_request = captured["request"]
    payload = json.loads(api_request.data.decode("utf-8"))
    assert result == "real response"
    assert api_request.full_url == "https://api.minimax.test/v1/chat/completions"
    assert api_request.headers["Authorization"] == "Bearer secret"
    assert captured["timeout"] == 12
    assert payload["model"] == "minimax-model"
    assert payload["messages"] == [
        {"role": "system", "content": "Be concise"},
        {"role": "user", "content": "Create three angles"},
    ]
