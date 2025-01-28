"""User edit pages and features
"""

import re

from flask import Blueprint
from flask import render_template
from flask import g
from flask import url_for
from flask import request
from flask import session
from flask import flash
from flask import redirect
from flask import current_app

from .db import get_db
from .auth import login_required
from .recipes import fetch_recipe_related

bp = Blueprint("edit", __name__, url_prefix="/edit")


@bp.route("/recipe/", defaults={"recipe_id": None, "tab": None})
@bp.route("/recipe/<int:recipe_id>", defaults={"tab": 1})
@bp.route("/recipe/<int:recipe_id>/", defaults={"tab": 1})
@bp.route("/recipe/<int:recipe_id>/<int:tab>")
@login_required
def recipe(recipe_id: int, tab: int):
    """Own recipes
    """
    if recipe_id is None:
        page = int(request.args.get("page", 0))
        user_recipes, remaining = list_user_recipes(g.user["id"], page)
        context = {"recipes": user_recipes}
        if remaining > 0:
            context["next_page"] = url_for("edit.recipe", page=page + 1)
        if page > 0:
            context["prev_page"] = url_for("edit.recipe", page=page - 1)
        return render_template("edit/recipes.html", **context)

    recipe_context = fetch_author_recipe_context(recipe_id, g.user["id"])
    if recipe_context is None:
        return redirect(url_for("edit.recipe"))

    back = request.args.get("back", url_for("edit.recipe"))
    submit_url = url_for("edit.recipe_update",
                         recipe_id=recipe_id,
                         tab=tab,
                         back=back)
    recipe_context["submit_url"] = submit_url
    tmpl = ["", "_ingredients", "_instructions"][tab - 1]
    return render_template("edit/recipe" + tmpl + ".html", **recipe_context)


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


@bp.route("/recipe/update/<int:recipe_id>", methods=["POST"])
@login_required
def recipe_update(recipe_id: int):
    """Update recipe
    """
    update_author_recipe(recipe_id, g.user["id"], request.form)
    update_recipe_ingredients(recipe_id, request.form)

    if request.form.get("return", False):
        return redirect(request.args.get("back", url_for("edit.recipe")))

    tab = int(request.args.get("tab", 1))
    param = {
        "recipe_id": recipe_id,
        "tab": int(request.form.get("tab", tab)),
        "back": request.args.get("back", "")
    }
    return redirect(url_for("edit.recipe", **param))


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


