import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-for-production")
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
    API_TIMEOUT_SECONDS = float(os.environ.get("API_TIMEOUT_SECONDS", "5.0"))

    # Service name, shown in the GOV.UK header.
    SERVICE_NAME = "Search the land register"
