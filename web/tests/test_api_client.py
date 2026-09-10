import httpx
import pytest
import respx

from app.api_client import ApiError, LandRegistryApiClient, TitleNotFound

BASE = "http://api.test"

TITULO = {
    "titleNumber": "SGL123456",
    "tenure": "FREEHOLD",
    "classOfTitle": "Title absolute",
    "address": {"line1": "12 Mallow Gardens", "town": "Croydon", "postcode": "CR0 2QQ"},
    "pricePaidPence": 42500000,
    "pricePaidDate": "2019-06-14",
    "proprietors": [{"name": "ALEX MORGAN HOLLOWAY", "address": "12 Mallow Gardens"}],
    "charges": [],
}

PROBLEM_404 = {
    "type": "https://land-registry.study/problems/title-not-found",
    "title": "Title not found",
    "status": 404,
    "detail": "No title exists with the number ZZ000000",
    "instance": "/api/v1/titles/ZZ000000",
    "titleNumber": "ZZ000000",
}


@pytest.fixture
def api():
    return LandRegistryApiClient(BASE, timeout=1.0)


@respx.mock
def test_get_title_devolve_o_json(api):
    respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(return_value=httpx.Response(200, json=TITULO))

    resultado = api.get_title("SGL123456")

    assert resultado["titleNumber"] == "SGL123456"
    assert resultado["address"]["postcode"] == "CR0 2QQ"


@respx.mock
def test_get_title_normaliza_para_maiusculas(api):
    rota = respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(
        return_value=httpx.Response(200, json=TITULO)
    )

    api.get_title("  sgl123456 ")

    assert rota.called


@respx.mock
def test_get_title_levanta_title_not_found_em_404(api):
    respx.get(f"{BASE}/api/v1/titles/ZZ000000").mock(
        return_value=httpx.Response(
            404, json=PROBLEM_404, headers={"content-type": "application/problem+json"}
        )
    )

    with pytest.raises(TitleNotFound) as exc:
        api.get_title("ZZ000000")

    assert exc.value.title_number == "ZZ000000"


@respx.mock
def test_get_title_levanta_api_error_em_500(api):
    respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(return_value=httpx.Response(500, text="boom"))

    with pytest.raises(ApiError):
        api.get_title("SGL123456")


@respx.mock
def test_get_title_levanta_api_error_quando_a_api_esta_fora(api):
    respx.get(f"{BASE}/api/v1/titles/SGL123456").mock(side_effect=httpx.ConnectError("recusado"))

    with pytest.raises(ApiError):
        api.get_title("SGL123456")


def test_title_not_found_e_subclasse_de_api_error():
    # Permite que as rotas tratem só ApiError quando o motivo não importa.
    assert issubclass(TitleNotFound, ApiError)
