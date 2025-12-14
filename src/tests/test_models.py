from datetime import datetime

from snipster.models import Language, Snippet

# def test_models_snippet_title_validation():
#     with pytest.raises(ValidationError):
#         Snippet(code="print(Hello)")

# def test_models_snippet_code_validation():
#     with pytest.raises(ValidationError) as exc_info:
#         Snippet(title="Hello World")

#     print(exc_info.value)


def test_model_snippet_favorite_default():
    snippet = Snippet(title="Hello World", code="print(Hello World)")
    assert not snippet.favorite


def test_model_snippet_language_default():
    snippet = Snippet(title="Hello World", code="print(Hello World)")
    assert snippet.language == "python"


def test_model_snippet_description_default():
    snippet = Snippet(title="Hello World", code="print(Hello World)")
    assert snippet.description is None


def test_model_snippet_tags_default():
    snippet = Snippet(title="Hello World", code="print(Hello World)")
    assert snippet.tags is None


def test_model_snippet_created_at_default():
    snippet = Snippet(title="Hello World", code="print(Hello World)")
    assert snippet.created_at is not None
    assert (datetime.now() - snippet.created_at).seconds < 10


def test_model_snippet_updated_at_default():
    snippet = Snippet(title="Hello World", code="print(Hello World)")
    assert snippet.updated_at is not None
    assert (datetime.now() - snippet.updated_at).seconds < 10


def test_model_language_enum():
    language = Language("python")
    assert language.name == "PYTHON"
