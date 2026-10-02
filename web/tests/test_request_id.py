import json
import logging
import re

import pytest

from app import create_app

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def test_every_response_has_a_request_id(client):
    assert UUID.match(client.get("/").headers["X-Request-ID"])


def test_a_valid_incoming_id_is_reused(client):
    response = client.get("/", headers={"X-Request-ID": "proxy-71ac"})

    assert response.headers["X-Request-ID"] == "proxy-71ac"


@pytest.mark.parametrize("unsafe", ["has spaces", "x" * 65])
def test_an_unsafe_incoming_id_is_replaced(client, unsafe):
    response = client.get("/", headers={"X-Request-ID": unsafe})

    assert UUID.match(response.headers["X-Request-ID"])


def test_records_logged_during_a_request_carry_its_id(caplog):
    app = create_app({"TESTING": True, "SECRET_KEY": "test", "API_BASE_URL": "http://api.test"})

    @app.get("/logs-something")
    def logs_something():
        logging.getLogger("app.example").info("hello")
        return "ok"

    with caplog.at_level(logging.INFO, logger="app"):
        response = app.test_client().get("/logs-something", headers={"X-Request-ID": "trace-9"})

    record = next(r for r in caplog.records if r.getMessage() == "hello")
    assert record.request_id == "trace-9" == response.headers["X-Request-ID"]


def test_outside_a_request_the_id_is_a_dash(caplog):
    # Creating an app is what installs the request id on log records; without it
    # this test would depend on another test having created one first.
    create_app({"TESTING": True, "SECRET_KEY": "test", "API_BASE_URL": "http://api.test"})

    with caplog.at_level(logging.INFO, logger="app"):
        logging.getLogger("app.example").info("at start-up")

    assert caplog.records[-1].request_id == "-"


def test_the_json_formatter_writes_one_object_with_the_id_and_extra_fields():
    from app.logs import JsonFormatter

    record = logging.makeLogRecord(
        {
            "name": "app.order",
            "levelname": "INFO",
            "msg": "Order %s viewed",
            "args": ("LR-AAAA2222",),
        }
    )
    record.request_id = "trace-9"
    record.reference = "LR-AAAA2222"

    entry = json.loads(JsonFormatter().format(record))

    assert entry["message"] == "Order LR-AAAA2222 viewed"
    assert entry["log.level"] == "INFO"
    # Same field name as the API's JSON logs, so one search finds both services.
    assert entry["requestId"] == "trace-9"
    assert entry["reference"] == "LR-AAAA2222"
