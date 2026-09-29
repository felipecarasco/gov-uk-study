import httpx
import pytest
import respx
from bs4 import BeautifulSoup

API = "http://api.test/api/v1/titles"


def flat(number):
    return {
        "titleNumber": f"TGL1000{number:02d}",
        "tenure": "LEASEHOLD",
        "address": {
            "line1": f"Flat {number}, Riverside Court",
            "line2": "2 Wharf Lane",
            "town": "London",
            "postcode": "SE1 7PB",
        },
    }


def api_page(numbers, total=25, previous_cursor=None, next_cursor=None):
    return httpx.Response(
        200,
        json={
            "results": [flat(n) for n in numbers],
            "total": total,
            "previousCursor": previous_cursor,
            "nextCursor": next_cursor,
        },
    )


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


@respx.mock
def test_lists_each_title_with_a_link_to_its_detail(client):
    respx.get(API).mock(return_value=api_page([1, 2]))

    response = client.get("/search/results?postcode=SE17PB")
    assert response.status_code == 200

    soup = page(response)
    assert "Properties in SE1 7PB" in soup.find("h1").get_text()
    link = soup.select_one("a[href='/search/titles/TGL100001']")
    assert link is not None
    assert "Flat 1, Riverside Court" in link.get_text()
    assert "Leasehold" in soup.get_text()


@respx.mock
@pytest.mark.parametrize("total, text", [(25, "25 properties"), (1, "1 property")])
def test_shows_how_many_properties_the_postcode_has(client, total, text):
    respx.get(API).mock(return_value=api_page([1], total=total))

    assert text in page(client.get("/search/results?postcode=SE17PB")).get_text()


@respx.mock
def test_shows_a_next_link_when_there_are_more_results(client):
    respx.get(API).mock(return_value=api_page([1, 2], next_cursor="QTpUR0wxMDAwMDI"))

    soup = page(client.get("/search/results?postcode=SE17PB"))

    next_link = soup.select_one(".govuk-pagination__next a")
    assert next_link is not None
    assert next_link["href"] == "/search/results?postcode=SE17PB&cursor=QTpUR0wxMDAwMDI"


@respx.mock
def test_has_no_next_link_on_the_last_page(client):
    respx.get(API).mock(return_value=api_page([21, 22], previous_cursor="QjpUR0wxMDAwMjE"))

    soup = page(client.get("/search/results?postcode=SE17PB&cursor=QTpUR0wxMDAwMjA"))

    assert soup.select_one(".govuk-pagination__next") is None


@respx.mock
def test_shows_a_previous_link_after_the_first_page(client):
    respx.get(API).mock(return_value=api_page([21, 22], previous_cursor="QjpUR0wxMDAwMjE"))

    soup = page(client.get("/search/results?postcode=SE17PB&cursor=QTpUR0wxMDAwMjA"))

    previous_link = soup.select_one(".govuk-pagination__prev a")
    assert previous_link is not None
    assert previous_link["href"] == "/search/results?postcode=SE17PB&cursor=QjpUR0wxMDAwMjE"


@respx.mock
def test_has_no_previous_link_on_the_first_page(client):
    respx.get(API).mock(return_value=api_page([1, 2], next_cursor="QTpUR0wxMDAwMDI"))

    soup = page(client.get("/search/results?postcode=SE17PB"))

    assert soup.select_one(".govuk-pagination__prev") is None


@respx.mock
def test_passes_the_cursor_to_the_api(client):
    route = respx.get(API).mock(return_value=api_page([21]))

    client.get("/search/results?postcode=SE17PB&cursor=QTpUR0wxMDAwMjA")

    assert route.calls.last.request.url.params["cursor"] == "QTpUR0wxMDAwMjA"


@respx.mock
def test_a_postcode_with_no_titles_shows_no_results(client):
    respx.get(API).mock(return_value=api_page([], total=0))

    response = client.get("/search/results?postcode=ZZ99ZZ")

    # An empty search is an answer, not an error: 200, unlike an unknown title number.
    assert response.status_code == 200
    soup = page(response)
    assert "No results for ZZ9 9ZZ" in soup.find("h1").get_text()
    assert soup.select_one("a[href='/search/postcode']") is not None


@respx.mock
@pytest.mark.parametrize("query", ["?postcode=12345", "", "?postcode="])
def test_an_invalid_or_missing_postcode_goes_back_to_the_search(client, query):
    route = respx.get(API).mock(return_value=api_page([]))

    response = client.get(f"/search/results{query}")

    assert response.status_code == 302
    assert response.headers["Location"] == "/search/postcode"
    assert not route.called


@respx.mock
def test_a_rejected_cursor_restarts_from_the_first_page(client):
    respx.get(API).mock(
        return_value=httpx.Response(
            400,
            json={
                "type": "https://land-registry.study/problems/validation-failed",
                "errors": {"cursor": "cursor is not valid; start again from the first page"},
            },
            headers={"content-type": "application/problem+json"},
        )
    )

    response = client.get("/search/results?postcode=SE17PB&cursor=tampered")

    assert response.status_code == 302
    assert response.headers["Location"] == "/search/results?postcode=SE17PB"


@respx.mock
def test_api_down_returns_503(client):
    respx.get(API).mock(side_effect=httpx.ConnectError("refused"))

    assert client.get("/search/results?postcode=SE17PB").status_code == 503
