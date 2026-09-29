from bs4 import BeautifulSoup

VALID_DETAILS = {
    "applicant_name": "Alex Morgan Holloway",
    "applicant_email": "alex@example.com",
    "applicant_address": "12 Mallow Gardens, Croydon, CR0 2QQ",
}


def start(client, document_type="TITLE_REGISTER"):
    client.get("/order/start/SGL123456")
    client.post("/order/document-type", data={"document_type": document_type})


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


def test_shows_the_three_fields(client):
    start(client)
    soup = page(client.get("/order/your-details"))

    assert soup.select_one("input#applicant_name.govuk-input") is not None
    assert soup.select_one("input#applicant_email.govuk-input") is not None
    assert soup.select_one("textarea#applicant_address.govuk-textarea") is not None

    for field in ("applicant_name", "applicant_email", "applicant_address"):
        assert soup.select_one(f"label[for='{field}']") is not None, f"{field} has no label"


def test_email_and_name_have_the_right_type_and_autocomplete(client):
    start(client)
    soup = page(client.get("/order/your-details"))

    email = soup.select_one("input#applicant_email")
    assert email["type"] == "email"
    assert email["autocomplete"] == "email"

    name = soup.select_one("input#applicant_name")
    assert name["autocomplete"] == "name"


def test_an_empty_submission_lists_the_three_errors(client):
    start(client)
    summary = page(client.post("/order/your-details", data={})).select_one(".govuk-error-summary")
    assert summary is not None

    text = summary.get_text()
    assert "Enter your full name" in text
    assert "Enter your email address" in text
    assert "Enter your address" in text

    # One link per field in error, in the same order as the fields on the page.
    targets = [a["href"] for a in summary.select("a[href^='#']")]
    assert targets == ["#applicant_name", "#applicant_email", "#applicant_address"]


def test_error_summary_links_point_at_fields_that_exist(client):
    start(client)
    soup = page(client.post("/order/your-details", data={}))

    links = soup.select(".govuk-error-summary a[href^='#']")
    # Without this, a page with no summary at all would pass: the loop never runs.
    assert links, "the error summary has no anchor link"
    for link in links:
        target = link["href"].removeprefix("#")
        assert soup.find(id=target) is not None


def test_an_invalid_email_gets_the_gds_message(client):
    start(client)
    response = client.post(
        "/order/your-details", data={**VALID_DETAILS, "applicant_email": "not-an-email"}
    )

    text = page(response).get_text()
    assert "Enter an email address in the correct format, like name@example.com" in text


def test_a_name_that_is_too_long_is_rejected(client):
    start(client)
    response = client.post(
        "/order/your-details", data={**VALID_DETAILS, "applicant_name": "x" * 256}
    )

    assert "Full name must be 255 characters or fewer" in page(response).get_text()


def test_valid_details_move_on_and_are_kept_in_the_session(client):
    start(client)
    response = client.post(
        "/order/your-details",
        data={
            "applicant_name": "  Alex Morgan Holloway  ",
            "applicant_email": "  ALEX@example.com ",
            "applicant_address": "12 Mallow Gardens, Croydon, CR0 2QQ",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/check-answers"

    with client.session_transaction() as session:
        order = session["order"]
        # Surrounding spaces are trimmed; the email is lower-cased.
        assert order["applicant_name"] == "Alex Morgan Holloway"
        assert order["applicant_email"] == "alex@example.com"
        assert order["applicant_address"] == "12 Mallow Gardens, Croydon, CR0 2QQ"
        # Earlier answers survive.
        assert order["title_number"] == "SGL123456"
        assert order["document_type"] == "TITLE_REGISTER"


def test_the_form_is_filled_in_when_coming_back(client):
    start(client)
    client.post(
        "/order/your-details", data={**VALID_DETAILS, "applicant_address": "12 Mallow Gardens"}
    )

    soup = page(client.get("/order/your-details"))
    assert soup.select_one("input#applicant_name")["value"] == "Alex Morgan Holloway"
    assert soup.select_one("textarea#applicant_address").get_text() == "12 Mallow Gardens"


def test_a_name_of_only_spaces_counts_as_empty(client):
    # The trim filter turns "   " into "". A validator that only checks that
    # something was sent (InputRequired) would accept it.
    start(client)
    response = client.post("/order/your-details", data={**VALID_DETAILS, "applicant_name": "   "})

    assert response.status_code == 200
    assert "Enter your full name" in page(response).get_text()
