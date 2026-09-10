from bs4 import BeautifulSoup


def test_get_mostra_o_formulario(client):
    resposta = client.get("/search/title-number")
    assert resposta.status_code == 200

    sopa = BeautifulSoup(resposta.get_data(as_text=True), "html.parser")
    campo = sopa.select_one("input#title_number.govuk-input")
    assert campo is not None
    assert sopa.select_one("label[for='title_number']") is not None
    assert "SGL123456" in sopa.select_one("#title_number-hint").get_text()


def test_submissao_vazia_mostra_error_summary(client):
    resposta = client.post("/search/title-number", data={"title_number": ""})
    assert resposta.status_code == 200

    sopa = BeautifulSoup(resposta.get_data(as_text=True), "html.parser")

    resumo = sopa.select_one(".govuk-error-summary")
    assert resumo is not None, "falta o error summary no topo da página"
    assert "Enter a title number" in resumo.get_text()

    assert sopa.select_one("input#title_number.govuk-input--error") is not None
    assert sopa.select_one(".govuk-error-message") is not None


def test_titulo_da_pagina_comeca_com_error_quando_ha_erro(client):
    # Leitores de tela anunciam o <title> primeiro; o GDS exige o prefixo.
    resposta = client.post("/search/title-number", data={"title_number": ""})
    sopa = BeautifulSoup(resposta.get_data(as_text=True), "html.parser")
    assert sopa.title.string.startswith("Error: ")


def test_links_do_error_summary_apontam_para_campos_existentes(client):
    """O teste de destaque da spec: cada âncora do resumo precisa aterrissar
    num elemento que realmente existe na página."""
    resposta = client.post("/search/title-number", data={"title_number": ""})
    sopa = BeautifulSoup(resposta.get_data(as_text=True), "html.parser")

    links = sopa.select(".govuk-error-summary a[href^='#']")
    assert links, "o error summary não tem nenhum link âncora"

    for link in links:
        alvo = link["href"].removeprefix("#")
        assert (
            sopa.find(id=alvo) is not None
        ), f"o link do error summary aponta para #{alvo}, que não existe na página"


def test_formato_invalido_mostra_mensagem_especifica(client):
    resposta = client.post("/search/title-number", data={"title_number": "123"})
    sopa = BeautifulSoup(resposta.get_data(as_text=True), "html.parser")
    assert "correct format" in sopa.select_one(".govuk-error-summary").get_text()


def test_titulo_valido_redireciona_para_o_detalhe(client):
    # Não precisa de mock da API: a rota só valida e redireciona, sem chamar o backend.
    resposta = client.post("/search/title-number", data={"title_number": "sgl123456"})

    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/search/titles/SGL123456"
