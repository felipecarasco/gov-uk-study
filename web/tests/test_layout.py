import pytest
from bs4 import BeautifulSoup

# Pages that render without calling the API.
PAGES = ["/", "/search/title-number", "/search/postcode"]


def page(client, path):
    return BeautifulSoup(client.get(path).get_data(as_text=True), "html.parser")


@pytest.mark.parametrize("path", PAGES)
def test_every_page_has_one_header_main_and_footer_landmark(client, path):
    # Screen reader users jump between landmarks; without <header> and <footer>
    # there is no way to reach the footer links except reading the whole page.
    soup = page(client, path)

    assert len(soup.select("body > header")) == 1
    assert len(soup.select("main")) == 1
    assert len(soup.select("body > footer")) == 1


def test_the_header_keeps_the_service_name_linking_to_the_start(client):
    link = page(client, "/").select_one("header a[href='/']")

    assert link is not None
    assert "Search the land register" in link.get_text()


def test_the_footer_keeps_its_links(client):
    footer = page(client, "/").select_one("body > footer")

    assert footer.select(".govuk-footer__meta a")
