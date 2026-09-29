import httpx
import pytest
import respx

from app.api_client import ApiError, LandRegistryApiClient, OrderNotFound, OrderNotPaid

BASE = "http://api.test"
PROBLEM_JSON = {"content-type": "application/problem+json"}

PAID = {
    "reference": "LR-AAAA2222",
    "titleNumber": "SGL123456",
    "documentType": "TITLE_REGISTER",
    "status": "PAID",
    "amountPence": 300,
    "createdAt": "2026-09-10T12:00:00Z",
    "paidAt": "2026-09-10T12:05:00Z",
}


@pytest.fixture
def api():
    return LandRegistryApiClient(BASE, timeout=1.0)


@respx.mock
def test_pay_order_posts_and_returns_the_paid_order(api):
    route = respx.post(f"{BASE}/api/v1/orders/LR-AAAA2222/payment").mock(
        return_value=httpx.Response(200, json=PAID)
    )

    assert api.pay_order("LR-AAAA2222")["status"] == "PAID"
    assert route.called


@respx.mock
def test_paying_an_unknown_order_raises_order_not_found(api):
    respx.post(f"{BASE}/api/v1/orders/LR-NOTEXIST/payment").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://land-registry.study/problems/order-not-found",
                "reference": "LR-NOTEXIST",
            },
            headers=PROBLEM_JSON,
        )
    )

    with pytest.raises(OrderNotFound):
        api.pay_order("LR-NOTEXIST")


@respx.mock
def test_get_order_document_returns_the_pdf_and_its_file_name(api):
    respx.get(f"{BASE}/api/v1/orders/LR-AAAA2222/document").mock(
        return_value=httpx.Response(
            200,
            content=b"%PDF-1.7 fake",
            headers={
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="LR-AAAA2222-title-register.pdf"',
            },
        )
    )

    document = api.get_order_document("LR-AAAA2222")

    assert document.content == b"%PDF-1.7 fake"
    assert document.filename == "LR-AAAA2222-title-register.pdf"


@respx.mock
def test_get_order_document_accepts_the_pdf_and_problem_details(api):
    # Asking for application/json alone would get a 406 from the API.
    route = respx.get(f"{BASE}/api/v1/orders/LR-AAAA2222/document").mock(
        return_value=httpx.Response(
            200, content=b"%PDF-", headers={"content-type": "application/pdf"}
        )
    )

    api.get_order_document("LR-AAAA2222")

    accept = route.calls.last.request.headers["accept"]
    assert "application/pdf" in accept
    assert "application/problem+json" in accept


@respx.mock
def test_the_document_of_an_unpaid_order_raises_order_not_paid(api):
    respx.get(f"{BASE}/api/v1/orders/LR-AAAA2222/document").mock(
        return_value=httpx.Response(
            409,
            json={
                "type": "https://land-registry.study/problems/order-not-paid",
                "reference": "LR-AAAA2222",
            },
            headers=PROBLEM_JSON,
        )
    )

    with pytest.raises(OrderNotPaid) as exc:
        api.get_order_document("LR-AAAA2222")

    assert exc.value.reference == "LR-AAAA2222"


@respx.mock
def test_get_order_document_raises_api_error_when_the_api_is_down(api):
    respx.get(f"{BASE}/api/v1/orders/LR-AAAA2222/document").mock(
        side_effect=httpx.ConnectError("refused")
    )

    with pytest.raises(ApiError):
        api.get_order_document("LR-AAAA2222")


def test_order_not_paid_is_an_api_error():
    assert issubclass(OrderNotPaid, ApiError)
