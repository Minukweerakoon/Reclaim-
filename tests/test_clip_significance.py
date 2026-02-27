def classify_significance(similarity: float, ci: tuple, threshold: float = 0.85):
    low, high = ci
    if low >= threshold:
        return 'positive'
    if high < threshold:
        return 'negative'
    return 'borderline'


def test_significance_positive():
    assert classify_significance(0.9, (0.86, 0.94)) == 'positive'


def test_significance_negative():
    assert classify_significance(0.6, (0.4, 0.7)) == 'negative'


def test_significance_borderline():
    assert classify_significance(0.84, (0.78, 0.88)) == 'borderline'

