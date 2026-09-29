import json

import httpx
import pytest
import respx

from app.api_client import (
    ApiError,
    LandRegistryApiClient,
    OrderNotFound,
    TitleNotFound,
    ValidationFailed,
)

BASE = "http://api.test"

ORDER = {
    "reference": "LR-AAAA2222",
    "titleNumber": "SGL123456",
    "documentType": "TITLE_REGISTER",
    "applicantName": "Alex Morgan Holloway",
    "applicantEmail": "alex@example.com",
    "applicantAddress": "12 Mallow Gardens, Croydon, CR0 2QQ",
    "status": "PENDING_PAYMENT",
    "amountPence": 300,
    "createdAt": "2026-09-10T12:00:00Z",
}

ORDER_DATA = {
    "title_number": "SGL123456",
    "document_type": "TITLE_REGISTER",
    "applicant_name": "Alex Morgan Holloway",
    "applicant_email": "alex@example.com",
    "applicant_address": "12 Mallow Gardens, Croydon, CR0 2QQ",
}

PROBLEM_JSON = {"content-type": "application/problem+json"}


@pytest.fixture
def api():
    return LandRegistryApiClient(BASE, timeout=1.0)


@respx.mock
def test_create_order_returns_the_order(api):
    respx.post(f"{BASE}/api/v1/orders").mock(return_value=httpx.Response(201, json=ORDER))

    result = api.create_order(**ORDER_DATA)

    assert result["reference"] == "LR-AAAA2222"
    assert result["amountPence"] == 300


@respx.mock
def test_create_order_sends_the_body_in_camel_case(api):
    route = respx.post(f"{BASE}/api/v1/orders").mock(return_value=httpx.Response(201, json=ORDER))

    api.create_order(**ORDER_DATA)

    sent = json.loads(route.calls[0].request.content)
    assert sent == {
        "titleNumber": "SGL123456",
        "documentType": "TITLE_REGISTER",
        "applicantName": "Alex Morgan Holloway",
        "applicantEmail": "alex@example.com",
        "applicantAddress": "12 Mallow Gardens, Croydon, CR0 2QQ",
    }


@respx.mock
def test_create_order_raises_title_not_found_on_its_problem_type(api):
    respx.post(f"{BASE}/api/v1/orders").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://land-registry.study/problems/title-not-found",
                "title": "Title not found",
                "status": 404,
                "titleNumber": "ZZ000000",
            },
            headers=PROBLEM_JSON,
        )
    )

    with pytest.raises(TitleNotFound) as exc:
        api.create_order(**ORDER_DATA)

    assert exc.value.title_number == "ZZ000000"


@respx.mock
def test_create_order_raises_validation_failed_with_the_fields(api):
    respx.post(f"{BASE}/api/v1/orders").mock(
        return_value=httpx.Response(
            400,
            json={
                "type": "https://land-registry.study/problems/validation-failed",
                "title": "Validation failed",
                "status": 400,
                "errors": {"applicantEmail": "must be a well-formed email address"},
            },
            headers=PROBLEM_JSON,
        )
    )

    with pytest.raises(ValidationFailed) as exc:
        api.create_order(**ORDER_DATA)

    assert exc.value.errors == {"applicantEmail": "must be a well-formed email address"}


@respx.mock
def test_get_order_returns_the_order(api):
    respx.get(f"{BASE}/api/v1/orders/LR-AAAA2222").mock(
        return_value=httpx.Response(200, json=ORDER)
    )

    assert api.get_order("LR-AAAA2222")["status"] == "PENDING_PAYMENT"


@respx.mock
def test_get_order_raises_order_not_found_on_its_problem_type(api):
    respx.get(f"{BASE}/api/v1/orders/LR-NOTEXIST").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://land-registry.study/problems/order-not-found",
                "reference": "LR-NOTEXIST",
            },
            headers=PROBLEM_JSON,
        )
    )

    with pytest.raises(OrderNotFound) as exc:
        api.get_order("LR-NOTEXIST")

    assert exc.value.reference == "LR-NOTEXIST"


@respx.mock
def test_a_404_without_a_problem_type_is_a_generic_api_error(api):
    # A proxy in front of the API can answer 404 with an HTML page. That says
    # nothing about the order, so it must not become OrderNotFound, and reading
    # the non-JSON body must not blow up.
    respx.get(f"{BASE}/api/v1/orders/LR-AAAA2222").mock(
        return_value=httpx.Response(404, text="<html>Not Found</html>")
    )

    with pytest.raises(ApiError) as exc:
        api.get_order("LR-AAAA2222")

    assert type(exc.value) is ApiError


@respx.mock
def test_create_order_raises_api_error_when_the_api_is_down(api):
    respx.post(f"{BASE}/api/v1/orders").mock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(ApiError):
        api.create_order(**ORDER_DATA)


def test_exception_hierarchy():
    # Routes that do not care about the reason handle ApiError only.
    assert issubclass(OrderNotFound, ApiError)
    assert issubclass(ValidationFailed, ApiError)
