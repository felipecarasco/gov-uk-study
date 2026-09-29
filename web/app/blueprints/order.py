from flask import Blueprint, abort, redirect, render_template, session, url_for

from app.forms.order import DocumentTypeForm

bp = Blueprint("order", __name__, url_prefix="/order")


def _save(**fields):
    """Merge fields into the order kept in the session.

    Flask only notices assignments to top-level session keys. Changing the
    nested dict in place (session["order"]["x"] = y) would not be saved, so the
    whole dict is copied, updated and assigned back.
    """
    order = dict(session.get("order", {}))
    order.update(fields)
    session["order"] = order


@bp.get("/start/<title_number>")
def start(title_number):
    session["order"] = {"title_number": title_number.strip().upper()}
    return redirect(url_for("order.document_type"))


@bp.route("/document-type", methods=["GET", "POST"])
def document_type():
    form = DocumentTypeForm()

    if form.validate_on_submit():
        _save(document_type=form.document_type.data)
        return redirect(url_for("order.your_details"))

    return render_template(
        "order/document_type.html",
        form=form,
        title_number=session["order"]["title_number"],
    )


@bp.get("/your-details")
def your_details():
    # Placeholder so that url_for("order.your_details") resolves.
    # Task 6 replaces it with the real page.
    abort(501)
