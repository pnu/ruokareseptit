"""Homepage"""

from flask import Blueprint
from flask import current_app
from flask import render_template

bp = Blueprint("home", __name__)

@bp.route("/")
def index():
    """Homepage"""
    hello_what = current_app.config["HELLO_WHAT"]
    return render_template("home/index.html", hello_what=hello_what)
