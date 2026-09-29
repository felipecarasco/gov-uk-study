import httpx
import respx
from bs4 import BeautifulSoup

BASE = "http://api.test"

TITLE = {
    "titleNumber": "SGL123457",
    "tenure": "LEASEHOLD",
    "classOfTitle": "Title absolute",
    "address": {
        "line1": "Flat 4, Hazelmere Court",
        "line2": "18 Mallow Gardens",
        "town": "Croydon",
        "postcode": "CR0 2QQ",
    },
    "pricePaidPence": 28750000,
    "pricePaidDate": "2021-11-02",
    "proprietors": [
        {"name": "JAMIE PATEL", "address": "Flat 4, Hazelmere Court"},
        {"name": "ROWAN PATEL", "address": "Flat 4, Hazelmere Court"},
    ],
    "charges": [
        {"lender": "CALDER BANK PLC", "chargeDate": "2021-11-02", "amountPence": 23000000},
        {"lender": "MERIDIAN LENDING LTD", "chargeDate": "2024-01-17", "amountPence": 4500000},
    ],
}

NO_CHARGES = {
    "titleNumber": "SGL123458",
    "tenure": "FREEHOLD",
    "classOfTitle": "Possessory title",
    "address": {"line1": "3 Bramber Lane", "town": "Croydon", "postcode": "CR0 3RD"},
    "proprietors": [{"name": "SAM OKONKWO", "address": "3 Bramber Lane"}],
    "charges": [],
}


@respx.mock
def test_detail_shows_the_title_data(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(return_value=httpx.Response(200, json=TITLE))

    response = client.get("/search/titles/SGL123457")
    assert response.status_code == 200

    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    text = soup.get_text()

    assert "SGL123457" in soup.find("h1").get_text()
    assert "Leasehold" in text
    assert "Flat 4, Hazelmere Court" in text
    assert "CR0 2QQ" in text
    assert soup.select(".govuk-summary-list"), "expected GOV.UK summary lists"


@respx.mock
def test_detail_formats_amounts_in_pounds(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(return_value=httpx.Response(200, json=TITLE))

    text = BeautifulSoup(
        client.get("/search/titles/SGL123457").get_data(as_text=True), "html.parser"
    ).get_text()

    # 28750000 pence = £287,500.00
    assert "£287,500.00" in text
    assert "£230,000.00" in text


@respx.mock
def test_detail_lists_every_proprietor_and_charge(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(return_value=httpx.Response(200, json=TITLE))

    text = BeautifulSoup(
        client.get("/search/titles/SGL123457").get_data(as_text=True), "html.parser"
    ).get_text()

    assert "JAMIE PATEL" in text
    assert "ROWAN PATEL" in text
    assert "CALDER BANK PLC" in text
    assert "MERIDIAN LENDING LTD" in text


@respx.mock
def test_detail_without_charges_shows_a_message(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123458").mock(
        return_value=httpx.Response(200, json=NO_CHARGES)
    )

    response = client.get("/search/titles/SGL123458")
    assert response.status_code == 200

    text = BeautifulSoup(response.get_data(as_text=True), "html.parser").get_text()
    assert "No charges are registered" in text
    assert "Price paid" not in text  # the seed has no price for this title


@respx.mock
def test_unknown_title_shows_the_not_found_page(client):
    respx.get(f"{BASE}/api/v1/titles/ZZ000000").mock(
        return_value=httpx.Response(404, json={"status": 404, "title": "Title not found"})
    )

    response = client.get("/search/titles/ZZ000000")
    assert response.status_code == 404

    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    assert "No results" in soup.find("h1").get_text()
    assert "ZZ000000" in soup.get_text()
    # A GOV.UK "no results" page must offer a way back.
    assert soup.select_one("a[href='/search/title-number']") is not None


@respx.mock
def test_api_down_returns_503(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(side_effect=httpx.ConnectError("refused"))

    assert client.get("/search/titles/SGL123457").status_code == 503


@respx.mock
def test_dates_follow_the_govuk_style(client):
    """The GOV.UK style guide requires '2 November 2021', not '2021-11-02'.
    See https://www.gov.uk/guidance/style-guide/a-to-z#dates."""
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(return_value=httpx.Response(200, json=TITLE))

    text = BeautifulSoup(
        client.get("/search/titles/SGL123457").get_data(as_text=True), "html.parser"
    ).get_text()

    assert "2 November 2021" in text
    assert "17 January 2024" in text
    assert "2021-11-02" not in text
