"""SourcingAgent — Agent 3 of the 4-agent manifest pipeline.

Replaces: AssetLibrary + Generation agents.

Takes the per-scene search queries produced by the Mood & Keyword Agent and
makes REST calls to free-license media repositories, returning real, usable
media URLs plus the attribution data each provider's license requires.

Providers (both free-tier, key via env var):
  Unsplash  — photos.        UNSPLASH_ACCESS_KEY   https://unsplash.com/developers
  Pixabay   — photos+video.  PIXABAY_API_KEY       https://pixabay.com/api/docs/

No third-party dependencies — stdlib urllib only, matching tools/llm_client.py.

Input contract (run):
  {
    "scenes": [
      {"scene_id": "scene_01", "search_queries": ["old cricket bat", ...]},
      ...
    ],
    "results_per_query": 3,          # optional, default 3
    "media_types": ["image", "video"]  # optional, default both
  }

Output contract:
  {
    "scene_media": {
      "scene_01": [
        {
          "query": "old cricket bat",
          "media_type": "image",
          "provider": "unsplash",
          "url": "...",              # direct asset URL (regular-size image / mp4)
          "page_url": "...",         # provider page, for attribution links
          "thumbnail": "...",
          "credit": "Photo by <name> on Unsplash",
          "license": "Unsplash License",
          "width": 1080, "height": 720
        },
        ...
      ]
    },
    "providers_used": ["unsplash", "pixabay"],
    "errors": [ {"query": "...", "provider": "...", "error": "..."} ]
  }
"""
from __future__ import annotations

import json
import os
import time
from typing import Callable, Optional
from urllib import error, parse, request

from agents.base import BaseAgent

# Injectable HTTP fetcher: fetch_json(url, headers) -> dict.
# Tests swap this out; production uses _urllib_fetch_json.
FetchJson = Callable[[str, dict], dict]


def _urllib_fetch_json(url: str, headers: dict) -> dict:
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code} from {parse.urlsplit(url).netloc}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach {parse.urlsplit(url).netloc}: {exc.reason}") from exc


class UnsplashProvider:
    """Photo search via the Unsplash API (free tier: 50 req/hour)."""

    name = "unsplash"
    media_types = ("image",)

    def __init__(self, access_key: str, fetch_json: FetchJson = _urllib_fetch_json) -> None:
        self.access_key = access_key
        self.fetch_json = fetch_json

    def search(self, query: str, media_type: str, per_page: int) -> list[dict]:
        if media_type != "image":
            return []
        url = "https://api.unsplash.com/search/photos?" + parse.urlencode(
            {"query": query, "per_page": per_page, "orientation": "landscape"}
        )
        data = self.fetch_json(url, {"Authorization": f"Client-ID {self.access_key}"})
        results = []
        for photo in data.get("results", []):
            user = photo.get("user") or {}
            results.append(
                {
                    "query": query,
                    "media_type": "image",
                    "provider": self.name,
                    "url": (photo.get("urls") or {}).get("regular", ""),
                    "page_url": (photo.get("links") or {}).get("html", ""),
                    "thumbnail": (photo.get("urls") or {}).get("thumb", ""),
                    "credit": f"Photo by {user.get('name', 'Unknown')} on Unsplash",
                    "license": "Unsplash License",
                    "width": photo.get("width"),
                    "height": photo.get("height"),
                }
            )
        return results


class PixabayProvider:
    """Photo and video search via the Pixabay API (free tier: 100 req/min)."""

    name = "pixabay"
    media_types = ("image", "video")

    def __init__(self, api_key: str, fetch_json: FetchJson = _urllib_fetch_json) -> None:
        self.api_key = api_key
        self.fetch_json = fetch_json

    def search(self, query: str, media_type: str, per_page: int) -> list[dict]:
        # Pixabay rejects per_page < 3.
        per_page = max(per_page, 3)
        if media_type == "image":
            url = "https://pixabay.com/api/?" + parse.urlencode(
                {"key": self.api_key, "q": query, "image_type": "photo", "per_page": per_page, "safesearch": "true"}
            )
            data = self.fetch_json(url, {})
            return [
                {
                    "query": query,
                    "media_type": "image",
                    "provider": self.name,
                    "url": hit.get("largeImageURL", ""),
                    "page_url": hit.get("pageURL", ""),
                    "thumbnail": hit.get("previewURL", ""),
                    "credit": f"Image by {hit.get('user', 'Unknown')} on Pixabay",
                    "license": "Pixabay Content License",
                    "width": hit.get("imageWidth"),
                    "height": hit.get("imageHeight"),
                }
                for hit in data.get("hits", [])
            ]
        if media_type == "video":
            url = "https://pixabay.com/api/videos/?" + parse.urlencode(
                {"key": self.api_key, "q": query, "per_page": per_page, "safesearch": "true"}
            )
            data = self.fetch_json(url, {})
            results = []
            for hit in data.get("hits", []):
                videos = hit.get("videos") or {}
                best = videos.get("medium") or videos.get("small") or videos.get("tiny") or {}
                results.append(
                    {
                        "query": query,
                        "media_type": "video",
                        "provider": self.name,
                        "url": best.get("url", ""),
                        "page_url": hit.get("pageURL", ""),
                        "thumbnail": best.get("thumbnail", ""),
                        "credit": f"Video by {hit.get('user', 'Unknown')} on Pixabay",
                        "license": "Pixabay Content License",
                        "width": best.get("width"),
                        "height": best.get("height"),
                        "duration_seconds": hit.get("duration"),
                    }
                )
            return results
        return []


class SourcingAgent(BaseAgent):
    """Fans each scene's search queries out to the configured providers.

    Providers are auto-configured from env vars when not passed explicitly;
    a scene is never dropped on a provider error — failures land in the
    'errors' diagnostic list and the remaining providers still run.
    """

    WRITABLE_FIELDS = frozenset({"scene_media"})
    DIAGNOSTIC_KEYS = frozenset({"providers_used", "errors"})

    def __init__(
        self,
        providers: Optional[list] = None,
        request_interval: float = 0.2,
    ) -> None:
        super().__init__(name="sourcing")
        self.providers = providers if providers is not None else self._providers_from_env()
        self.request_interval = request_interval

    @staticmethod
    def _providers_from_env() -> list:
        providers = []
        unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
        if unsplash_key:
            providers.append(UnsplashProvider(unsplash_key))
        pixabay_key = os.environ.get("PIXABAY_API_KEY", "")
        if pixabay_key:
            providers.append(PixabayProvider(pixabay_key))
        return providers

    def run(self, input: dict) -> dict:  # noqa: A002
        scenes = input.get("scenes") or []
        results_per_query = int(input.get("results_per_query") or 3)
        media_types = input.get("media_types") or ["image", "video"]

        scene_media: dict[str, list[dict]] = {}
        errors: list[dict] = []

        for scene in scenes:
            scene_id = scene.get("scene_id") or f"scene_{len(scene_media) + 1:02d}"
            collected: list[dict] = []
            for query in scene.get("search_queries") or []:
                for provider in self.providers:
                    for media_type in media_types:
                        if media_type not in provider.media_types:
                            continue
                        try:
                            collected.extend(provider.search(query, media_type, results_per_query))
                        except Exception as exc:  # provider failure must not sink the scene
                            errors.append(
                                {"query": query, "provider": provider.name, "error": str(exc)}
                            )
                        if self.request_interval:
                            time.sleep(self.request_interval)
            scene_media[scene_id] = collected

        return self._enforce_scope(
            {
                "scene_media": scene_media,
                "providers_used": [p.name for p in self.providers],
                "errors": errors,
            }
        )
