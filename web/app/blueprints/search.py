from flask import Blueprint, redirect, render_template, url_for

from app.api_client import ApiError, TitleNotFound, get_api_client
from app.forms.search import TitleNumberForm

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.route("/title-number", methods=["GET", "POST"])
def title_number():
    form = TitleNumberForm()

    if form.validate_on_submit():
        return redirect(url_for("search.detail", title_number=form.title_number.data))

    return render_template("search/title_number.html", form=form)


@bp.get("/titles/<title_number>")
def detail(title_number):
    try:
        titulo = get_api_client().get_title(title_number)
    except TitleNotFound:
        return render_template(
            "search/not_found.html", title_number=title_number.upper()
        ), 404
    except ApiError:
        return render_template("search/unavailable.html"), 503

    return render_template("search/detail.html", title=titulo)
