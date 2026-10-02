import logging

import httpx
import respx

API = "http://api.test/api/v1"

TITLE = {
    "titleNumber": "SGL123456",
    "tenure": "FREEHOLD",
    "classOfTitle": "Title absolute",
    "address": {"line1": "12 Mallow Gardens", "town": "Croydon", "postcode": "CR0 2QQ"},
    "proprietors": [],
    "charges": [],
}

CREATED = {
    "reference": "LR-AAAA2222",
    "titleNumber": "SGL123456",
    "documentType": "TITLE_REGISTER",
    "status": "PENDING_PAYMENT",
    "amountPence": 300,
    "createdAt": "2026-09-10T12:00:00Z",
    "paidAt": None,
}


def warnings_and_errors(caplog):
    return [r for r in caplog.records if r.levelno >= logging.WARNING]


@respx.mock
def test_calls_to_the_api_carry_the_pages_request_id(client):
    route = respx.get(f"{API}/titles/SGL123456").mock(return_value=httpx.Response(200, json=TITLE))

    response = client.get("/search/titles/SGL123456", headers={"X-Request-ID": "page-77"})

    assert route.calls.last.request.headers["X-Request-ID"] == "page-77"
    assert response.headers["X-Request-ID"] == "page-77"


@respx.mock
def test_an_unreachable_api_is_logged_with_the_cause_and_the_id(client, caplog):
    respx.get(f"{API}/titles/SGL123456").mock(side_effect=httpx.ConnectError("refused"))

    with caplog.at_level(logging.INFO, logger="app"):
        response = client.get("/search/titles/SGL123456", headers={"X-Request-ID": "page-down"})

    assert response.status_code == 503
    [record] = warnings_and_errors(caplog)
    assert record.levelno == logging.WARNING
    assert "ConnectError" in record.getMessage()
    assert record.request_id == "page-down"


@respx.mock
def test_an_unexpected_api_response_is_logged_as_an_error(client, caplog):
    respx.get(f"{API}/titles/SGL123456").mock(return_value=httpx.Response(500, text="boom"))

    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/search/titles/SGL123456")

    [record] = warnings_and_errors(caplog)
    assert record.levelno == logging.ERROR
    assert "500" in record.getMessage()


@respx.mock
def test_an_unknown_title_is_not_logged_as_a_problem(client, caplog):
    respx.get(f"{API}/titles/ZZ000000").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://land-registry.study/problems/title-not-found",
                "titleNumber": "ZZ000000",
            },
            headers={"content-type": "application/problem+json"},
        )
    )

    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/search/titles/ZZ000000")

    assert warnings_and_errors(caplog) == []


@respx.mock
def test_a_rejected_order_is_not_logged_as_a_problem(client, caplog):
    # Goes through the client's generic error mapping, unlike the unknown title
    # above, which get_title handles on its own.
    with client.session_transaction() as session:
        session["order"] = {
            "title_number": "SGL123456",
            "document_type": "TITLE_REGISTER",
            "applicant_name": "Sam Okonkwo",
            "applicant_email": "sam@example.com",
            "applicant_address": "3 Bramber Lane",
        }
    respx.post(f"{API}/orders").mock(
        return_value=httpx.Response(
            400,
            json={
                "type": "https://land-registry.study/problems/validation-failed",
                "errors": {"applicantEmail": "Enter an email address in the correct format"},
            },
            headers={"content-type": "application/problem+json"},
        )
    )

    with caplog.at_level(logging.INFO, logger="app"):
        response = client.post("/order/check-answers", data={})

    assert response.status_code == 200
    assert warnings_and_errors(caplog) == []


def test_asking_for_another_browsers_order_is_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        response = client.get("/order/payment/LR-AAAA2222")

    assert response.status_code == 404
    [record] = warnings_and_errors(caplog)
    assert "LR-AAAA2222" in record.getMessage()


@respx.mock
def test_the_applicants_details_never_reach_the_log(client, caplog):
    respx.post(f"{API}/orders").mock(return_value=httpx.Response(201, json=CREATED))

    with caplog.at_level(logging.DEBUG):
        client.get("/order/start/SGL123456")
        client.post("/order/document-type", data={"document_type": "TITLE_REGISTER"})
        client.post(
            "/order/your-details",
            data={
                "applicant_name": "Alex Morgan Holloway",
                "applicant_email": "alex@example.com",
                "applicant_address": "12 Mallow Gardens, Croydon, CR0 2QQ",
            },
        )
        client.post("/order/check-answers", data={})

    assert "Alex Morgan Holloway" not in caplog.text
    assert "alex@example.com" not in caplog.text
    assert "12 Mallow Gardens" not in caplog.text
