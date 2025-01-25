"""User edit pages and features"""

from flask import Blueprint
from flask import render_template
from flask import g
from flask import url_for
from flask import request
from flask import session
from flask import flash
from flask import redirect

from .db import get_db
from .auth import login_required

bp = Blueprint("edit", __name__, url_prefix="/edit")


@bp.route("/recipe/", defaults={"recipe_id": None})
@bp.route("/recipe/<int:recipe_id>")
@login_required
def recipe(recipe_id: int):
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
    if request.method == "GET":
        session.pop("create_recipe_title", None)
        session.pop("create_recipe_summary", None)
        return render_template("edit/create.html")

    title = request.form["title"]
    summary = request.form["summary"]
    session["create_recipe_title"] = title
    session["create_recipe_summary"] = summary

    if title == "":
        flash_error("Reseptin nimi on pakollinen.")
    elif len(title) < 4 or not title.isalnum():
        flash_error("Reseptin nimi ei ole vaatimusten mukainen.")
    else:
        recipe_id = insert_recipe(title, summary)
        if recipe_id is None:
            flash_error("Palvelussa on jo samanniminen resepti. Valitse toinen nimi.")
        else:
            flash("Uusi resepti on luotu.")
            session.pop("create_recipe_title", None)
            session.pop("create_recipe_summary", None)
            return redirect(url_for("edit.recipe", recipe_id=recipe_id))

    context = {
        "title": session.pop("create_recipe_title", ""),
        "summary": session.pop("create_recipe_summary", "")
    }
    return render_template("edit/create.html", **context)


@bp.route("/settings")
def settings():
    """Own settings"""
    context = {}
    return render_template("edit/settings.html", **context)


# Utility functions

def flash_error(message: str):
    """Flash form validation error"""
    flash(message, "form_validation_error")

def insert_recipe(title: str, summary: str) -> int | None:
    """Insert new recipe to database. Return id if successful,
    None otherwise."""
    try:
        query = "INSERT INTO recipes (title, summary, author_id) VALUES (?, ?, ?)"
        params = (title, summary, session["uid"])
        db = get_db()
        res = db.execute(query, params)
        db.commit()
        return res.lastrowid
    except db.IntegrityError:
        return None
