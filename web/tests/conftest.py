import pytest

from app import create_app


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test",
            "API_BASE_URL": "http://api.test",
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
