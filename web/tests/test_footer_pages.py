import pytest
from bs4 import BeautifulSoup


def page(client, path):
    return BeautifulSoup(client.get(path).get_data(as_text=True), "html.parser")


def test_the_footer_links_to_the_three_pages(client):
    hrefs = {a["href"] for a in page(client, "/").select("footer .govuk-footer__meta a")}

    assert {"/accessibility", "/cookies", "/privacy"} <= hrefs


@pytest.mark.parametrize(
    "path, heading",
    [
        ("/accessibility", "Accessibility statement"),
        ("/cookies", "Cookies"),
        ("/privacy", "Privacy notice"),
    ],
)
def test_each_page_exists(client, path, heading):
    response = client.get(path)

    assert response.status_code == 200
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    assert soup.find("h1").get_text(strip=True) == heading


def test_the_cookies_page_names_the_only_cookie(client):
    text = page(client, "/cookies").get_text()

    assert "session" in text
    assert "essential" in text
