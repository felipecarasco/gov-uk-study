from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
import respx
from bs4 import BeautifulSoup

TITLE = {
    "titleNumber": "TGL100007",
    "tenure": "LEASEHOLD",
    "classOfTitle": "Title absolute",
    "address": {"line1": "Flat 7, Riverside Court", "town": "London", "postcode": "SE1 7PB"},
    "proprietors": [],
    "charges": [],
}

RESULTS = {
    "results": [
        {
            "titleNumber": "TGL100007",
            "tenure": "LEASEHOLD",
            "address": {
                "line1": "Flat 7, Riverside Court",
                "town": "London",
                "postcode": "SE1 7PB",
            },
        }
    ],
    "total": 25,
    "previousCursor": None,
    "nextCursor": None,
}


def page(response):
    return BeautifulSoup(response.get_data(as_text=True), "html.parser")


def back_link(client, query):
    with respx.mock:
        respx.get("http://api.test/api/v1/titles/TGL100007").mock(
            return_value=httpx.Response(200, json=TITLE)
        )
        return page(client.get(f"/search/titles/TGL100007{query}")).select_one("a.govuk-back-link")[
            "href"
        ]


@respx.mock
def test_results_link_to_each_detail_with_the_way_back(client):
    respx.get("http://api.test/api/v1/titles").mock(return_value=httpx.Response(200, json=RESULTS))

    link = page(client.get("/search/results?postcode=SE17PB&cursor=QTpUR0wxMDAwMDY")).select_one(
        "tbody a.govuk-link"
    )["href"]

    parts = urlsplit(link)
    assert parts.path == "/search/titles/TGL100007"
    assert parse_qs(parts.query)["back"] == [
        "/search/results?postcode=SE17PB&cursor=QTpUR0wxMDAwMDY"
    ]


def test_the_detail_goes_back_to_those_results(client):
    href = back_link(client, "?back=%2Fsearch%2Fresults%3Fpostcode%3DSE17PB")

    assert href == "/search/results?postcode=SE17PB"


def test_without_a_way_back_the_detail_goes_back_to_the_search(client):
    assert back_link(client, "") == "/search/title-number"


# Anything that is not this site's results page could send the user elsewhere:
# an open redirect that a phishing link could use to look trustworthy.
@pytest.mark.parametrize(
    "unsafe",
    [
        "https%3A%2F%2Fevil.example%2Fsearch%2Fresults",
        "%2F%2Fevil.example%2Fsearch%2Fresults",
        "javascript%3Aalert(1)",
        "%2Forder%2Fcheck-answers",
    ],
)
def test_an_unsafe_way_back_is_ignored(client, unsafe):
    assert back_link(client, f"?back={unsafe}") == "/search/title-number"
