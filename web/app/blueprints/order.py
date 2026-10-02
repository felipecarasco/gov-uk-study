import functools
import logging

from flask import Blueprint, Response, abort, redirect, render_template, request, session, url_for

from app.api_client import ApiError, OrderNotFound, OrderNotPaid, ValidationFailed, get_api_client
from app.forms.order import (
    DOCUMENT_TYPE_LABELS,
    ConfirmOrderForm,
    DocumentTypeForm,
    PaymentForm,
    YourDetailsForm,
)

bp = Blueprint("order", __name__, url_prefix="/order")

log = logging.getLogger(__name__)

# Shown before the order exists. The API decides the real amount (OrderService),
# and the confirmation comes from what it returns; this only has to match it.
ORDER_PRICE_PENCE = 300

# Where each API field can be changed, so an error from the API links to the
# page that fixes it.
_CHANGE_PAGE = {
    "documentType": "order.document_type",
    "applicantName": "order.your_details",
    "applicantEmail": "order.your_details",
    "applicantAddress": "order.your_details",
}


# The page that fills in each session key, in flow order. A guard sends the
# user to the page for the first key that is missing.
_FILLED_IN_BY = {
    "title_number": "main.index",
    "document_type": "order.document_type",
    "applicant_name": "order.your_details",
    "applicant_email": "order.your_details",
    "applicant_address": "order.your_details",
}


def requires_order(*keys):
    """Only run the view if the order in the session has every key given.

    Otherwise redirect to the page that fills in the first missing key: someone
    arriving from a shared link or the browser's back button gets sent to the
    right step instead of a 500, and an order can never be sent incomplete.
    Being a view decorator, it guards GET and POST alike.
    """

    def decorator(view):
        # functools.wraps keeps the view's name. Without it every guarded view
        # is called "wrapper", and Flask fails at start-up with "View function
        # mapping is overwriting an existing endpoint function".
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            order = session.get("order") or {}
            for key in _FILLED_IN_BY:
                if key in keys and not order.get(key):
                    return redirect(url_for(_FILLED_IN_BY[key]))
            return view(*args, **kwargs)

        return wrapper

    return decorator


# How many recent orders this browser remembers as its own.
_PLACED_ORDERS_KEPT = 10


def _remember_placed(reference):
    placed = [ref for ref in session.get("placed_orders", []) if ref != reference]
    session["placed_orders"] = ([reference] + placed)[:_PLACED_ORDERS_KEPT]


def _placed_here(reference):
    """True if this browser placed the order.

    The reference is unguessable, but it sits in the URL and can leak in a
    screenshot, a shared link or browser history. Without this check anyone
    holding it could pay for the order, see its confirmation or download it.
    Other people's orders get a 404, not a 403: a 403 would confirm that the
    reference exists.
    """
    return reference in session.get("placed_orders", [])


def _abort_unless_placed_here(reference):
    """404 for another browser's order, and a note in the log.

    Someone opening an order they did not place is usually a shared link, but
    many of them in a row is worth noticing. Only the reference is logged.
    """
    if not _placed_here(reference):
        log.warning("Order %s requested by a browser that did not place it", reference)
        abort(404)


def _save(**fields):
    """Merge fields into the order kept in the session.

    Flask only notices assignments to top-level session keys. Changing the
    nested dict in place (session["order"]["x"] = y) would not be saved, so the
    whole dict is copied, updated and assigned back.
    """
    order = dict(session.get("order", {}))
    order.update(fields)
    session["order"] = order


def _changing():
    """True when the user came from a Change link on check answers."""
    return bool(request.args.get("change"))


def _next(endpoint):
    """Where to go after saving: back to check answers when changing an answer."""
    return url_for("order.check_answers") if _changing() else url_for(endpoint)


def _back(href):
    """Where the Back link goes: check answers when changing an answer."""
    return url_for("order.check_answers") if _changing() else href


def _prefill():
    """Answers to show on GET. On POST only what was submitted counts."""
    return session["order"] if request.method == "GET" else None


@bp.get("/start/<title_number>")
def start(title_number):
    session["order"] = {"title_number": title_number.strip().upper()}
    return redirect(url_for("order.document_type"))


