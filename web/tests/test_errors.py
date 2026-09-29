import httpx
import respx
from bs4 import BeautifulSoup

from app import create_app


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


def test_an_unknown_address_gets_the_govuk_page_not_found(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    soup = page(response)
    assert soup.title.string.startswith("Page not found")
    assert soup.find("h1").get_text(strip=True) == "Page not found"
    assert "check it is correct" in soup.get_text()


def test_a_404_raised_by_a_route_gets_the_same_page(client):
    # The order was not placed in this browser, so the route aborts with 404.
    response = client.get("/order/payment/LR-AAAA2222")

    assert response.status_code == 404
    assert page(response).find("h1").get_text(strip=True) == "Page not found"


def test_an_unexpected_error_gets_the_problem_page_without_details():
    app = create_app(
        {
            "TESTING": True,
            "PROPAGATE_EXCEPTIONS": False,
            "SECRET_KEY": "test",
            "API_BASE_URL": "http://api.test",
        }
    )

    @app.get("/broken")
    def broken():
        raise RuntimeError("database password is hunter2")

    response = app.test_client().get("/broken")

    assert response.status_code == 500
    soup = page(response)
    assert soup.find("h1").get_text(strip=True) == "Sorry, there is a problem with the service"
    assert "hunter2" not in soup.get_text()


@respx.mock
def test_the_api_being_down_gets_the_service_unavailable_page(client):
    respx.get("http://api.test/api/v1/titles/SGL123456").mock(
        side_effect=httpx.ConnectError("refused")
    )

    response = client.get("/search/titles/SGL123456")

    assert response.status_code == 503
    assert page(response).find("h1").get_text(strip=True) == "Sorry, the service is unavailable"
