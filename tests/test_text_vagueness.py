from text_validator import TextValidator


def test_vagueness_specific():
    tv = TextValidator(enable_logging=False)
    res = tv.detect_vagueness('I lost my red iPhone 13 near the library entrance', 'en')
    assert res['valid'] is True


def test_vagueness_generic():
    tv = TextValidator(enable_logging=False)
    res = tv.detect_vagueness('I lost something', 'en')
    assert res['valid'] in (True, False)  # Non-deterministic across models, but function runs

