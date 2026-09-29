import httpx
import pytest
import respx

from app.api_client import ApiError, LandRegistryApiClient, TitleNotFound

BASE = "http://api.test"

TITLE = {
    "titleNumber": "SGL123456",
    "tenure": "FREEHOLD",
    "classOfTitle": "Title absolute",
    "address": {"line1": "12 Mallow Gardens", "town": "Croydon", "postcode": "CR0 2QQ"},
    "pricePaidPence": 42500000,
    "pricePaidDate": "2019-06-14",
    "proprietors": [{"name": "ALEX MORGAN HOLLOWAY", "address": "12 Mallow Gardens"}],
    "charges": [],
}

PROBLEM_404 = {
    "type": "https://land-registry.study/problems/title-not-found",
    "title": "Title not found",
    "status": 404,
    "detail": "No title exists with the number ZZ000000",
    "instance": "/api/v1/titles/ZZ000000",
    "titleNumber": "ZZ000000",
}


@pytest.fixture
def api():
    return LandRegistryApiClient(BASE, timeout=1.0)


@respx.mock
def test_get_title_returns_the_json(api):
    respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(return_value=httpx.Response(200, json=TITLE))

    result = api.get_title("SGL123456")

    assert result["titleNumber"] == "SGL123456"
    assert result["address"]["postcode"] == "CR0 2QQ"


@respx.mock
def test_get_title_upper_cases_the_number(api):
    route = respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(
        return_value=httpx.Response(200, json=TITLE)
    )

    api.get_title("  sgl123456 ")

    assert route.called


@respx.mock
def test_get_title_raises_title_not_found_on_404(api):
    respx.get(f"{BASE}/api/v1/titles/ZZ000000").mock(
        return_value=httpx.Response(
            404, json=PROBLEM_404, headers={"content-type": "application/problem+json"}
        )
    )

    with pytest.raises(TitleNotFound) as exc:
        api.get_title("ZZ000000")

    assert exc.value.title_number == "ZZ000000"


@respx.mock
def test_get_title_raises_api_error_on_500(api):
    respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(return_value=httpx.Response(500, text="boom"))

    with pytest.raises(ApiError):
        api.get_title("SGL123456")


@respx.mock
def test_get_title_raises_api_error_when_the_api_is_down(api):
    respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(ApiError):
        api.get_title("SGL123456")


def test_title_not_found_is_an_api_error():
    # Lets routes handle ApiError only when the reason does not matter.
    assert issubclass(TitleNotFound, ApiError)
