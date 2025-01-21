"""User profile pages and features"""

from flask import Blueprint
from flask import render_template
from flask import g

bp = Blueprint("profile", __name__, url_prefix="/profile")


@bp.route("/")
def index():
    """Profile page"""
    context = {"username": g.user["username"]}
    return render_template("profile/index.html", **context)


@bp.route("/recipes")
def recipes():
    """Own recipes"""
    context = {}
    return render_template("profile/recipes.html", **context)


@bp.route("/friends")
def friends():
    """Own friends"""
    context = {}
    return render_template("profile/friends.html", **context)


@bp.route("/settings")
def settings():
    """Own settings"""
    context = {}
    return render_template("profile/settings.html", **context)
