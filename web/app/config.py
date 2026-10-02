import os

# Only good enough for running locally: create_app refuses it outside debug and tests.
DEV_ONLY_SECRET_KEY = "dev-only-not-for-production"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", DEV_ONLY_SECRET_KEY)
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
    API_TIMEOUT_SECONDS = float(os.environ.get("API_TIMEOUT_SECONDS", "5.0"))

    # Lax: the cookie is not sent on requests started by other sites, which is a
    # second line of defence behind the CSRF tokens.
    SESSION_COOKIE_SAMESITE = "Lax"
    # True wherever the service is reached over HTTPS, such as behind an
    # OpenShift route; False by default so that plain http://localhost works.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

    # "text" for development, "json" in containers (see web/Dockerfile).
    LOG_FORMAT = os.environ.get("LOG_FORMAT", "text")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Service name, shown in the GOV.UK header.
    SERVICE_NAME = "Search the land register"
