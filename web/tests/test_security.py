import re

import pytest
from bs4 import BeautifulSoup

from app import create_app
from app.config import DEV_ONLY_SECRET_KEY


def test_every_response_has_the_security_headers(client):
    headers = client.get("/").headers

    assert headers["X-Content-Type-Options"] == "nosniff"
    # The payment page is one button: framing it on another site would let that
    # site trick people into clicking it (clickjacking).
    assert headers["X-Frame-Options"] == "DENY"
    # Order references sit in URLs; never send them to other sites.
    assert headers["Referrer-Policy"] == "same-origin"


def test_the_content_security_policy_only_allows_scripts_with_this_responses_nonce(client):
    response = client.get("/")
    policy = response.headers["Content-Security-Policy"]
    nonce = re.search(r"'nonce-([^']+)'", policy).group(1)

    assert "frame-ancestors 'none'" in policy
    scripts = BeautifulSoup(response.get_data(as_text=True), "html.parser").select("script")
    assert scripts, "the page has no scripts to check"
    for script in scripts:
        assert script.get("nonce") == nonce


def test_the_nonce_changes_on_every_response(client):
    first = client.get("/").headers["Content-Security-Policy"]
    second = client.get("/").headers["Content-Security-Policy"]

    assert first != second


def test_the_session_cookie_is_http_only_and_same_site(client):
    response = client.get("/order/start/SGL123456")
    cookie = response.headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_refuses_to_start_without_a_real_secret_key():
    # Signing sessions with a key that sits in the source code would let anyone
    # forge a session, including the list of orders "placed in this browser".
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"TESTING": False, "DEBUG": False, "SECRET_KEY": DEV_ONLY_SECRET_KEY})


def test_starts_with_a_real_secret_key():
    app = create_app({"TESTING": False, "DEBUG": False, "SECRET_KEY": "a-real-secret"})

    assert app.config["SECRET_KEY"] == "a-real-secret"
