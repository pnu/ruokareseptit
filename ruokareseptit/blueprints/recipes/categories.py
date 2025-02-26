"""Recipe categories
"""

from flask import Blueprint
from flask import render_template

bp = Blueprint("categories", __name__, url_prefix="/categories", template_folder="templates")


@bp.route("/")
def index():
    """Browse all categories
    """
    context = {}
    return render_template("recipes/categories/all.html", **context)


@bp.route("/abc")
def abc():
    """Browse category ABC
    """
    context = {"title": "Kategoria: ABC"}
    return render_template("recipes/categories/placeholder.html", **context)


@bp.route("/xyz")
def xyz():
    """Browse category XYZ
    """
    context = {"title": "Kategoria: XYZ"}
    return render_template("recipes/categories/placeholder.html", **context)
