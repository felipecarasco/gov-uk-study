from bs4 import BeautifulSoup


def test_pagina_inicial_responde_200(client):
    assert client.get("/").status_code == 200


def test_pagina_inicial_tem_titulo_e_botao_de_inicio(client):
    html = client.get("/").get_data(as_text=True)
    sopa = BeautifulSoup(html, "html.parser")

    assert "Search the land register" in sopa.title.string

    h1 = sopa.find("h1")
    assert h1 is not None
    assert "Search the land register" in h1.get_text()

    botao = sopa.select_one("a.govuk-button--start")
    assert botao is not None, "falta o botão verde do padrão start page"
    assert botao.get_text(strip=True).startswith("Start now")
    assert botao["href"] == "/search/title-number"


def test_pagina_inicial_carrega_o_css_do_govuk(client):
    html = client.get("/").get_data(as_text=True)
    assert "govuk-frontend.min.css" in html
    assert 'class="govuk-template' in html


def test_pagina_inicial_tem_skip_link(client):
    # Requisito de acessibilidade do GDS: primeiro elemento focável da página.
    sopa = BeautifulSoup(client.get("/").get_data(as_text=True), "html.parser")
    skip = sopa.select_one("a.govuk-skip-link")
    assert skip is not None
    assert skip["href"] == "#main-content"
