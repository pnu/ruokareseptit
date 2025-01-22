"""User edit pages and features"""

from flask import Blueprint
from flask import render_template
from flask import g
from flask import url_for

from .db import get_db
from .auth import login_required

bp = Blueprint("edit", __name__, url_prefix="/edit")


@bp.route("/recipes/", defaults={'page': 0})
@bp.route("/recipes/<int:page>")
@login_required
def recipes(page):
    """Own recipes"""
    query = "SELECT * FROM recipes WHERE author_id = ? LIMIT 11 OFFSET ?"
    cursor = get_db().execute(query, [g.user["id"], page * 10])
    rows = cursor.fetchall()
    context = {"recipes": rows}
    if len(rows) > 10:
        rows.pop()
        context["next_page"] = url_for("edit.recipes", page=page + 1)
    if page > 0:
        context["prev_page"] = url_for("edit.recipes", page=page - 1)
    return render_template("edit/recipes.html", **context)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create new recipe"""
    context = {}
    return render_template("edit/create.html", **context)


@bp.route("/settings")
def settings():
    """Own settings"""
    context = {}
    return render_template("edit/settings.html", **context)
