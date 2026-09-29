from bs4 import BeautifulSoup


def test_get_shows_the_form(client):
    response = client.get("/search/title-number")
    assert response.status_code == 200

    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    field = soup.select_one("input#title_number.govuk-input")
    assert field is not None
    assert soup.select_one("label[for='title_number']") is not None
    assert "SGL123456" in soup.select_one("#title_number-hint").get_text()


def test_empty_submission_shows_the_error_summary(client):
    response = client.post("/search/title-number", data={"title_number": ""})
    assert response.status_code == 200

    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")

    summary = soup.select_one(".govuk-error-summary")
    assert summary is not None, "the error summary is missing from the top of the page"
    assert "Enter a title number" in summary.get_text()

    assert soup.select_one("input#title_number.govuk-input--error") is not None
    assert soup.select_one(".govuk-error-message") is not None


def test_page_title_starts_with_error_when_there_is_an_error(client):
    # Screen readers announce the <title> first; GOV.UK requires the prefix.
    response = client.post("/search/title-number", data={"title_number": ""})
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    assert soup.title.string.startswith("Error: ")


def test_error_summary_links_point_at_fields_that_exist(client):
    """Every anchor in the summary has to land on an element that really
    exists on the page."""
    response = client.post("/search/title-number", data={"title_number": ""})
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")

    links = soup.select(".govuk-error-summary a[href^='#']")
    assert links, "the error summary has no anchor link"

    for link in links:
        target = link["href"].removeprefix("#")
        assert (
            soup.find(id=target) is not None
        ), f"the error summary link points at #{target}, which is not on the page"


def test_invalid_format_shows_a_specific_message(client):
    response = client.post("/search/title-number", data={"title_number": "123"})
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    assert "correct format" in soup.select_one(".govuk-error-summary").get_text()


def test_valid_title_redirects_to_the_detail(client):
    # No API mock needed: the route only validates and redirects, without calling the back end.
    response = client.post("/search/title-number", data={"title_number": "sgl123456"})

    assert response.status_code == 302
    assert response.headers["Location"] == "/search/titles/SGL123456"
