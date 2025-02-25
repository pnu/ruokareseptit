"""User edit pages and features
"""

from flask import Blueprint
from flask import render_template

bp = Blueprint("reviews", __name__, url_prefix="/reviews", template_folder="templates")


@bp.route("/")
def index():
    """Own reviews
    """
    context = {}
    return render_template("my/reviews/list.html", **context)
