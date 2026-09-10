from datetime import date

from flask import Flask
from govuk_frontend_wtf.main import WTFormsHelpers
from jinja2 import ChoiceLoader, PackageLoader, PrefixLoader

from app.config import Config


def create_app(config_overrides=None):
    app = Flask(__name__, static_folder="static")
    app.config.from_object(Config)

    if config_overrides:
        app.config.update(config_overrides)

    # As macros do GOV.UK vivem dentro dos pacotes instalados, não em app/templates.
    # O PrefixLoader mapeia o prefixo do caminho ("govuk_frontend_jinja/...") para
    # o pacote correspondente; o ChoiceLoader tenta primeiro os templates do app.
    app.jinja_loader = ChoiceLoader(
        [
            PackageLoader("app"),
            PrefixLoader(
                {
                    "govuk_frontend_jinja": PackageLoader("govuk_frontend_jinja"),
                    "govuk_frontend_wtf": PackageLoader("govuk_frontend_wtf"),
                }
            ),
        ]
    )

    # Registra o helper wtforms_errors(), usado pelo error summary nos templates.
    WTFormsHelpers(app)

    @app.template_filter("pounds")
    def format_pounds(pence):
        """Converte pence em libras formatadas. Aritmética inteira, sem float."""
        if pence is None:
            return ""
        libras, resto = divmod(int(pence), 100)
        return f"£{libras:,}.{resto:02d}"

    @app.template_filter("govuk_date")
    def format_govuk_date(iso_date):
        """Converte '2021-11-02' em '2 November 2021'.

        O guia de estilo do GOV.UK exige dia sem zero à esquerda, mês por extenso
        e ano com quatro dígitos. Ver style guide, verbete 'dates'.
        """
        if not iso_date:
            return ""
        d = date.fromisoformat(iso_date)
        return f"{d.day} {d.strftime('%B')} {d.year}"

    from app.blueprints import register_blueprints

    register_blueprints(app)

    return app
