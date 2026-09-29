import pytest

from app import create_app


@pytest.fixture
def assets_client(tmp_path):
    (tmp_path / "fonts").mkdir()
    (tmp_path / "fonts" / "bold.woff2").write_bytes(b"font-bytes")
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test",
            "API_BASE_URL": "http://api.test",
            "GOVUK_ASSETS_DIR": str(tmp_path),
        }
    )
    return app.test_client()


def test_serves_the_govuk_assets_where_the_css_asks_for_them(assets_client):
    # govuk-frontend.min.css asks for /assets/fonts/... and /assets/images/...
    response = assets_client.get("/assets/fonts/bold.woff2")

    assert response.status_code == 200
    assert response.data == b"font-bytes"


def test_a_missing_asset_is_not_found(assets_client):
    assert assets_client.get("/assets/fonts/missing.woff2").status_code == 404


def test_cannot_reach_files_outside_the_assets_folder(assets_client):
    assert assets_client.get("/assets/..%2F..%2Fapp%2Fconfig.py").status_code == 404
