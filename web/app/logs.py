"""Logging for the front end: a request id on every line, as text or JSON.

The id is created (or taken from a proxy's X-Request-ID) at the start of each
request, returned in the response header and sent to the API, which logs under
the same id. One id therefore follows a click through both services.
"""

import json
import logging
import re
import sys
import uuid
from datetime import datetime, timezone

from flask import g, has_request_context, request

REQUEST_ID_HEADER = "X-Request-ID"

# Written into every log line, so only short, plain values are accepted.
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

_TEXT_FORMAT = "%(asctime)s %(levelname)-5s [%(request_id)s] %(name)s : %(message)s"

# Attributes every LogRecord has; anything else was passed with extra=... and
# becomes a field of its own in the JSON output.
_STANDARD_ATTRIBUTES = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "request_id"}


def current_request_id():
    return g.get("request_id", "-") if has_request_context() else "-"


class JsonFormatter(logging.Formatter):
    """One JSON object per line, close to the API's Elastic Common Schema output."""

    def format(self, record):
        entry = {
            "@timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "log.level": record.levelname,
            "log.logger": record.name,
            "message": record.getMessage(),
            "requestId": getattr(record, "request_id", "-"),
        }
        entry.update({k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRIBUTES})
        if record.exc_info:
            entry["error.stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure_logging(app):
    _put_request_id_on_every_record()
    _add_app_handler(app.config["LOG_FORMAT"], app.config["LOG_LEVEL"])

    @app.before_request
    def assign_request_id():
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        g.request_id = incoming if _SAFE_ID.match(incoming) else str(uuid.uuid4())

    @app.after_request
    def return_request_id(response):
        response.headers[REQUEST_ID_HEADER] = current_request_id()
        return response


def _put_request_id_on_every_record():
    # A record factory, not a handler filter: it reaches every record, including
    # those collected by other handlers such as pytest's caplog.
    previous = logging.getLogRecordFactory()
    if getattr(previous, "adds_request_id", False):
        return

    def factory(*args, **kwargs):
        record = previous(*args, **kwargs)
        record.request_id = current_request_id()
        return record

    factory.adds_request_id = True
    logging.setLogRecordFactory(factory)


def _add_app_handler(log_format, level):
    # On the "app" logger, the parent of every module logger here and the logger
    # Flask itself uses for unhandled exceptions. Records still propagate to the
    # root logger, so nothing that listens there misses them.
    logger = logging.getLogger("app")
    logger.setLevel(level)
    if any(getattr(handler, "is_app_handler", False) for handler in logger.handlers):
        return  # create_app runs many times in the tests
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        JsonFormatter() if log_format == "json" else logging.Formatter(_TEXT_FORMAT)
    )
    handler.is_app_handler = True
    logger.addHandler(handler)
