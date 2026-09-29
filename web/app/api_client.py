"""The only way out to the land register API.

Nothing else in the front end should know there is a remote service. Blueprints
and templates receive plain dictionaries and know nothing about httpx or HTTP
status codes.
"""

import httpx
from flask import current_app

# RFC 9457 "type" values the API returns. They are stable identifiers, which is
# why errors are told apart by type and not by status: a 404 from POST /orders
# means "unknown title", a 404 from GET /orders/{ref} means "unknown order".
_PROBLEMS = "https://land-registry.study/problems/"
_TITLE_NOT_FOUND = _PROBLEMS + "title-not-found"
_ORDER_NOT_FOUND = _PROBLEMS + "order-not-found"
_VALIDATION_FAILED = _PROBLEMS + "validation-failed"


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

    def _send(self, method, path, **kwargs):
        url = f"{self._base_url}{path}"
        try:
            return httpx.request(
                method,
                url,
                timeout=self._timeout,
                headers={"Accept": "application/json"},
                **kwargs,
            )
        except httpx.RequestError as error:
            raise ApiError(f"Could not reach the API: {error}") from error

    def _json_or_raise(self, response):
        if response.status_code >= 400:
            raise _error_from(response)
        try:
            return response.json()
        except ValueError as error:
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

    return ApiError(f"The API answered {response.status_code} for {response.request.url}")


def get_api_client():
    """Build the client from the current application's configuration."""
    return LandRegistryApiClient(
        current_app.config["API_BASE_URL"],
        timeout=current_app.config["API_TIMEOUT_SECONDS"],
    )
