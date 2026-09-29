from flask import Blueprint, redirect, render_template, request, url_for

from app import postcodes

from app.api_client import ApiError, TitleNotFound, ValidationFailed, get_api_client
from app.forms.search import PostcodeForm, TitleNumberForm

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.route("/title-number", methods=["GET", "POST"])
def title_number():
    form = TitleNumberForm()

    if form.validate_on_submit():
        return redirect(url_for("search.detail", title_number=form.title_number.data))

    return render_template("search/title_number.html", form=form)


@bp.route("/postcode", methods=["GET", "POST"])
def postcode():
    form = PostcodeForm()

    if form.validate_on_submit():
        # Results live at a GET URL (Post/Redirect/Get), so they can be bookmarked,
        # shared and reached again with the browser's Back button.
        return redirect(url_for("search.results", postcode=postcodes.normalise(form.postcode.data)))

    return render_template("search/postcode.html", form=form)


@bp.get("/results")
def results():
    postcode = postcodes.normalise(request.args.get("postcode"))
    if not postcodes.is_valid(postcode):
        return redirect(url_for("search.postcode"))

    cursor = request.args.get("cursor")
    try:
        found = get_api_client().search_titles(postcode, cursor)
    except ValidationFailed:
        if cursor:
            # A cursor edited by hand, or left over from an old link: start the
            # search again from the first page rather than showing an error.
            return redirect(url_for("search.results", postcode=postcode))
        return redirect(url_for("search.postcode"))
    except ApiError:
        return render_template("search/unavailable.html"), 503

    def page_href(page_cursor):
        return (
            url_for("search.results", postcode=postcode, cursor=page_cursor)
            if page_cursor
            else None
        )

    return render_template(
        "search/results.html",
        postcode=postcodes.format_for_display(postcode),
        titles=found["results"],
        total=found["total"],
        previous_href=page_href(found["previousCursor"]),
        next_href=page_href(found["nextCursor"]),
    )


@bp.get("/titles/<title_number>")
def detail(title_number):
    try:
        title = get_api_client().get_title(title_number)
    except TitleNotFound:
        return render_template("search/not_found.html", title_number=title_number.upper()), 404
    except ApiError:
        return render_template("search/unavailable.html"), 503

    return render_template("search/detail.html", title=title)
