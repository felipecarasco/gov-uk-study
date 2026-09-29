import httpx
import respx
from bs4 import BeautifulSoup

API = "http://api.test/api/v1/orders"
PROBLEM_JSON = {"content-type": "application/problem+json"}


def order(status="PAID"):
    return {
        "reference": "LR-AAAA2222",
        "titleNumber": "SGL123456",
        "documentType": "TITLE_REGISTER",
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
def test_shows_the_reference_and_a_link_to_download_the_copy(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222").mock(return_value=httpx.Response(200, json=order()))

    response = client.get("/order/confirmation/LR-AAAA2222")
    assert response.status_code == 200

    soup = page(response)
    panel = soup.select_one(".govuk-panel--confirmation")
    assert panel is not None
    assert panel.select_one("strong").get_text() == "LR-AAAA2222"
    download = soup.select_one("a[href='/order/LR-AAAA2222/document']")
    assert download is not None
    assert "PDF" in download.get_text()


@respx.mock
def test_an_unpaid_order_goes_back_to_the_payment(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222").mock(
        return_value=httpx.Response(200, json=order("PENDING_PAYMENT"))
    )

    response = client.get("/order/confirmation/LR-AAAA2222")

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/payment/LR-AAAA2222"


@respx.mock
def test_another_browsers_confirmation_is_not_found(client):
    route = respx.route(url__startswith=API).mock(return_value=httpx.Response(200, json=order()))

    assert client.get("/order/confirmation/LR-AAAA2222").status_code == 404
    assert not route.called


@respx.mock
def test_a_reference_the_api_does_not_know_is_not_found(client):
    placed_here(client)
    route = respx.get(f"{API}/LR-AAAA2222").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://land-registry.study/problems/order-not-found",
                "reference": "LR-AAAA2222",
            },
            headers=PROBLEM_JSON,
        )
    )

    assert client.get("/order/confirmation/LR-AAAA2222").status_code == 404
    assert route.called


@respx.mock
def test_downloads_the_pdf_as_an_attachment(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222/document").mock(
        return_value=httpx.Response(
            200,
            content=b"%PDF-1.7 fake",
            headers={
                "content-type": "application/pdf",
                "content-disposition": 'attachment; filename="LR-AAAA2222-title-register.pdf"',
            },
        )
    )

    response = client.get("/order/LR-AAAA2222/document")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data == b"%PDF-1.7 fake"
    assert (
        response.headers["Content-Disposition"]
        == "attachment; filename=LR-AAAA2222-title-register.pdf"
    )


@respx.mock
def test_downloading_an_unpaid_order_goes_back_to_the_payment(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222/document").mock(
        return_value=httpx.Response(
            409,
            json={
                "type": "https://land-registry.study/problems/order-not-paid",
                "reference": "LR-AAAA2222",
            },
            headers=PROBLEM_JSON,
        )
    )

    response = client.get("/order/LR-AAAA2222/document")

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/payment/LR-AAAA2222"


@respx.mock
def test_another_browsers_document_is_not_found(client):
    route = respx.route(url__startswith=API).mock(
        return_value=httpx.Response(200, content=b"%PDF-")
    )

    assert client.get("/order/LR-AAAA2222/document").status_code == 404
    assert not route.called


@respx.mock
def test_downloading_while_the_api_is_down_returns_503(client):
    placed_here(client)
    respx.get(f"{API}/LR-AAAA2222/document").mock(side_effect=httpx.ConnectError("refused"))

    assert client.get("/order/LR-AAAA2222/document").status_code == 503
