"""Security headers and the per-response Content Security Policy nonce."""

import secrets

from flask import g

# Scripts run only if they carry this response's nonce: an injected <script>
# cannot guess it. Everything else may only come from this site.
_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}'; "
    "img-src 'self' data:; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "base-uri 'self'"
)


def init_security(app):
    @app.before_request
    def make_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    # The GOV.UK template adds nonce="{{ cspNonce }}" to its own inline script.
    @app.context_processor
    def expose_nonce():
        return {"cspNonce": g.get("csp_nonce", "")}

    @app.after_request
    def add_headers(response):
        response.headers["Content-Security-Policy"] = _POLICY.format(nonce=g.get("csp_nonce", ""))
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response
