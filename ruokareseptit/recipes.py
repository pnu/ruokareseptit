"""Published recipe listings
"""

from flask import Blueprint
from flask import render_template

bp = Blueprint("recipes", __name__, url_prefix="/recipes")


@bp.route("/")
def index():
    """Recipes main page
    """
    context = {}
    return render_template("recipes/index.html", **context)


@bp.route("/browse")
def browse():
    """Browse recipes
    """
    context = {}
    return render_template("recipes/browse.html", **context)


@bp.route("/browse/abc")
def browse_abc():
    """Browse category ABC
    """
    context = {"title": "Kategoria: ABC"}
    return render_template("recipes/placeholder.html", **context)


@bp.route("/browse/xyz")
def browse_xyz():
    """Browse category XYZ
    """
    context = {"title": "Kategoria: XYZ"}
    return render_template("recipes/placeholder.html", **context)


@bp.route("/search")
def search():
    """Contact page
    """
    context = {}
    return render_template("recipes/search.html", **context)
