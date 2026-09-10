def test_factory_cria_app_com_config_de_teste(app):
    assert app.testing is True
    assert app.config["API_BASE_URL"] == "http://api.test"


def test_jinja_enxerga_as_macros_do_govuk(app):
    # Se o ChoiceLoader estiver mal configurado, isto levanta TemplateNotFound.
    template = app.jinja_env.get_template("govuk_frontend_jinja/components/button/macro.html")
    assert template is not None


def test_pagina_inexistente_devolve_404(client):
    assert client.get("/nao-existe").status_code == 404
