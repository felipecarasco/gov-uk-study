from bs4 import BeautifulSoup


def test_start_page_returns_200(client):
    assert client.get("/").status_code == 200


def test_start_page_has_a_title_and_a_start_button(client):
    html = client.get("/").get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")

    assert "Search the land register" in soup.title.string

    h1 = soup.find("h1")
    assert h1 is not None
    assert "Search the land register" in h1.get_text()

    button = soup.select_one("a.govuk-button--start")
    assert button is not None, "the green start page button is missing"
    assert button.get_text(strip=True).startswith("Start now")
    assert button["href"] == "/search/title-number"


def test_start_page_loads_the_govuk_css(client):
    html = client.get("/").get_data(as_text=True)
    assert "govuk-frontend.min.css" in html
    assert 'class="govuk-template' in html


def test_start_page_has_a_skip_link(client):
    # GOV.UK accessibility requirement: the first focusable element on the page.
    soup = BeautifulSoup(client.get("/").get_data(as_text=True), "html.parser")
    skip = soup.select_one("a.govuk-skip-link")
    assert skip is not None
    assert skip["href"] == "#main-content"
