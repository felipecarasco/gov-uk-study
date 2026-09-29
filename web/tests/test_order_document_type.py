import httpx
import respx
from bs4 import BeautifulSoup

TITLE = {
    "titleNumber": "SGL123456",
    "tenure": "FREEHOLD",
    "classOfTitle": "Title absolute",
    "address": {"line1": "12 Mallow Gardens", "town": "Croydon", "postcode": "CR0 2QQ"},
    "proprietors": [{"name": "ALEX MORGAN HOLLOWAY", "address": "12 Mallow Gardens"}],
    "charges": [],
}


def test_title_detail_has_an_order_a_copy_button(client):
    with respx.mock:
        respx.get("http://api.test/api/v1/titles/SGL123456").mock(
            return_value=httpx.Response(200, json=TITLE)
        )
        html = client.get("/search/titles/SGL123456").get_data(as_text=True)

    soup = BeautifulSoup(html, "html.parser")
    button = soup.select_one("a.govuk-button[href='/order/start/SGL123456']")
    assert button is not None, "the title detail page has no 'Order a copy' button"
    assert "Order a copy" in button.get_text()


def test_start_keeps_the_title_in_the_session_and_redirects(client):
    response = client.get("/order/start/sgl123456")

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/document-type"

    with client.session_transaction() as session:
        assert session["order"]["title_number"] == "SGL123456"


def test_page_shows_both_document_types(client):
    client.get("/order/start/SGL123456")

    soup = BeautifulSoup(client.get("/order/document-type").get_data(as_text=True), "html.parser")

    assert soup.select_one(".govuk-radios") is not None
    values = {i["value"] for i in soup.select("input.govuk-radios__input")}
    assert values == {"TITLE_REGISTER", "TITLE_PLAN"}

    # GOV.UK requires a group of radios to live inside a fieldset with a legend.
    fieldset = soup.select_one("fieldset.govuk-fieldset")
    assert fieldset is not None
    assert fieldset.select_one("legend") is not None


def test_choosing_nothing_shows_the_error_summary(client):
    client.get("/order/start/SGL123456")

    response = client.post("/order/document-type", data={})
    assert response.status_code == 200

    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    summary = soup.select_one(".govuk-error-summary")
    assert summary is not None
    assert "Select a document type" in summary.get_text()
    assert soup.title.string.startswith("Error: ")


def test_error_summary_links_point_at_fields_that_exist(client):
    client.get("/order/start/SGL123456")
    response = client.post("/order/document-type", data={})
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")

    links = soup.select(".govuk-error-summary a[href^='#']")
    assert links, "the error summary has no anchor link"
    for link in links:
        target = link["href"].removeprefix("#")
        assert (
            soup.find(id=target) is not None
        ), f"the link points at #{target}, which is not on the page"


def test_a_valid_choice_moves_on_and_is_kept_in_the_session(client):
    client.get("/order/start/SGL123456")

    response = client.post("/order/document-type", data={"document_type": "TITLE_PLAN"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/your-details"

    with client.session_transaction() as session:
        assert session["order"]["document_type"] == "TITLE_PLAN"
        assert session["order"]["title_number"] == "SGL123456"


def test_a_value_outside_the_options_is_rejected_with_the_gds_message(client):
    client.get("/order/start/SGL123456")

    response = client.post("/order/document-type", data={"document_type": "ANYTHING"})

    assert response.status_code == 200
    summary = BeautifulSoup(response.get_data(as_text=True), "html.parser").select_one(
        ".govuk-error-summary"
    )
    assert summary is not None
    assert "Select a document type" in summary.get_text()
    assert "Not a valid choice" not in summary.get_text()
