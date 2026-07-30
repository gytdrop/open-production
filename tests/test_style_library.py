"""Tests for StyleLibrary — §12 Customization / Style Token Library Hierarchy."""
from __future__ import annotations

import pytest

from schema.production_document import StyleToken
from service.style_library import (
    StyleLibrary,
    CategoryInfo,
    CategoryNotEmpty,
    CategoryNotFound,
    DuplicateTokenId,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _token(suffix: str, kind: str = "color") -> StyleToken:
    return StyleToken(id=f"tok_{suffix}", name=f"Token {suffix}", kind=kind)


# ---------------------------------------------------------------------------
# add_category / list_categories
# ---------------------------------------------------------------------------

def test_add_category_returns_slug():
    lib = StyleLibrary()
    slug = lib.add_category("Palette")
    assert slug == "palette"


def test_add_category_is_idempotent():
    """Calling add_category twice with the same name must not raise."""
    lib = StyleLibrary()
    lib.add_category("palette")
    lib.add_category("palette")
    assert len(lib.list_categories()) == 1


def test_add_category_normalises_spaces():
    lib = StyleLibrary()
    lib.add_category("Primary Palette")
    cats = {c.name for c in lib.list_categories()}
    assert "primary_palette" in cats


def test_add_category_with_description():
    lib = StyleLibrary()
    lib.add_category("lighting", description="Key and fill lighting tokens")
    cats = {c.name: c for c in lib.list_categories()}
    assert cats["lighting"].description == "Key and fill lighting tokens"


def test_list_categories_empty_library():
    lib = StyleLibrary()
    assert lib.list_categories() == []


def test_list_categories_sorted():
    lib = StyleLibrary()
    lib.add_category("zulu")
    lib.add_category("alpha")
    names = [c.name for c in lib.list_categories()]
    assert names == sorted(names)


def test_list_categories_token_count():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    lib.add_token("palette", _token("pal002"))
    lib.add_token("typography", _token("typ001", kind="composite"))
    cats = {c.name: c for c in lib.list_categories()}
    assert cats["palette"].token_count == 2
    assert cats["typography"].token_count == 1


# ---------------------------------------------------------------------------
# remove_category
# ---------------------------------------------------------------------------

def test_remove_empty_category():
    lib = StyleLibrary()
    lib.add_category("temp")
    lib.remove_category("temp")
    assert len(lib.list_categories()) == 0


def test_remove_category_not_found_raises():
    lib = StyleLibrary()
    with pytest.raises(CategoryNotFound):
        lib.remove_category("nonexistent")


def test_remove_nonempty_category_raises_without_cascade():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    with pytest.raises(CategoryNotEmpty):
        lib.remove_category("palette")


def test_remove_nonempty_category_with_cascade():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    lib.remove_category("palette", cascade=True)
    assert lib.list_categories() == []
    assert lib.all_tokens() == []


# ---------------------------------------------------------------------------
# add_token
# ---------------------------------------------------------------------------

def test_add_token_creates_category_if_absent():
    lib = StyleLibrary()
    tok = _token("auto001")
    lib.add_token("newcat", tok)
    assert lib.get_token("tok_auto001") is not None
    cats = {c.name for c in lib.list_categories()}
    assert "newcat" in cats


def test_add_token_duplicate_id_raises():
    lib = StyleLibrary()
    tok = _token("pal001")
    lib.add_token("palette", tok)
    with pytest.raises(DuplicateTokenId):
        lib.add_token("palette", tok)


def test_add_token_duplicate_id_different_category_raises():
    """A token id must be unique across the entire library, not just within a category."""
    lib = StyleLibrary()
    tok = _token("pal001")
    lib.add_token("palette", tok)
    with pytest.raises(DuplicateTokenId):
        lib.add_token("typography", tok)


# ---------------------------------------------------------------------------
# remove_token
# ---------------------------------------------------------------------------

def test_remove_token_returns_true():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    assert lib.remove_token("tok_pal001") is True


def test_remove_token_returns_false_for_unknown():
    lib = StyleLibrary()
    assert lib.remove_token("tok_unknown") is False


def test_remove_token_no_longer_retrievable():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    lib.remove_token("tok_pal001")
    assert lib.get_token("tok_pal001") is None


def test_remove_token_decrements_category_count():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    lib.add_token("palette", _token("pal002"))
    lib.remove_token("tok_pal001")
    cats = {c.name: c for c in lib.list_categories()}
    assert cats["palette"].token_count == 1


# ---------------------------------------------------------------------------
# get_token
# ---------------------------------------------------------------------------

def test_get_token_found():
    lib = StyleLibrary()
    tok = _token("pal001")
    lib.add_token("palette", tok)
    assert lib.get_token("tok_pal001") is tok


def test_get_token_not_found_returns_none():
    lib = StyleLibrary()
    assert lib.get_token("tok_nobody") is None


# ---------------------------------------------------------------------------
# tokens_in_category
# ---------------------------------------------------------------------------

def test_tokens_in_category_returns_list():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    lib.add_token("palette", _token("pal002"))
    toks = lib.tokens_in_category("palette")
    assert len(toks) == 2


def test_tokens_in_category_absent_returns_empty():
    lib = StyleLibrary()
    assert lib.tokens_in_category("nonexistent") == []


def test_tokens_in_category_normalises_name():
    """Category name lookup is case-insensitive (slug normalisation)."""
    lib = StyleLibrary()
    lib.add_token("Palette", _token("pal001"))
    assert len(lib.tokens_in_category("palette")) == 1
    assert len(lib.tokens_in_category("PALETTE")) == 1


# ---------------------------------------------------------------------------
# all_tokens
# ---------------------------------------------------------------------------

def test_all_tokens_flat_list():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    lib.add_token("typography", _token("typ001", kind="composite"))
    lib.add_token("lighting", _token("lit001", kind="lighting"))
    all_toks = lib.all_tokens()
    assert len(all_toks) == 3


def test_all_tokens_empty_library():
    lib = StyleLibrary()
    assert lib.all_tokens() == []


# ---------------------------------------------------------------------------
# rename_category
# ---------------------------------------------------------------------------

def test_rename_category():
    lib = StyleLibrary()
    lib.add_token("old_name", _token("tok0001"))
    lib.rename_category("old_name", "new_name")
    assert lib.tokens_in_category("new_name") != []
    assert lib.tokens_in_category("old_name") == []


def test_rename_category_merges_into_existing():
    """Renaming into an existing category merges tokens."""
    lib = StyleLibrary()
    lib.add_token("a", _token("tok_aa01"))
    lib.add_token("b", _token("tok_bb01"))
    lib.rename_category("a", "b")
    assert len(lib.tokens_in_category("b")) == 2
    assert lib.tokens_in_category("a") == []


def test_rename_category_not_found_raises():
    lib = StyleLibrary()
    with pytest.raises(CategoryNotFound):
        lib.rename_category("ghost", "new")


def test_rename_category_same_name_is_noop():
    lib = StyleLibrary()
    lib.add_token("palette", _token("pal001"))
    lib.rename_category("palette", "palette")
    assert len(lib.tokens_in_category("palette")) == 1


# ---------------------------------------------------------------------------
# category_of
# ---------------------------------------------------------------------------

def test_category_of_found():
    lib = StyleLibrary()
    lib.add_token("lighting", _token("lit001", kind="lighting"))
    assert lib.category_of("tok_lit001") == "lighting"


def test_category_of_not_found_returns_none():
    lib = StyleLibrary()
    assert lib.category_of("tok_nobody") is None


# ---------------------------------------------------------------------------
# __len__
# ---------------------------------------------------------------------------

def test_len_reflects_total_token_count():
    lib = StyleLibrary()
    assert len(lib) == 0
    lib.add_token("a", _token("aa0001"))
    lib.add_token("b", _token("bb0001"))
    assert len(lib) == 2
    lib.remove_token("tok_aa0001")
    assert len(lib) == 1


# ---------------------------------------------------------------------------
# Serialise / deserialise
# ---------------------------------------------------------------------------

def test_to_dict_round_trips():
    """from_dict(to_dict()) must reproduce the same tokens and categories."""
    lib = StyleLibrary(name="test_lib")
    lib.add_category("palette", description="Colour tokens")
    tok = _token("pal001")
    lib.add_token("palette", tok)
    lib.add_token("typography", _token("typ001", kind="composite"))

    data = lib.to_dict()
    lib2 = StyleLibrary.from_dict(data)
    assert lib2.name == "test_lib"
    assert len(lib2) == 2
    recovered = lib2.get_token("tok_pal001")
    assert recovered is not None
    assert recovered.name == tok.name
    assert recovered.kind == tok.kind


def test_to_dict_preserves_category_descriptions():
    lib = StyleLibrary()
    lib.add_category("lighting", description="Key and fill")
    data = lib.to_dict()
    lib2 = StyleLibrary.from_dict(data)
    cats = {c.name: c for c in lib2.list_categories()}
    assert cats["lighting"].description == "Key and fill"


def test_from_dict_empty():
    lib = StyleLibrary.from_dict({})
    assert len(lib) == 0
    assert lib.list_categories() == []


def test_hierarchy_name():
    """Library name is preserved through serialisation."""
    lib = StyleLibrary(name="brand_kit")
    d = lib.to_dict()
    lib2 = StyleLibrary.from_dict(d)
    assert lib2.name == "brand_kit"


# ---------------------------------------------------------------------------
# StyleToken value preservation
# ---------------------------------------------------------------------------

def test_token_value_and_tokens_dict_preserved():
    """StyleToken.value and StyleToken.tokens survive round-trip serialisation."""
    lib = StyleLibrary()
    tok = StyleToken(id="tok_cx0001", name="Primary Blue", kind="color",
                     value="#3b82d4", tokens={"hex": "#3b82d4", "rgb": "59,130,212"})
    lib.add_token("palette", tok)
    lib2 = StyleLibrary.from_dict(lib.to_dict())
    recovered = lib2.get_token("tok_cx0001")
    assert recovered.value == "#3b82d4"
    assert recovered.tokens == {"hex": "#3b82d4", "rgb": "59,130,212"}
