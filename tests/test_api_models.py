from pydantic import ValidationError

from src.api.models import SearchRequest, SearchWeights


def test_search_request_requires_intent() -> None:
    try:
        SearchRequest()
        raise AssertionError("Expected validation error for missing search intent.")
    except ValidationError:
        pass


def test_search_weights_must_not_all_be_zero() -> None:
    try:
        SearchWeights(skill=0.0, role=0.0, experience=0.0)
        raise AssertionError("Expected validation error for zeroed weights.")
    except ValidationError:
        pass


def test_search_request_accepts_req_number_with_skills() -> None:
    payload = SearchRequest(
        req_number="REQ-001",
        required_skills=["Python"],
    )
    assert payload.req_number == "REQ-001"
    assert payload.top_k >= 1
