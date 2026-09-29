from flask import Blueprint, render_template

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("main/index.html")


@bp.get("/accessibility")
def accessibility():
    return render_template("main/accessibility.html")


@bp.get("/cookies")
def cookies():
    return render_template("main/cookies.html")


@bp.get("/privacy")
def privacy():
    return render_template("main/privacy.html")
