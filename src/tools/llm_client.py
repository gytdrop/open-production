"""LLM client interface, mock clients, and real provider clients.

Clients:
  LLMClient          — Protocol (interface) every client must satisfy.
  MockLLMClient      — Fixed-response mock. Used in tests.
  ResearchMockLLMClient — Deterministic three-angle response. Used in the browser demo.
  OpenAILLMClient    — Real client backed by the OpenAI API.
                       Requires OPENAI_API_KEY env var.
  HTTPChatCompletionsClient — Dependency-free client for MiniMax and
                       other OpenAI-compatible chat-completions providers.

Usage:
  # In production (env var set):
  from tools.llm_client import OpenAILLMClient
  llm = OpenAILLMClient()              # reads OPENAI_API_KEY from environment
  llm = OpenAILLMClient(model="gpt-4o")

  # In tests / offline:
  from tools.llm_client import MockLLMClient
  llm = MockLLMClient()

  # Auto-select (production or mock):
  from tools.llm_client import get_default_client
  llm = get_default_client()           # selects OpenAI, MiniMax, generic, or mock
"""
from __future__ import annotations

import json
import os
from urllib import error, request
from typing import Optional, Protocol


class LLMClient(Protocol):
    """Minimal LLM client contract."""

    def complete(self, prompt: str, system: str = "") -> str:
        """Return the model''s completion for ``prompt`` (with optional ``system`` preamble)."""
        ...


def _default_three_angle_json() -> str:
    """Deterministic three-angle JSON used when MockLLMClient has no explicit response."""
    angles = [
        {
            "id": "skeptic",
            "name": "Skeptic",
            "summary": "What are the strongest objections to the mainstream framing?",
            "questions_to_address": [
                "What evidence is missing from the dominant narrative?",
                "Which stakeholders benefit from the current framing?",
                "What has been overstated or under-scrutinised?",
            ],
            "risk_focus": "May overemphasise doubt and underplay genuine progress.",
        },
        {
            "id": "advocate",
            "name": "Advocate",
            "summary": "Why does the topic matter and who stands to benefit most?",
            "questions_to_address": [
                "What is the strongest evidence in favour of the topic?",
                "Who are the primary beneficiaries and what do they report?",
                "What milestones mark genuine forward progress?",
            ],
            "risk_focus": "May underweight risks, costs, or equity concerns.",
        },
        {
            "id": "contrarian",
            "name": "Contrarian",
            "summary": "What is the defensible but underexplored position on the topic?",
            "questions_to_address": [
                "What does the consensus get backwards?",
                "Which second-order effects are being ignored?",
                "What would a contrarian-but-rigorous analyst argue?",
            ],
            "risk_focus": "May prioritise novelty over accuracy.",
        },
    ]
    return json.dumps({"angles": angles})


class MockLLMClient:
    """Returns a fixed JSON string. Used by tests + the demo stub.

    Behaviour:
    * If ``set_response(s)`` was called (or the constructor received a
      non-None ``response=``), ``complete()`` returns that string verbatim.
    * Otherwise ``complete()`` returns a default three-angle JSON payload
      that ``agents.creative_reframing.CreativeReframing`` can parse as-is.
    """

    def __init__(self, response: Optional[str] = None) -> None:
        self.response: Optional[str] = response

    def set_response(self, s: str) -> None:
        """Pin ``complete()`` to return ``s`` until cleared."""
        self.response = s

    def complete(self, prompt: str, system: str = "") -> str:
        if self.response is not None:
            return self.response
        return _default_three_angle_json()


