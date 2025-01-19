"""Homepage"""

from flask import Blueprint, current_app

bp = Blueprint("home", __name__)

@bp.route("/")
def index():
    """Homepage"""
    return f"Hello {current_app.config['HELLO_WHAT']}!"
