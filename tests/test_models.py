from datetime import datetime, timezone

import pytest
from pydantic_core import ValidationError

from snipster import Language, Snippet


@pytest.fixture
def simple_snippet():
    """Factory for creating a minimal valid snippet"""
    return Snippet(title="Hello World", code="print('Hello World')")


@pytest.fixture
def snippet_factory():
    """Factory function for creating custom snippets"""

    def _create(**kwargs):  # pragma: no cover
        default = {
            "title": "Hello World",
            "code": "print(Hello World)",
        }
        default.update(kwargs)
        return Snippet(**default)

    return _create  # pragma: no cover


def test_model_snippet_favorite_default(simple_snippet):
    snippet = simple_snippet
    assert not snippet.favorite


def test_model_snippet_description_default(simple_snippet):
    snippet = simple_snippet
    assert snippet.description is None


def test_model_snippet_tags_default(simple_snippet):
    snippet = simple_snippet
    assert snippet.tags is None


class TestTimestampDefaults:
    """Group all default timestamp fields tests"""

    def test_model_snippet_timestamp_default(self):
        before = datetime.now(timezone.utc)
        snippet = Snippet(title="Hello World", code="print('Hello World')")
        after = datetime.now(timezone.utc)

        assert snippet.created_at is not None
        assert before <= snippet.created_at <= after

    def test_model_snippet_updated_at_default(self):
        before = datetime.now(timezone.utc)
        snippet = Snippet(title="Hello World", code="print('Hello World')")
        after = datetime.now(timezone.utc)

        assert snippet.updated_at is not None
        assert before <= snippet.updated_at <= after


class TestLanguageEnums:
    """Group all Language Enums tests"""

    @pytest.mark.parametrize(
        "lang_value,expected_name",
        [
            ("Python", "PYTHON"),
            ("JavaScript", "JAVASCRIPT"),
            ("TypeScript", "TYPESCRIPT"),
        ],
    )
    def test_language_enum_valid_values(self, lang_value, expected_name):
        """Test all valid Language enum values"""
        language = Language(lang_value)
        assert language.name == expected_name
        assert language.value == lang_value

    def test_model_snippet_language_default(self, simple_snippet):
        snippet = simple_snippet
        assert snippet.language == Language.PYTHON

    def test_language_enum_invalid_value(self):
        """Test that invalid language raises ValueError"""
        with pytest.raises(ValueError, match="not a valid Language"):
            Language("R")

    def test_language_enum_comparison(self):
        """Test that Language enums can be compared"""
        python1 = Language.PYTHON
        python2 = Language.PYTHON
        javascript = Language.JAVASCRIPT

        assert python1 == python2
        assert python1 != javascript


def test_title_field_validation(snippet_factory):
    test_data = {"title": "XX", "code": "print('test')"}

    with pytest.raises(ValidationError, match="Title must be at least 3 characters"):
        snippet_factory(**test_data)
