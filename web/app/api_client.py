"""Única porta de saída para a API do registro de imóveis.

Nada mais no front-end deve saber que existe um serviço remoto. Blueprints e
templates recebem dicionários simples e não conhecem httpx nem códigos HTTP.
"""

import httpx
from flask import current_app


class ApiError(Exception):
    """A API não respondeu, ou respondeu com um erro que não sabemos tratar."""


class TitleNotFound(ApiError):
    """A API respondeu 404 para um número de título."""

    def __init__(self, title_number):
        super().__init__(f"Nenhum título com o número {title_number}")
        self.title_number = title_number


class LandRegistryApiClient:
    def __init__(self, base_url, timeout=5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def get_title(self, title_number):
        """Busca um título pelo número. Levanta TitleNotFound ou ApiError."""
        numero = (title_number or "").strip().upper()
        url = f"{self._base_url}/api/v1/titles/{numero}"

        try:
            resposta = httpx.get(url, timeout=self._timeout, headers={"Accept": "application/json"})
        except httpx.RequestError as erro:
            raise ApiError(f"Não foi possível contatar a API: {erro}") from erro

        if resposta.status_code == 404:
            raise TitleNotFound(numero)

        if resposta.status_code >= 400:
            raise ApiError(f"A API respondeu {resposta.status_code} para {url}")

        try:
            return resposta.json()
        except ValueError as erro:
            raise ApiError("A API devolveu um corpo que não é JSON") from erro


def get_api_client():
    """Constrói o cliente a partir da configuração da aplicação corrente."""
    return LandRegistryApiClient(
        current_app.config["API_BASE_URL"],
        timeout=current_app.config["API_TIMEOUT_SECONDS"],
    )