class ResearchMockLLMClient:
    """Returns a deterministic three-angle JSON response for demo/research prompts.

    Extracts the topic from the prompt (first line after "Topic: ") and
    builds a valid ``{"angles": [...]}`` payload so the demo runs with no
    real API keys.
    """

    def complete(self, prompt: str, system: str = "") -> str:  # noqa: ARG002
        topic = "the topic"
        for line in prompt.splitlines():
            if line.startswith("Topic:"):
                topic = line.split(":", 1)[1].strip()
                break
        angles = [
            {
                "id": "skeptic",
                "name": "The skeptic''s view",
                "summary": f"What are the strongest objections to current claims about {topic}?",
                "questions_to_address": [
                    f"What evidence is missing from the mainstream narrative on {topic}?",
                    "Which stakeholders benefit from the dominant framing?",
                    "What has been overstated or under-scrutinised?",
                ],
                "risk_focus": "May overemphasise doubt and underplay genuine progress.",
            },
            {
                "id": "advocate",
                "name": "The advocate''s case",
                "summary": f"Why does {topic} matter and who stands to benefit most?",
                "questions_to_address": [
                    f"What is the strongest evidence in favour of {topic}?",
                    "Who are the primary beneficiaries and what do they report?",
                    "What milestones mark genuine forward progress?",
                ],
                "risk_focus": "May underweight risks, costs, or equity concerns.",
            },
            {
                "id": "contrarian",
                "name": "The non-obvious take",
                "summary": f"What is the defensible but underexplored position on {topic}?",
                "questions_to_address": [
                    f"What does the consensus on {topic} get backwards?",
                    "Which second-order effects are being ignored?",
                    "What would a contrarian-but-rigorous analyst argue?",
                ],
                "risk_focus": "May prioritise novelty over accuracy.",
            },
        ]
        return json.dumps({"angles": angles})


class OpenAILLMClient:
    """Real LLM client backed by the OpenAI Chat Completions API.

    Reads OPENAI_API_KEY from the environment. If the key is absent,
    __init__ raises EnvironmentError so callers can fall back to a mock.

    Requires: ``pip install openai``  (not a hard dependency — imported lazily).
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self._api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. "
                "Set it in your environment or pass api_key= explicitly. "
                "Use MockLLMClient or get_default_client() for offline use."
            )

    def complete(self, prompt: str, system: str = "") -> str:
        """Send a chat completion request and return the text content."""
        try:
            import openai  # lazy import — not a hard requirement
        except ImportError as exc:
            raise ImportError(
                "openai package is not installed. "
                "Run: pip install openai"
            ) from exc

        client = openai.OpenAI(api_key=self._api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""



class HTTPChatCompletionsClient:
    """Client for providers implementing the OpenAI chat-completions format.

    ``base_url`` may be either a versioned API root such as
    ``https://api.example.com/v1`` or the complete
    ``.../chat/completions`` endpoint.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise EnvironmentError("An API key is required for the HTTP LLM client.")
        if not base_url:
            raise EnvironmentError("A base URL is required for the HTTP LLM client.")
        if not model:
            raise EnvironmentError("A model name is required for the HTTP LLM client.")

        normalized_url = base_url.rstrip("/")
        if not normalized_url.endswith("/chat/completions"):
            normalized_url += "/chat/completions"

        self.api_key = api_key
        self.base_url = normalized_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def complete(self, prompt: str, system: str = "") -> str:
        """Send a chat-completions request and return its first text response."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        ).encode("utf-8")
        api_request = request.Request(
            self.base_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(api_request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LLM provider returned HTTP {exc.code}: {details}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f"Could not connect to the LLM provider: {exc.reason}") from exc

        try:
            parsed = json.loads(response_body)
            return parsed["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("LLM provider returned an invalid chat-completions response.") from exc


def get_default_client(
    model: str = OpenAILLMClient.DEFAULT_MODEL,
) -> "LLMClient":
    """Select a configured production client, or return the offline mock.

    Selection order is OpenAI, MiniMax, generic OpenAI-compatible provider,
    then ``MockLLMClient``. A provider is selected only when all of its
    required environment variables are present.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        try:
            return OpenAILLMClient(model=model, api_key=api_key)
        except Exception:
            pass

    minimax_api_key = os.environ.get("MINIMAX_API_KEY", "")
    minimax_base_url = os.environ.get("MINIMAX_BASE_URL", "")
    minimax_model = os.environ.get("MINIMAX_MODEL", "")
    if minimax_api_key and minimax_base_url and minimax_model:
        return HTTPChatCompletionsClient(
            api_key=minimax_api_key,
            base_url=minimax_base_url,
            model=minimax_model,
        )

    compatible_api_key = os.environ.get("LLM_API_KEY", "")
    compatible_base_url = os.environ.get("LLM_BASE_URL", "")
    compatible_model = os.environ.get("LLM_MODEL", "")
    if compatible_api_key and compatible_base_url and compatible_model:
        return HTTPChatCompletionsClient(
            api_key=compatible_api_key,
            base_url=compatible_base_url,
            model=compatible_model,
        )

    return MockLLMClient()
