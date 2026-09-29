import httpx
import pytest
import respx
from bs4 import BeautifulSoup

from app import create_app

BASE = "http://api.test"

CREATED_ORDER = {
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

COMPLETE_ORDER = {
    "title_number": "SGL123456",
    "document_type": "TITLE_REGISTER",
    "applicant_name": "Alex Morgan Holloway",
    "applicant_email": "alex@example.com",
    "applicant_address": "12 Mallow Gardens, Croydon, CR0 2QQ",
}


def fill_in(client):
    client.get("/order/start/SGL123456")
    client.post("/order/document-type", data={"document_type": "TITLE_REGISTER"})
    client.post(
        "/order/your-details",
        data={
            "applicant_name": "Alex Morgan Holloway",
            "applicant_email": "alex@example.com",
            "applicant_address": "12 Mallow Gardens, Croydon, CR0 2QQ",
        },
    )


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


def test_shows_every_answer(client):
    fill_in(client)
    soup = page(client.get("/order/check-answers"))

    assert "Check your answers" in soup.find("h1").get_text()

    text = soup.select_one(".govuk-summary-list").get_text()
    assert "SGL123456" in text
    assert "Title register" in text  # the label, not the value TITLE_REGISTER
    assert "Alex Morgan Holloway" in text
    assert "alex@example.com" in text
    assert "12 Mallow Gardens" in text


def test_shows_the_amount_to_pay(client):
    fill_in(client)
    assert "£3.00" in page(client.get("/order/check-answers")).get_text()


def test_change_links_go_back_to_the_right_question(client):
    fill_in(client)
    soup = page(client.get("/order/check-answers"))

    hrefs = [a["href"] for a in soup.select(".govuk-summary-list__actions a")]
    assert "/order/document-type?change=1" in hrefs
    assert "/order/your-details?change=1" in hrefs


def test_change_links_have_accessible_text(client):
    """Several 'Change' links on one page need context for screen readers;
    GOV.UK provides it with a visually hidden span."""
    fill_in(client)
    soup = page(client.get("/order/check-answers"))

    links = soup.select(".govuk-summary-list__actions a")
    assert links, "the page has no Change links"
    for link in links:
        hidden = link.select_one("span.govuk-visually-hidden")
        assert hidden is not None, f"link '{link.get_text(strip=True)}' has no hidden context"
        assert hidden.get_text(strip=True), "the hidden span is empty"


def test_change_returns_to_check_answers_after_saving(client):
    fill_in(client)

    response = client.post("/order/document-type?change=1", data={"document_type": "TITLE_PLAN"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/check-answers"

    with client.session_transaction() as session:
        assert session["order"]["document_type"] == "TITLE_PLAN"


def test_without_change_the_flow_goes_on_as_normal(client):
    client.get("/order/start/SGL123456")
    response = client.post("/order/document-type", data={"document_type": "TITLE_PLAN"})
    assert response.headers["Location"] == "/order/your-details"


def test_changing_the_document_type_shows_the_current_answer(client):
    fill_in(client)
    soup = page(client.get("/order/document-type?change=1"))

    checked = soup.select_one("input.govuk-radios__input[checked]")
    assert checked is not None, "no option is selected when coming back to change it"
    assert checked["value"] == "TITLE_REGISTER"


def test_back_link_returns_to_check_answers_while_changing(client):
    fill_in(client)
    soup = page(client.get("/order/your-details?change=1"))

    assert soup.select_one("a.govuk-back-link")["href"] == "/order/check-answers"


@respx.mock
def test_confirming_creates_the_order_and_redirects(client):
    fill_in(client)
    route = respx.post(f"{BASE}/api/v1/orders").mock(
        return_value=httpx.Response(201, json=CREATED_ORDER)
    )

    response = client.post("/order/check-answers", data={})

    assert route.called
    assert response.status_code == 302
    assert response.headers["Location"] == "/order/confirmation/LR-AAAA2222"


@respx.mock
def test_confirming_clears_the_session(client):
    fill_in(client)
    respx.post(f"{BASE}/api/v1/orders").mock(return_value=httpx.Response(201, json=CREATED_ORDER))

    client.post("/order/check-answers", data={})

    with client.session_transaction() as session:
        assert (
            "order" not in session
        ), "the session must be cleared: a reload must not create a duplicate order"


@respx.mock
def test_confirmation_page_shows_the_reference(client):
    respx.get(f"{BASE}/api/v1/orders/LR-AAAA2222").mock(
        return_value=httpx.Response(200, json=CREATED_ORDER)
    )

    response = client.get("/order/confirmation/LR-AAAA2222")
    assert response.status_code == 200

    panel = page(response).select_one(".govuk-panel--confirmation")
    assert panel is not None, "the GOV.UK green confirmation panel is missing"
    # The reference must be real bold text, not "<strong>" escaped into the page.
    strong = panel.select_one("strong")
    assert strong is not None and strong.get_text() == "LR-AAAA2222"
    assert "<strong>" not in panel.get_text()


@respx.mock
def test_confirmation_for_an_unknown_reference_returns_404(client):
    route = respx.get(f"{BASE}/api/v1/orders/LR-NOTEXIST").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://land-registry.study/problems/order-not-found",
                "reference": "LR-NOTEXIST",
            },
            headers={"content-type": "application/problem+json"},
        )
    )

    assert client.get("/order/confirmation/LR-NOTEXIST").status_code == 404
    # The 404 must come from asking the API, not from a missing route.
    assert route.called


@respx.mock
def test_an_api_validation_error_returns_to_check_answers(client):
    fill_in(client)
    respx.post(f"{BASE}/api/v1/orders").mock(
        return_value=httpx.Response(
            400,
            json={
                "type": "https://land-registry.study/problems/validation-failed",
                "errors": {"applicantEmail": "Enter an email address in the correct format"},
            },
            headers={"content-type": "application/problem+json"},
        )
    )

    response = client.post("/order/check-answers", data={})

    assert response.status_code == 200
    summary = page(response).select_one(".govuk-error-summary")
    assert summary is not None
    assert "Enter an email address in the correct format" in summary.get_text()
    # The error links to the page where the answer can be fixed.
    assert summary.select_one("a")["href"] == "/order/your-details?change=1"


@respx.mock
def test_api_down_returns_503(client):
    fill_in(client)
    respx.post(f"{BASE}/api/v1/orders").mock(side_effect=httpx.ConnectError("refused"))

    assert client.post("/order/check-answers", data={}).status_code == 503


@pytest.fixture
def csrf_client():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test",
            "API_BASE_URL": "http://api.test",
        }
    )
    return app.test_client()


@respx.mock
def test_confirming_without_a_csrf_token_creates_nothing(csrf_client):
    # Without the token check, any other site could post this form using the
    # victim's session and place an order in their name.
    with csrf_client.session_transaction() as session:
        session["order"] = dict(COMPLETE_ORDER)
    route = respx.post(f"{BASE}/api/v1/orders").mock(
        return_value=httpx.Response(201, json=CREATED_ORDER)
    )

    response = csrf_client.post("/order/check-answers", data={})

    assert not route.called
    # The page is shown again, with nothing sent, rather than failing.
    assert response.status_code == 200
    assert "Check your answers" in page(response).get_text()
    with csrf_client.session_transaction() as session:
        assert "order" in session
