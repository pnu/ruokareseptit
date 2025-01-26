"""User edit pages and features
"""

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

RECIPE_INGREDIENTS_MAX = 20
RECIPE_INSTRUCTIONS_MAX = 20
RECIPE_CATEGORIES_MAX = 20
RECIPE_LIST_PAGE_SIZE = 5


@bp.route("/recipe/", defaults={"recipe_id": None})
@bp.route("/recipe/<int:recipe_id>")
@login_required
def recipe(recipe_id: int):
    """Own recipes
    """
    if recipe_id is None:
        page = int(request.args.get("page", 0))
        user_recipes, count = list_user_recipes(
            g.user["id"], RECIPE_LIST_PAGE_SIZE, page
        )
        context = {"recipes": user_recipes}
        if count - page * RECIPE_LIST_PAGE_SIZE > RECIPE_LIST_PAGE_SIZE:
            context["next_page"] = url_for("edit.recipe", page=page + 1)
        if page > 0:
            context["prev_page"] = url_for("edit.recipe", page=page - 1)
        return render_template("edit/recipes.html", **context)

    recipe_context = fetch_recipe_context(recipe_id, g.user["id"])
    if recipe_context is None:
        return redirect(url_for("edit.recipe"))

    return render_template("edit/recipe.html", **recipe_context)


@bp.route("/recipe/create", methods=["GET", "POST"])
@login_required
def create():
    """Create new recipe
    """
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
            flash_error("Nimi on jo varattu. Valitse toinen nimi.")
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


@bp.route("/recipe/update/<int:recipe_id>")
@login_required
def recipe_update(recipe_id: int):
    """Update recipe
    """
    return f"updated recipe {recipe_id}"


@bp.route("/recipe/delete/<int:recipe_id>")
@login_required
def recipe_delete(recipe_id: int):
    """Delete recipe
    """
    return f"deleted recipe {recipe_id}"


@bp.route("/settings")
def settings():
    """Own settings
    """
    context = {}
    return render_template("edit/settings.html", **context)


# Utility functions


def flash_error(message: str):
    """Flash form validation error
    """
    flash(message, "form_validation_error")


def insert_recipe(title: str, summary: str) -> int | None:
    """Insert new recipe to database. Return id if successful,
    None otherwise.
    """
    try:
        with get_db() as db:
            res = db.execute(
                """
                INSERT INTO recipes (title, summary, author_id)
                VALUES (?, ?, ?)
                """, [title, summary, session["uid"]])
            return res.lastrowid
    except db.IntegrityError:
        return None


def list_user_recipes(author_id: int, page_size: int, page: int):
    """Query recipes of user `author_id`
    """
    user_recipes_total_count = get_db().execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE author_id = ?
        """, [author_id]).fetchone()[0]

    user_recipes = get_db().execute(
        """
        SELECT *
        FROM recipes
        WHERE author_id = ? LIMIT ? OFFSET ?
        """, [author_id, page_size, page * page_size]
    )
    return user_recipes, user_recipes_total_count


def fetch_recipe_context(recipe_id: int, author_id: int):
    """Fetch a recipe from database. The recipe `author_id` in
    databse must match the `author_id` passed. Returns a dict
    to be used as a `render_template` context.
    """
    recipe_row = get_db().execute(
        """
        SELECT *
        FROM recipes
        WHERE id = ? AND author_id = ?
        """, [recipe_id, author_id]).fetchone()

    if recipe_row is None:
        return None

    ingredients = get_db().execute(
        """
        SELECT * FROM ingredients WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, RECIPE_INGREDIENTS_MAX])

    instructions = get_db().execute(
        """
        SELECT * FROM instructions WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, RECIPE_INSTRUCTIONS_MAX])

    categories = get_db().execute(
        """
        SELECT categories.title
        FROM recipe_category
        JOIN categories
        ON recipe_category.category_id = categories.id
        WHERE recipe_category.recipe_id = ?
        LIMIT ?
        """, [recipe_id, RECIPE_CATEGORIES_MAX])

    return {
        "recipe": recipe_row,
        "ingredients": ingredients,
        "instructions": instructions,
        "categories": categories
    }
