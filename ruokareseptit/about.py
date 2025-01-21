"""Homepage"""
from flask import Blueprint
from flask import render_template

bp = Blueprint("about", __name__, url_prefix="/about")


@bp.route("/")
def index():
    """About us page"""
    context = {}
    return render_template("about/index.html", **context)


@bp.route("/instructions")
def instructions():
    """Instructions page"""
    context = {}
    return render_template("about/instructions.html", **context)


@bp.route("/instructions/abc")
def instructions_abc():
    """Instructions ABC"""
    context = {"title": "Ohjeet: ABC"}
    return render_template("about/placeholder.html", **context)


@bp.route("/instructions/xyz")
def instructions_xyz():
    """Instructions XYZ"""
    context = {"title": "Ohjeet: XYZ"}
    return render_template("about/placeholder.html", **context)


@bp.route("/contact")
def contact():
    """Contact page"""
    context = {}
    return render_template("about/contact.html", **context)
