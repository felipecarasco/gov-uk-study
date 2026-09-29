import httpx
import pytest
import respx
from bs4 import BeautifulSoup

from app import create_app

API = "http://api.test/api/v1/orders"


def order(status="PENDING_PAYMENT"):
    return {
        "reference": "LR-AAAA2222",
        "titleNumber": "SGL123456",
        "documentType": "TITLE_PLAN",
        "status": status,
        "amountPence": 300,
        "createdAt": "2026-09-10T12:00:00Z",
        "paidAt": "2026-09-10T12:05:00Z" if status == "PAID" else None,
    }


def placed_here(client, reference="LR-AAAA2222"):
    with client.session_transaction() as session:
        session["placed_orders"] = [reference]


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


@respx.mock
def test_shows_what_is_being_paid_for(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222").mock(return_value=httpx.Response(200, json=order()))

    soup = page(client.get("/order/payment/LR-AAAA2222"))

    text = soup.get_text()
    assert "LR-AAAA2222" in text
    assert "Title plan" in text
    assert "£3.00" in text
    assert "No money will be taken" in text
    assert soup.select_one("button.govuk-button").get_text(strip=True) == "Pay £3.00"


@respx.mock
def test_paying_calls_the_api_and_goes_to_the_confirmation(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222").mock(return_value=httpx.Response(200, json=order()))
    pay = respx.post(f"{API}/LR-AAAA2222/payment").mock(
        return_value=httpx.Response(200, json=order("PAID"))
    )

    response = client.post("/order/payment/LR-AAAA2222", data={})

    assert pay.called
    assert response.status_code == 302
    assert response.headers["Location"] == "/order/confirmation/LR-AAAA2222"


@respx.mock
def test_an_order_already_paid_goes_straight_to_the_confirmation(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222").mock(return_value=httpx.Response(200, json=order("PAID")))

    response = client.get("/order/payment/LR-AAAA2222")

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/confirmation/LR-AAAA2222"


@respx.mock
@pytest.mark.parametrize("method", ["get", "post"])
def test_another_browsers_order_is_not_found(client, method):
    # The reference is in the URL, so it can leak in a screenshot or a shared
    # link. Only the browser that placed the order may pay for it.
    route = respx.route(url__startswith=API).mock(return_value=httpx.Response(200, json=order()))

    response = getattr(client, method)("/order/payment/LR-AAAA2222")

    assert response.status_code == 404
    assert not route.called


@respx.mock
def test_an_order_the_api_does_not_know_is_not_found(client):
    placed_here(client)
    route = respx.get(f"{API}/LR-AAAA2222").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://land-registry.study/problems/order-not-found",
                "reference": "LR-AAAA2222",
            },
            headers={"content-type": "application/problem+json"},
        )
    )

    assert client.get("/order/payment/LR-AAAA2222").status_code == 404
    # The 404 must come from asking the API, not from a missing route.
    assert route.called


@respx.mock
def test_api_down_while_paying_returns_503(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222").mock(return_value=httpx.Response(200, json=order()))
    respx.post(f"{API}/LR-AAAA2222/payment").mock(side_effect=httpx.ConnectError("refused"))

    assert client.post("/order/payment/LR-AAAA2222", data={}).status_code == 503


@respx.mock
def test_paying_without_a_csrf_token_pays_nothing():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test",
            "API_BASE_URL": "http://api.test",
        }
    )
    client = app.test_client()
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222").mock(return_value=httpx.Response(200, json=order()))
    pay = respx.post(f"{API}/LR-AAAA2222/payment").mock(
        return_value=httpx.Response(200, json=order("PAID"))
    )

    response = client.post("/order/payment/LR-AAAA2222", data={})

    assert not pay.called
    assert response.status_code == 200
