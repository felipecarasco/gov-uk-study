import httpx
import respx
from bs4 import BeautifulSoup

BASE = "http://api.test"

TITULO = {
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

SEM_ONUS = {
    "titleNumber": "SGL123458",
    "tenure": "FREEHOLD",
    "classOfTitle": "Possessory title",
    "address": {"line1": "3 Bramber Lane", "town": "Croydon", "postcode": "CR0 3RD"},
    "proprietors": [{"name": "SAM OKONKWO", "address": "3 Bramber Lane"}],
    "charges": [],
}


@respx.mock
def test_detalhe_mostra_os_dados_do_titulo(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(
        return_value=httpx.Response(200, json=TITULO)
    )

    resposta = client.get("/search/titles/SGL123457")
    assert resposta.status_code == 200

    sopa = BeautifulSoup(resposta.get_data(as_text=True), "html.parser")
    texto = sopa.get_text()

    assert "SGL123457" in sopa.find("h1").get_text()
    assert "Leasehold" in texto
    assert "Flat 4, Hazelmere Court" in texto
    assert "CR0 2QQ" in texto
    assert sopa.select(".govuk-summary-list"), "esperava summary lists do GDS"


@respx.mock
def test_detalhe_formata_valores_em_libras(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(
        return_value=httpx.Response(200, json=TITULO)
    )

    texto = BeautifulSoup(
        client.get("/search/titles/SGL123457").get_data(as_text=True), "html.parser"
    ).get_text()

    # 28750000 pence = £287,500.00
    assert "£287,500.00" in texto
    assert "£230,000.00" in texto


@respx.mock
def test_detalhe_lista_todos_os_proprietarios_e_onus(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(
        return_value=httpx.Response(200, json=TITULO)
    )

    texto = BeautifulSoup(
        client.get("/search/titles/SGL123457").get_data(as_text=True), "html.parser"
    ).get_text()

    assert "JAMIE PATEL" in texto
    assert "ROWAN PATEL" in texto
    assert "CALDER BANK PLC" in texto
    assert "MERIDIAN LENDING LTD" in texto


@respx.mock
def test_detalhe_sem_onus_mostra_mensagem_e_nao_quebra(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123458").mock(
        return_value=httpx.Response(200, json=SEM_ONUS)
    )

    resposta = client.get("/search/titles/SGL123458")
    assert resposta.status_code == 200

    texto = BeautifulSoup(resposta.get_data(as_text=True), "html.parser").get_text()
    assert "No charges are registered" in texto
    assert "Price paid" not in texto  # o seed não tem preço para este título


@respx.mock
def test_titulo_inexistente_mostra_pagina_de_nao_encontrado(client):
    respx.get(f"{BASE}/api/v1/titles/ZZ000000").mock(
        return_value=httpx.Response(404, json={"status": 404, "title": "Title not found"})
    )

    resposta = client.get("/search/titles/ZZ000000")
    assert resposta.status_code == 404

    sopa = BeautifulSoup(resposta.get_data(as_text=True), "html.parser")
    assert "No results" in sopa.find("h1").get_text()
    assert "ZZ000000" in sopa.get_text()
    # A página de "nenhum resultado" do GDS precisa oferecer um caminho de volta.
    assert sopa.select_one("a[href='/search/title-number']") is not None


@respx.mock
def test_api_fora_do_ar_devolve_503(client):
    respx.get(f"{BASE}/api/v1/titles/SGL123457").mock(
        side_effect=httpx.ConnectError("recusado")
    )

    assert client.get("/search/titles/SGL123457").status_code == 503
