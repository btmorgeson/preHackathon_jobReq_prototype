from src.scoring.aggregator import _normalize_scores, _normalize_weights


def test_normalize_scores_min_max() -> None:
    ids = ["a", "b", "c"]
    scores = {"a": 0.2, "b": 0.5, "c": 0.8}
    normalized = _normalize_scores(scores, ids)
    assert normalized["a"] == 0.0
    assert normalized["c"] == 1.0
    assert 0.0 < normalized["b"] < 1.0


def test_normalize_scores_equal_values() -> None:
    ids = ["a", "b"]
    scores = {"a": 0.5, "b": 0.5}
    normalized = _normalize_scores(scores, ids)
    assert normalized == {"a": 1.0, "b": 1.0}


def test_normalize_weights_sum_to_one() -> None:
    weights = _normalize_weights({"skill": 2.0, "role": 1.0, "experience": 1.0})
    assert round(weights["skill"] + weights["role"] + weights["experience"], 6) == 1.0
    assert weights["skill"] == 0.5
