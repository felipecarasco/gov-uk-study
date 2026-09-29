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

    # The GOV.UK macros live inside the installed packages, not in app/templates.
    # PrefixLoader maps the path prefix ("govuk_frontend_jinja/...") to the
    # matching package; ChoiceLoader tries the app's own templates first.
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

    # Registers the wtforms_errors() helper used by the error summary in templates.
    WTFormsHelpers(app)

    @app.template_filter("pounds")
    def format_pounds(pence):
        """Formats pence as pounds. Integer arithmetic, no float."""
        if pence is None:
            return ""
        pounds, remainder = divmod(int(pence), 100)
        return f"£{pounds:,}.{remainder:02d}"

    @app.template_filter("govuk_date")
    def format_govuk_date(iso_date):
        """Turns '2021-11-02' into '2 November 2021'.

        The GOV.UK style guide requires the day without a leading zero, the month
        in full and a four-digit year. See the style guide, entry 'dates'.
        """
        if not iso_date:
            return ""
        d = date.fromisoformat(iso_date)
        return f"{d.day} {d.strftime('%B')} {d.year}"

    from app.blueprints import register_blueprints

    register_blueprints(app)

    return app
