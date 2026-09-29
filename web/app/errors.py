"""GOV.UK error pages for the whole app."""

from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    # Only reached when the exception is not propagated (never in debug or
    # TESTING mode): the page says something went wrong and nothing else, so no
    # detail of the failure leaks to the user.
    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500