@bp.route("/document-type", methods=["GET", "POST"])
@requires_order("title_number")
def document_type():
    form = DocumentTypeForm(data=_prefill())

    if form.validate_on_submit():
        _save(document_type=form.document_type.data)
        return redirect(_next("order.your_details"))

    title_number = session["order"]["title_number"]
    return render_template(
        "order/document_type.html",
        form=form,
        back_href=_back(url_for("search.detail", title_number=title_number)),
    )


@bp.route("/your-details", methods=["GET", "POST"])
@requires_order("title_number", "document_type")
def your_details():
    form = YourDetailsForm(data=_prefill())

    if form.validate_on_submit():
        _save(
            applicant_name=form.applicant_name.data,
            applicant_email=form.applicant_email.data,
            applicant_address=form.applicant_address.data,
        )
        return redirect(_next("order.check_answers"))

    return render_template(
        "order/your_details.html",
        form=form,
        back_href=_back(url_for("order.document_type")),
    )


@bp.route("/check-answers", methods=["GET", "POST"])
@requires_order(*_FILLED_IN_BY)
def check_answers():
    order = session["order"]
    form = ConfirmOrderForm()
    errors = None

    if form.validate_on_submit():
        try:
            created = get_api_client().create_order(
                title_number=order["title_number"],
                document_type=order["document_type"],
                applicant_name=order["applicant_name"],
                applicant_email=order["applicant_email"],
                applicant_address=order["applicant_address"],
            )
        except ValidationFailed as exc:
            errors = _error_list(exc.errors)
        except ApiError:
            return render_template("errors/503.html"), 503
        else:
            # Clear the order before redirecting (Post/Redirect/Get): a reload
            # or a second click must not create and charge a second order.
            session.pop("order", None)
            _remember_placed(created["reference"])
            return redirect(url_for("order.payment", reference=created["reference"]))

    return render_template(
        "order/check_answers.html",
        form=form,
        order=order,
        document_label=DOCUMENT_TYPE_LABELS[order["document_type"]],
        price_pence=ORDER_PRICE_PENCE,
        errors=errors,
    )


@bp.route("/payment/<reference>", methods=["GET", "POST"])
def payment(reference):
    _abort_unless_placed_here(reference)

    try:
        order = get_api_client().get_order(reference)
    except OrderNotFound:
        abort(404)
    except ApiError:
        return render_template("errors/503.html"), 503

    if order["status"] == "PAID":
        return redirect(url_for("order.confirmation", reference=reference))

    form = PaymentForm()
    if form.validate_on_submit():
        try:
            get_api_client().pay_order(reference)
        except OrderNotFound:
            abort(404)
        except ApiError:
            return render_template("errors/503.html"), 503
        return redirect(url_for("order.confirmation", reference=reference))

    return render_template(
        "order/payment.html",
        form=form,
        order=order,
        document_label=DOCUMENT_TYPE_LABELS[order["documentType"]],
    )


@bp.get("/confirmation/<reference>")
def confirmation(reference):
    _abort_unless_placed_here(reference)

    try:
        order = get_api_client().get_order(reference)
    except OrderNotFound:
        abort(404)
    except ApiError:
        return render_template("errors/503.html"), 503

    if order["status"] != "PAID":
        return redirect(url_for("order.payment", reference=reference))

    return render_template(
        "order/confirmation.html",
        order=order,
        document_label=DOCUMENT_TYPE_LABELS[order["documentType"]],
    )


@bp.get("/<reference>/document")
def document(reference):
    _abort_unless_placed_here(reference)

    try:
        copy = get_api_client().get_order_document(reference)
    except OrderNotPaid:
        return redirect(url_for("order.payment", reference=reference))
    except OrderNotFound:
        abort(404)
    except ApiError:
        return render_template("errors/503.html"), 503

    # Passed through untouched: the PDF is made by the API.
    response = Response(copy.content, mimetype="application/pdf")
    response.headers.set("Content-Disposition", "attachment", filename=copy.filename)
    return response


def _error_list(errors):
    """Build the list govukErrorSummary expects from the API's field errors."""
    items = []
    for field, message in errors.items():
        endpoint = _CHANGE_PAGE.get(field)
        item = {"text": message}
        if endpoint:
            item["href"] = url_for(endpoint) + "?change=1"
        items.append(item)
    return items
