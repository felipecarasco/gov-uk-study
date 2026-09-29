from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app.forms.order import DocumentTypeForm, YourDetailsForm

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


@bp.route("/your-details", methods=["GET", "POST"])
def your_details():
    # On GET the form is filled in from the session, so going back keeps the
    # answers. On POST only what was submitted counts: a field missing from the
    # request must not be quietly taken from the session.
    form = YourDetailsForm(data=session["order"] if request.method == "GET" else None)

    if form.validate_on_submit():
        _save(
            applicant_name=form.applicant_name.data,
            applicant_email=form.applicant_email.data,
            applicant_address=form.applicant_address.data,
        )
        return redirect(url_for("order.check_answers"))

    return render_template("order/your_details.html", form=form)


@bp.get("/check-answers")
def check_answers():
    # Placeholder so that url_for("order.check_answers") resolves.
    # Task 7 replaces it with the real page.
    abort(501)
