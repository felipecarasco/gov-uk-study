def test_factory_builds_the_app_with_test_config(app):
    assert app.testing is True
    assert app.config["API_BASE_URL"] == "http://api.test"


def test_jinja_finds_the_govuk_macros(app):
    # If the ChoiceLoader is misconfigured, this raises TemplateNotFound.
    template = app.jinja_env.get_template("govuk_frontend_jinja/components/button/macro.html")
    assert template is not None


def test_unknown_page_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404
