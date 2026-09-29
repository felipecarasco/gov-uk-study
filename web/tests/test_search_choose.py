import pytest
from bs4 import BeautifulSoup


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


def test_asks_how_to_search_with_two_radios(client):
    soup = page(client.get("/search"))

    legend = soup.select_one("fieldset.govuk-fieldset legend h1")
    assert legend is not None
    assert "How do you want to search?" in legend.get_text()
    assert {i["value"] for i in soup.select("input.govuk-radios__input")} == {
        "title-number",
        "postcode",
    }


def test_choosing_nothing_shows_the_error_summary(client):
    soup = page(client.post("/search", data={}))

    assert "Select how you want to search" in soup.select_one(".govuk-error-summary").get_text()
    assert soup.title.string.startswith("Error: ")


@pytest.mark.parametrize(
    "choice, target", [("title-number", "/search/title-number"), ("postcode", "/search/postcode")]
)
def test_a_choice_leads_to_its_search(client, choice, target):
    response = client.post("/search", data={"search_by": choice})

    assert response.status_code == 302
    assert response.headers["Location"] == target


def test_a_value_outside_the_options_is_rejected(client):
    soup = page(client.post("/search", data={"search_by": "owner-name"}))

    assert "Select how you want to search" in soup.select_one(".govuk-error-summary").get_text()


@pytest.mark.parametrize("path", ["/search/title-number", "/search/postcode"])
def test_both_searches_go_back_to_the_choice(client, path):
    assert page(client.get(path)).select_one("a.govuk-back-link")["href"] == "/search"
