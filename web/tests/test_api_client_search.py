import httpx
import pytest
import respx

from app.api_client import ApiError, LandRegistryApiClient, ValidationFailed

BASE = "http://api.test"

PAGE = {
    "results": [
        {
            "titleNumber": "TGL100001",
            "tenure": "LEASEHOLD",
            "address": {
                "line1": "Flat 1, Riverside Court",
                "line2": "2 Wharf Lane",
                "town": "London",
                "postcode": "SE1 7PB",
            },
        }
    ],
    "total": 25,
    "previousCursor": None,
    "nextCursor": "QTpUR0wxMDAwMDE",
}


@pytest.fixture
def api():
    return LandRegistryApiClient(BASE, timeout=1.0)


@respx.mock
def test_search_titles_returns_the_page(api):
    respx.get(f"{BASE}/api/v1/titles").mock(return_value=httpx.Response(200, json=PAGE))

    page = api.search_titles("SE17PB")

    assert page["results"][0]["titleNumber"] == "TGL100001"
    assert page["total"] == 25
    assert page["nextCursor"] == "QTpUR0wxMDAwMDE"


@respx.mock
def test_search_titles_sends_the_postcode_and_the_cursor(api):
    route = respx.get(f"{BASE}/api/v1/titles").mock(return_value=httpx.Response(200, json=PAGE))

    api.search_titles("SE17PB", cursor="QTpUR0wxMDAwMDE")

    params = route.calls.last.request.url.params
    assert params["postcode"] == "SE17PB"
    assert params["cursor"] == "QTpUR0wxMDAwMDE"


@respx.mock
def test_the_first_page_sends_no_cursor(api):
    route = respx.get(f"{BASE}/api/v1/titles").mock(return_value=httpx.Response(200, json=PAGE))

    api.search_titles("SE17PB")

    assert "cursor" not in route.calls.last.request.url.params


@respx.mock
def test_a_rejected_cursor_raises_validation_failed(api):
    respx.get(f"{BASE}/api/v1/titles").mock(
        return_value=httpx.Response(
            400,
            json={
                "type": "https://land-registry.study/problems/validation-failed",
                "errors": {"cursor": "cursor is not valid; start again from the first page"},
            },
            headers={"content-type": "application/problem+json"},
        )
    )

    with pytest.raises(ValidationFailed) as exc:
        api.search_titles("SE17PB", cursor="bad")

    assert "cursor" in exc.value.errors


@respx.mock
def test_search_titles_raises_api_error_when_the_api_is_down(api):
    respx.get(f"{BASE}/api/v1/titles").mock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(ApiError):
        api.search_titles("SE17PB")
