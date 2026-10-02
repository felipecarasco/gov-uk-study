"""The only way out to the land register API.

Nothing else in the front end should know there is a remote service. Blueprints
and templates receive plain dictionaries and know nothing about httpx or HTTP
status codes.
"""

import logging
from dataclasses import dataclass

import httpx
from flask import current_app
from werkzeug.http import parse_options_header

from app.logs import REQUEST_ID_HEADER, current_request_id

log = logging.getLogger(__name__)

# RFC 9457 "type" values the API returns. They are stable identifiers, which is
# why errors are told apart by type and not by status: a 404 from POST /orders
# means "unknown title", a 404 from GET /orders/{ref} means "unknown order".
_PROBLEMS = "https://land-registry.study/problems/"
_TITLE_NOT_FOUND = _PROBLEMS + "title-not-found"
_ORDER_NOT_FOUND = _PROBLEMS + "order-not-found"
_VALIDATION_FAILED = _PROBLEMS + "validation-failed"
_ORDER_NOT_PAID = _PROBLEMS + "order-not-paid"


class ApiError(Exception):
    """The API did not answer, or answered with an error we cannot handle."""


class TitleNotFound(ApiError):
    """No title exists with the given number."""

    def __init__(self, title_number):
        super().__init__(f"No title with the number {title_number}")
        self.title_number = title_number


class OrderNotFound(ApiError):
    """No order exists with the given reference."""

    def __init__(self, reference):
        super().__init__(f"No order with the reference {reference}")
        self.reference = reference


class ValidationFailed(ApiError):
    """The API rejected the request body. `errors` maps each field to a message."""

    def __init__(self, errors):
        super().__init__(f"The API rejected the fields {sorted(errors)}")
        self.errors = errors


class OrderNotPaid(ApiError):
    """The order's document was asked for before the order was paid."""

    def __init__(self, reference):
        super().__init__(f"Order {reference} has not been paid")
        self.reference = reference


@dataclass(frozen=True)
class OrderDocument:
    content: bytes
    filename: str


class LandRegistryApiClient:
    def __init__(self, base_url, timeout=5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def get_title(self, title_number):
        """Fetch a title by number. Raises TitleNotFound or ApiError."""
        number = (title_number or "").strip().upper()
        response = self._send("GET", f"/api/v1/titles/{number}")

        # Only one resource can be missing here, so a bare 404 is enough.
        if response.status_code == 404:
            raise TitleNotFound(number)

        return self._json_or_raise(response)

    def search_titles(self, postcode, cursor=None):
        """One page of titles in a postcode.

        Returns {"results": [...], "total": int, "previousCursor": str | None,
        "nextCursor": str | None}. Raises ValidationFailed when the API rejects
        the postcode or the cursor, or ApiError.
        """
        params = {"postcode": postcode}
        if cursor:
            params["cursor"] = cursor
        return self._json_or_raise(self._send("GET", "/api/v1/titles", params=params))

    def create_order(
        self, title_number, document_type, applicant_name, applicant_email, applicant_address
    ):
        """Create an order. Raises TitleNotFound, ValidationFailed or ApiError."""
        # Explicit mapping on purpose: this dictionary *is* the contract with the
        # Java side, and a generic snake_case to camelCase converter would hide it.
        body = {
            "titleNumber": title_number,
            "documentType": document_type,
            "applicantName": applicant_name,
            "applicantEmail": applicant_email,
            "applicantAddress": applicant_address,
        }
        return self._json_or_raise(self._send("POST", "/api/v1/orders", json=body))

    def get_order(self, reference):
        """Fetch an order by reference. Raises OrderNotFound or ApiError."""
        return self._json_or_raise(self._send("GET", f"/api/v1/orders/{reference}"))

    def pay_order(self, reference):
        """Pay for an order; paying twice is harmless. Raises OrderNotFound or ApiError."""
        return self._json_or_raise(self._send("POST", f"/api/v1/orders/{reference}/payment"))

    def get_order_document(self, reference):
        """The order's copy as a PDF. Raises OrderNotPaid, OrderNotFound or ApiError."""
        response = self._send(
            "GET",
            f"/api/v1/orders/{reference}/document",
            # The PDF when it works, Problem Details when it does not.
            accept="application/pdf, application/problem+json",
        )
        if response.status_code >= 400:
            raise _error_from(response)

        _, options = parse_options_header(response.headers.get("content-disposition", ""))
        return OrderDocument(response.content, options.get("filename") or f"{reference}.pdf")

    def _send(self, method, path, accept="application/json", **kwargs):
        url = f"{self._base_url}{path}"
        headers = {"Accept": accept}
        request_id = current_request_id()
        if request_id != "-":
            # The API logs under the same id, so one search finds both sides.
            headers[REQUEST_ID_HEADER] = request_id
        try:
            return httpx.request(method, url, timeout=self._timeout, headers=headers, **kwargs)
        except httpx.RequestError as error:
            # Until now the page showed "service unavailable" and nothing was
            # recorded anywhere: this says which call failed and why.
            log.warning("API unreachable: %s %s failed with %s", method, url, type(error).__name__)
            raise ApiError(f"Could not reach the API: {error}") from error

    def _json_or_raise(self, response):
        if response.status_code >= 400:
            raise _error_from(response)
        try:
            return response.json()
        except ValueError as error:
            log.error("API returned a body that is not JSON for %s", response.request.url)
            raise ApiError("The API returned a body that is not JSON") from error


def _error_from(response):
    """Turn an error response into the most specific exception its type allows."""
    try:
        problem = response.json()
    except ValueError:
        problem = None
    if not isinstance(problem, dict):
        problem = {}

    problem_type = problem.get("type")
    if problem_type == _TITLE_NOT_FOUND:
        return TitleNotFound(problem.get("titleNumber"))
    if problem_type == _ORDER_NOT_FOUND:
        return OrderNotFound(problem.get("reference"))
    if problem_type == _VALIDATION_FAILED:
        return ValidationFailed(problem.get("errors") or {})
    if problem_type == _ORDER_NOT_PAID:
        return OrderNotPaid(problem.get("reference"))

    # Expected problems (unknown title, validation, unpaid order) were turned
    # into their own exceptions above and are not logged: they are answers, not
    # faults. Anything reaching this line is.
    log.error(
        "Unexpected API response %s for %s %s",
        response.status_code,
        response.request.method,
        response.request.url,
    )
    return ApiError(f"The API answered {response.status_code} for {response.request.url}")


def get_api_client():
    """Build the client from the current application's configuration."""
    return LandRegistryApiClient(
        current_app.config["API_BASE_URL"],
        timeout=current_app.config["API_TIMEOUT_SECONDS"],
    )
