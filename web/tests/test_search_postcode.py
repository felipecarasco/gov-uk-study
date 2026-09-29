from bs4 import BeautifulSoup


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


def test_shows_the_postcode_field(client):
    soup = page(client.get("/search/postcode"))

    field = soup.select_one("input#postcode.govuk-input")
    assert field is not None
    assert field["autocomplete"] == "postal-code"
    assert soup.select_one("label[for='postcode']") is not None
    assert "CR0 2QQ" in soup.select_one("#postcode-hint").get_text()


def test_an_empty_submission_asks_for_a_postcode(client):
    soup = page(client.post("/search/postcode", data={"postcode": ""}))

    summary = soup.select_one(".govuk-error-summary")
    assert summary is not None
    assert "Enter a postcode" in summary.get_text()
    assert soup.title.string.startswith("Error: ")


def test_a_partial_postcode_gets_the_full_postcode_message(client):
    soup = page(client.post("/search/postcode", data={"postcode": "CR0"}))

    assert (
        "Enter a full postcode, like CR0 2QQ" in soup.select_one(".govuk-error-summary").get_text()
    )


def test_error_summary_links_point_at_fields_that_exist(client):
    soup = page(client.post("/search/postcode", data={"postcode": ""}))

    links = soup.select(".govuk-error-summary a[href^='#']")
    assert links, "the error summary has no anchor link"
    for link in links:
        assert soup.find(id=link["href"].removeprefix("#")) is not None


def test_a_valid_postcode_redirects_to_the_normalised_results(client):
    response = client.post("/search/postcode", data={"postcode": "  se1   7pb "})

    assert response.status_code == 302
    assert response.headers["Location"] == "/search/results?postcode=SE17PB"


def test_the_two_search_pages_link_to_each_other(client):
    by_number = page(client.get("/search/title-number"))
    by_postcode = page(client.get("/search/postcode"))

    assert by_number.select_one("a[href='/search/postcode']") is not None
    assert by_postcode.select_one("a[href='/search/title-number']") is not None


def test_the_start_page_mentions_searching_by_postcode(client):
    assert "postcode" in page(client.get("/")).get_text()
