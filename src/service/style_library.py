"""StyleLibrary — Library Hierarchy and Category Management for style tokens.

§12 of the Open Production architecture spec.

Design
------
The StyleLibrary is an in-memory (optionally file-backed) hierarchical store
for StyleToken objects.  It maps directly onto the Production.style_tokens and
Production.brand_kit fields but adds:

  - Category grouping: every token belongs to exactly one category (a free-form
    slug, e.g. "palette/primary", "typography/body", "lighting/key").
  - A two-level hierarchy: LIBRARY → CATEGORY → TOKEN.
    The library is the root; categories are mid-level groupings; tokens are leaves.
  - CRUD for both categories and tokens.
  - A flat token view (all_tokens()) for compatibility with the existing
    AssetLibraryAgent assembler.
  - JSON serialise/deserialise for persistence.

Library Hierarchy
-----------------
    StyleLibrary
    ├── category: "palette"
    │   ├── StyleToken (id="tok_pal001", kind="color", ...)
    │   └── StyleToken (id="tok_pal002", kind="color", ...)
    ├── category: "typography"
    │   └── StyleToken (id="tok_typ001", kind="composite", ...)
    └── category: "lighting"
        └── StyleToken (id="tok_lit001", kind="lighting", ...)

Public API
----------
    add_category(name, description="") -> str
        Create a new category; return its slug.

    remove_category(name, cascade=False)
        Remove a category (raises if it has tokens and cascade=False).

    list_categories() -> list[CategoryInfo]
        Return all categories with token counts.

    add_token(category, token) -> None
        Add a StyleToken to a named category (creates category if absent).

    remove_token(token_id) -> bool
        Remove a token by id (from whatever category it lives in).
        Returns True if found and removed, False otherwise.

    get_token(token_id) -> StyleToken | None
        Look up a token by id.

    tokens_in_category(category) -> list[StyleToken]
        Return all tokens in a category (empty list if category absent).

    all_tokens() -> list[StyleToken]
        Return every token across all categories (flat list).

    rename_category(old_name, new_name) -> None
        Rename a category; moves all its tokens.

    to_dict() -> dict
        Serialise to a JSON-compatible dict.

    @classmethod from_dict(data) -> StyleLibrary
        Deserialise from a previously serialised dict.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from schema.production_document import StyleToken, StyleTokenKind


# ---------------------------------------------------------------------------
# Category slug normalisation
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9/_-]*$")


def _slug(name: str) -> str:
    """Normalise a category name to a lowercase slug (slashes allowed for hierarchy)."""
    return name.strip().lower().replace(" ", "_")


# ---------------------------------------------------------------------------
# CategoryInfo — lightweight descriptor returned by list_categories()
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CategoryInfo:
    name: str
    description: str
    token_count: int


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CategoryNotFound(KeyError):
    """Raised when a named category does not exist in the library."""


class CategoryNotEmpty(ValueError):
    """Raised when trying to remove a non-empty category without cascade=True."""


class DuplicateTokenId(ValueError):
    """Raised when a token with the same id already exists in the library."""


# ---------------------------------------------------------------------------
# StyleLibrary
# ---------------------------------------------------------------------------

class StyleLibrary:
    """Hierarchical store for StyleToken objects, grouped into named categories.

    The library is the root of a two-level hierarchy:
        LIBRARY → CATEGORY → TOKEN

    Thread safety: not thread-safe (prototype-grade, same as ProductionService).
    """

    def __init__(self, name: str = "default") -> None:
        self.name = name
        # category slug → list[StyleToken]
        self._categories: dict[str, list[StyleToken]] = {}
        # category slug → description string
        self._descriptions: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Category management
    # ------------------------------------------------------------------

    def add_category(self, name: str, description: str = "") -> str:
        """Create a new category and return its normalised slug.

        Idempotent — calling with an existing name updates the description.
        """
        slug = _slug(name)
        if slug not in self._categories:
            self._categories[slug] = []
        self._descriptions[slug] = description
        return slug

    def remove_category(self, name: str, cascade: bool = False) -> None:
        """Remove a category.

        Raises CategoryNotFound if the category does not exist.
        Raises CategoryNotEmpty if the category contains tokens and cascade=False.
        If cascade=True, tokens are silently deleted along with the category.
        """
        slug = _slug(name)
        if slug not in self._categories:
            raise CategoryNotFound(f"Category {name!r} not found in library {self.name!r}")
        if self._categories[slug] and not cascade:
            raise CategoryNotEmpty(
                f"Category {name!r} has {len(self._categories[slug])} token(s). "
                "Use cascade=True to delete tokens along with the category."
            )
        del self._categories[slug]
        self._descriptions.pop(slug, None)

    def list_categories(self) -> list[CategoryInfo]:
        """Return all categories with their token counts."""
        return [
            CategoryInfo(
                name=slug,
                description=self._descriptions.get(slug, ""),
                token_count=len(tokens),
            )
            for slug, tokens in sorted(self._categories.items())
        ]

    def rename_category(self, old_name: str, new_name: str) -> None:
        """Rename a category; its tokens move with it.

        Raises CategoryNotFound if old_name doesn't exist.
        If new_name already exists, tokens are merged into it.
        """
        old = _slug(old_name)
        new = _slug(new_name)
        if old not in self._categories:
            raise CategoryNotFound(f"Category {old_name!r} not found")
        if old == new:
            return
        if new not in self._categories:
            self._categories[new] = []
            self._descriptions[new] = self._descriptions.get(old, "")
        self._categories[new].extend(self._categories.pop(old))
        self._descriptions.pop(old, None)

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def add_token(self, category: str, token: StyleToken) -> None:
        """Add *token* to *category*, creating the category if it doesn't exist.

        Raises DuplicateTokenId if a token with the same id already exists
        anywhere in the library.
        """
        existing = self.get_token(token.id)
        if existing is not None:
            raise DuplicateTokenId(
                f"Token id {token.id!r} already exists in library {self.name!r}"
            )
        slug = _slug(category)
        if slug not in self._categories:
            self._categories[slug] = []
            self._descriptions[slug] = ""
        self._categories[slug].append(token)

    def remove_token(self, token_id: str) -> bool:
        """Remove a token by id. Returns True if found and removed, False otherwise."""
        for slug, tokens in self._categories.items():
            for i, tok in enumerate(tokens):
                if tok.id == token_id:
                    tokens.pop(i)
                    return True
        return False

    def get_token(self, token_id: str) -> Optional[StyleToken]:
        """Look up a token by id. Returns None if not found."""
        for tokens in self._categories.values():
            for tok in tokens:
                if tok.id == token_id:
                    return tok
        return None

    def tokens_in_category(self, category: str) -> list[StyleToken]:
        """Return all tokens in *category*. Returns empty list if category absent."""
        slug = _slug(category)
        return list(self._categories.get(slug, []))

    def all_tokens(self) -> list[StyleToken]:
        """Return every token across all categories (flat list, insertion order)."""
        result: list[StyleToken] = []
        for tokens in self._categories.values():
            result.extend(tokens)
        return result

    def category_of(self, token_id: str) -> Optional[str]:
        """Return the category slug containing *token_id*, or None if not found."""
        for slug, tokens in self._categories.items():
            for tok in tokens:
                if tok.id == token_id:
                    return slug
        return None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise the library to a JSON-compatible dict."""
        categories: dict[str, dict] = {}
        for slug, tokens in self._categories.items():
            categories[slug] = {
                "description": self._descriptions.get(slug, ""),
                "tokens": [
                    {
                        "id": tok.id,
                        "name": tok.name,
                        "kind": tok.kind,
                        "value": tok.value,
                        "tokens": tok.tokens,
                    }
                    for tok in tokens
                ],
            }
        return {"name": self.name, "categories": categories}

    @classmethod
    def from_dict(cls, data: dict) -> "StyleLibrary":
        """Deserialise from a previously serialised dict."""
        lib = cls(name=data.get("name", "default"))
        for slug, cat_data in (data.get("categories") or {}).items():
            lib._categories[slug] = []
            lib._descriptions[slug] = cat_data.get("description", "")
            for tok_data in cat_data.get("tokens") or []:
                tok = StyleToken(
                    id=tok_data["id"],
                    name=tok_data["name"],
                    kind=tok_data["kind"],
                    value=tok_data.get("value"),
                    tokens=tok_data.get("tokens") or {},
                )
                lib._categories[slug].append(tok)
        return lib

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return sum(len(tokens) for tokens in self._categories.values())

    def __repr__(self) -> str:  # pragma: no cover
        n_cats = len(self._categories)
        n_toks = len(self)
        return f"StyleLibrary(name={self.name!r}, categories={n_cats}, tokens={n_toks})"
