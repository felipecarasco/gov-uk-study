import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-nao-usar-em-producao")
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
    API_TIMEOUT_SECONDS = float(os.environ.get("API_TIMEOUT_SECONDS", "5.0"))

    # Nome do serviço, usado no header do GOV.UK.
    SERVICE_NAME = "Search the land register"
