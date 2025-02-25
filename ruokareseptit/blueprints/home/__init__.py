"""Homepage
"""

from flask import Blueprint
from flask import current_app
from flask import render_template

bp = Blueprint("home", __name__, template_folder="templates")


@bp.route("/")
def index():
    """Homepage
    """
    hello_what = current_app.config["HELLO_WHAT"]
    context = {
        "hello_what": hello_what
    }
    return render_template("home/index.html", **context)
