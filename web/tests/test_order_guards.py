import pytest

ORDER_PAGES = ["/order/document-type", "/order/your-details", "/order/check-answers"]


@pytest.mark.parametrize("path", ORDER_PAGES)
def test_entering_mid_flow_without_a_session_goes_back_to_the_start(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_your_details_needs_a_document_type(client):
    client.get("/order/start/SGL123456")  # only the title in the session

    response = client.get("/order/your-details")

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/document-type"


def test_check_answers_needs_the_applicant_details(client):
    client.get("/order/start/SGL123456")
    client.post("/order/document-type", data={"document_type": "TITLE_REGISTER"})

    response = client.get("/order/check-answers")

    assert response.status_code == 302
    assert response.headers["Location"] == "/order/your-details"


@pytest.mark.parametrize("path", ORDER_PAGES)
def test_a_post_without_a_session_is_blocked_too(client, path):
    """A direct POST, skipping the pages, must not get past the guard."""
    response = client.post(path, data={})

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
