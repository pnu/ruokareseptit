"""User profile pages and features"""

from flask import Blueprint
from flask import render_template
from flask import g
from flask import url_for

from .db import get_db

bp = Blueprint("profile", __name__, url_prefix="/profile")


@bp.route("/")
def index():
    """Profile page"""
    context = {"username": g.user["username"]}
    return render_template("profile/index.html", **context)


@bp.route("/recipes/", defaults={'page': 0})
@bp.route("/recipes/<page>")
def recipes(page):
    """Own recipes"""
    query = "SELECT * FROM recipes WHERE author_id = ? LIMIT 11 OFFSET ?"
    cursor = get_db().execute(query, [g.user["id"], page * 10])
    rows = cursor.fetchall()
    context = {"recipes": rows}
    if len(rows) > 10:
        rows.pop()
        context["next_page"] = url_for("profile.recipes", page=page + 1)
    if page > 0:
        context["prev_page"] = url_for("profile.recipes", page=page - 1)
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
