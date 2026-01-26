from snipster.types import Language


def test_language_enum_values():
    """Test Language enum has expected values"""
    assert Language.PYTHON.value == "Python"
    assert Language.JAVASCRIPT.value == "JavaScript"
    assert Language.TYPESCRIPT.value == "TypeScript"


def test_language_enum_membership():
    """Test Language enum membership"""
    assert "Python" in [lang.value for lang in Language]
    assert len(Language) == 3


def test_language_is_string_enum():
    """Test Language inherits from str"""
    assert isinstance(Language.PYTHON, str)
    assert Language.PYTHON == "Python"