def list_user_recipes(author_id: int, page: int):
    """Query recipes of user `author_id`
    """
    total_rows = get_db().execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE author_id = ?
        """, [author_id]).fetchone()[0]
    page_size = current_app.config["RECIPE_LIST_PAGE_SIZE"]
    offset = page * page_size
    user_recipes = get_db().execute(
        """
        SELECT *
        FROM recipes
        WHERE author_id = ? LIMIT ? OFFSET ?
        """, [author_id, page_size, offset]
    )
    recipes_remaining = total_rows - offset - page_size
    return user_recipes, recipes_remaining


def fetch_author_recipe_context(recipe_id: int, author_id: int):
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

    ingredients, instructions, categories = fetch_recipe_related(recipe_id)

    return {
        "recipe": recipe_row,
        "ingredients": ingredients,
        "instructions": instructions,
        "categories": categories
    }


def update_author_recipe(recipe_id: int, author_id: int, fields: dict) -> bool:
    """Update recipe to database. Recipe author_id must match.
    """
    try:
        # For checkbox `published` we need to distinguish between
        # cases when checkbox is not checked vs. it's not part
        # of the form.
        is_pub_default = fields.get("published.default")
        is_pub = fields.get("published", is_pub_default)
        with get_db() as db:
            db.execute(
                """
                UPDATE recipes
                SET title = IFNULL(?, title),
                summary = IFNULL(?, summary),
                preparation_time = IFNULL(?, preparation_time),
                cooking_time = IFNULL(? ,cooking_time),
                skill_level = IFNULL(?, skill_level),
                portions = IFNULL(?, portions),
                published = IFNULL(?, published)
                WHERE id = ? AND author_id = ?
                """, [
                    fields.get("title"),
                    fields.get("summary"),
                    fields.get("preparation_time"),
                    fields.get("cooking_time"),
                    fields.get("skill_level"),
                    fields.get("portions"),
                    is_pub,
                    recipe_id,
                    author_id
                ])
            return True
    except db.IntegrityError:
        print("HUI")
        return False


def update_recipe_ingredients(recipe_id: int, fields: dict):
    """Update all ingredients values from form keys eg.
    `ingredients_ID_amount` and `ingredients_ID_title`.
    Triggers also move, delete and add row actions.
    """
    ingredient_data = {}
    for key in fields:
        field = re.match(r"^ingredients_(\d+)_(\w+)$", key)
        if field is not None:
            i_id = field.group(1)
            column = field.group(2)
            value = fields[key]
            if column == "up":
                move_ingredients_row_up(recipe_id, i_id)
            elif column == "down":
                move_ingredients_row_down(recipe_id, i_id)
            elif column == "delete":
                delete_ingredients_row(recipe_id, i_id)
            else:
                if i_id not in ingredient_data:
                    ingredient_data[i_id] = {}
                ingredient_data[i_id][column] = value

    for i_id, values in ingredient_data.items():
        update_ingredients_row(recipe_id, i_id, values)

    if fields.get("ingredients_add_row", False):
        add_ingredients_row(recipe_id)


def add_ingredients_row(recipe_id: int) -> bool:
    """Add ingredients row to recipe
    """
    try:
        with get_db() as db:
            db.execute(
                """
                INSERT INTO ingredients (recipe_id, order_number)
                SELECT ?, IFNULL(MAX(order_number), 0) + 1
                FROM ingredients
                WHERE recipe_id = ?
                """, [recipe_id, recipe_id])
            return True
    except db.IntegrityError:
        return False


def delete_ingredients_row(recipe_id: int, ingredient_id: int) -> bool:
    """Delete s ingredients row from a recipe
    """
    try:
        with get_db() as db:
            db.execute(
                """
                DELETE FROM ingredients
                    WHERE recipe_id = ? AND id = ?
                """, [recipe_id, ingredient_id])
            return True
    except db.IntegrityError:
        return False


def update_ingredients_row(recipe_id: int, i_id: int, values: dict) -> bool:
    """Update ingredients
    """
    print(i_id, values)
    try:
        with get_db() as db:
            db.execute(
                """
                UPDATE ingredients
                SET (amount, unit, title) = (?, ?, ?)
                WHERE recipe_id = ? AND id = ?
                """, [
                    values["amount"],
                    values["unit"],
                    values["title"],
                    recipe_id, i_id]
                )
            return True
    except db.IntegrityError:
        return False


def move_ingredients_row_up(recipe_id: int, ingredient_id: int) -> bool:
    """Move up
    """
    try:
        with get_db() as db:
            db.execute(
                """
                WITH prev AS (
                    SELECT id, MAX(order_number) AS order_number
                    FROM ingredients
                    WHERE order_number < (
                        SELECT order_number FROM ingredients
                        WHERE id = :ingredient_id
                    ) AND recipe_id = :recipe_id
                ), this AS (
                    SELECT id, order_number
                    FROM ingredients
                    WHERE id = :ingredient_id
                    AND recipe_id = :recipe_id
                )
                UPDATE ingredients SET order_number = CASE
                    WHEN ingredients.id = prev.id THEN this.order_number
                    WHEN ingredients.id = this.id THEN prev.order_number
                    END
                FROM prev, this
                WHERE recipe_id = :recipe_id
                AND ingredients.id in (prev.id, this.id)
                """, {
                    "recipe_id": recipe_id,
                    "ingredient_id": ingredient_id
                })
            return True
    except db.IntegrityError:
        return False


def move_ingredients_row_down(recipe_id: int, ingredient_id: int) -> bool:
    """Move down
    """
    try:
        with get_db() as db:
            db.execute(
                """
                WITH next AS (
                    SELECT id, MIN(order_number) AS order_number
                    FROM ingredients
                    WHERE order_number > (
                        SELECT order_number FROM ingredients
                        WHERE id = :ingredient_id
                    ) AND recipe_id = :recipe_id
                ), this AS (
                    SELECT id, order_number
                    FROM ingredients
                    WHERE id = :ingredient_id
                    AND recipe_id = :recipe_id
                )
                UPDATE ingredients SET order_number = CASE
                    WHEN ingredients.id = next.id THEN this.order_number
                    WHEN ingredients.id = this.id THEN next.order_number
                    END
                FROM next, this
                WHERE recipe_id = :recipe_id
                AND ingredients.id in (next.id, this.id)
                """, {
                    "recipe_id": recipe_id,
                    "ingredient_id": ingredient_id
                })
            return True
    except db.IntegrityError:
        return False
