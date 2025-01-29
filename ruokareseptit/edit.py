"""User edit pages and features
"""

import re
from sqlite3 import Connection

from flask import Blueprint
from flask import render_template
from flask import g
from flask import url_for
from flask import request
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
        with get_db() as db:
            page = int(request.args.get("page", 0))
            u_recipes, count, more = list_user_recipes(db, g.user["id"], page)
            context = {"recipes": u_recipes, "count": count}
            if more > 0:
                context["next_page"] = url_for("edit.recipe", page=page + 1)
            if page > 0:
                context["prev_page"] = url_for("edit.recipe", page=page - 1)
            return render_template("edit/recipes.html", **context)

    with get_db() as db:
        recipe_context = fetch_author_recipe_context(db, recipe_id, g.user["id"])
        if recipe_context is None:
            return redirect(url_for("edit.recipe"))

        back = request.args.get("back", url_for("edit.recipe"))
        submit_url = url_for("edit.recipe_update", recipe_id=recipe_id,
                             tab=tab, back=back)
        recipe_context["submit_url"] = submit_url
        tmpl = ["", "_ingredients", "_instructions"][tab - 1]
        return render_template("edit/recipe" + tmpl + ".html", **recipe_context)


@bp.route("/recipe/create", methods=["GET", "POST"])
@login_required
def create():
    """Create new recipe
    """
    if request.method == "GET":
        return render_template("edit/create.html")

    recipe_id = None
    if validate_create_form(request.form) is False:
        return redirect(url_for("edit.create", **request.form))

    try:
        with get_db() as db:
            cursor = insert_recipe(db, g.user["id"], request.form)
            recipe_id = cursor.lastrowid
    except db.IntegrityError:
        flash_error("Nimi on jo varattu. Valitse toinen nimi.")
        return redirect(url_for("edit.create", **request.form))

    flash("Uusi resepti on luotu.")
    return redirect(url_for("edit.recipe", recipe_id=recipe_id))


def validate_create_form(fields: dict[str, str]) -> bool:
    """Validate create recipe form fields
    """
    title = fields.get("title")
    # summary = fields.get("summary")
    if title == "":
        flash_error("Reseptin nimi on pakollinen.")
    elif len(title) < 4 or not title.isalnum():
        flash_error("Reseptin nimi ei ole vaatimusten mukainen.")
    else:
        return True
    return False


@bp.route("/recipe/update/<int:recipe_id>", methods=["POST"])
@login_required
def recipe_update(recipe_id: int):
    """Update recipe
    """
    edit_params = {
        "recipe_id": recipe_id,
        "tab": int(request.args.get("tab", 1)),
        "back": request.args.get("back", "")
    }
    try:
        with get_db() as db:
            update_author_recipe(db, recipe_id, g.user["id"], request.form)
            update_recipe_ingredients(db, recipe_id, request.form)
    except db.IntegrityError:
        flash("Reseptin päivittäminen epäonnistui.")
        return redirect(url_for("edit.recipe", **edit_params))

    if request.form.get("return"):
        return redirect(request.args.get("back", url_for("edit.recipe")))

    edit_params["tab"] = int(request.form.get("tab", edit_params["tab"]))
    return redirect(url_for("edit.recipe", **edit_params))


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


# Utility functions ######################################################


def flash_error(message: str):
    """Flash form validation error
    """
    flash(message, "form_validation_error")


def update_recipe_ingredients(
        db: Connection, recipe_id: int, fields: dict[str, str]):
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
                move_ingredients_row_up(db, recipe_id, i_id)
            elif column == "down":
                move_ingredients_row_down(db, recipe_id, i_id)
            elif column == "delete":
                delete_ingredients_row(db, recipe_id, i_id)
            else:
                if i_id not in ingredient_data:
                    ingredient_data[i_id] = {}
                ingredient_data[i_id][column] = value

    for i_id, i_fields in ingredient_data.items():
        update_ingredients_row(db, recipe_id, i_id, i_fields)

    if fields.get("ingredients_add_row", False):
        add_ingredients_row(db, recipe_id)


# SQL queries for READ operations ########################################


def list_user_recipes(db: Connection, author_id: int, page: int):
    """Query recipes of user `author_id`
    """
    total_rows = db.execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE author_id = ?
        """, [author_id]).fetchone()[0]
    page_size = current_app.config["RECIPE_LIST_PAGE_SIZE"]
    offset = page * page_size
    user_recipes = db.execute(
        """
        SELECT *
        FROM recipes
        WHERE author_id = ? LIMIT ? OFFSET ?
        """, [author_id, page_size, offset]
    )
    recipes_remaining = total_rows - offset - page_size
    return user_recipes, total_rows, recipes_remaining


def fetch_author_recipe_context(db: Connection, recipe_id: int, author_id: int):
    """Fetch a recipe from database. The recipe `author_id` in
    databse must match the `author_id` passed. Returns a dict
    to be used as a `render_template` context.
    """
    recipe_row = db.execute(
        """
        SELECT *
        FROM recipes
        WHERE id = ? AND author_id = ?
        """, [recipe_id, author_id]).fetchone()

    if recipe_row is None:
        return None

    related = fetch_recipe_related(db, recipe_id)
    return {"recipe": recipe_row, **related}


# SQL queries for CREATE / UPDATE operations #############################


def insert_recipe(db: Connection, author_id: int, fields: dict[str, str]):
    """Insert new recipe to database. Fields must include keys
    `title`, `summary` and `author_id`.
    """
    fields = {**fields, "author_id": author_id}
    cursor = db.execute(
        """
        INSERT INTO recipes (title, summary, author_id)
        VALUES (:title, :summary, :author_id)
        """, fields)
    return cursor


def update_author_recipe(
        db: Connection, recipe_id: int, author_id: int, fields: dict[str, str]):
    """Update recipe to database. Recipe author_id must match.
    """
    # Need to use "?" placeholders because some (or even all)
    # of the fields may be missing. Passing a dict and using named
    # parameters would raise an error about missing value.
    title = fields.get("title")
    summary = fields.get("summary")
    preparation_time = fields.get("preparation_time")
    cooking_time = fields.get("cooking_time")
    skill_level = fields.get("skill_level")
    portions = fields.get("portions")
    # For checkbox `published` we need to distinguish between
    # cases when checkbox is not checked vs. it's not part
    # of the form.
    is_pub_default = fields.get("published.default")
    published = fields.get("published", is_pub_default)
    cursor = db.execute(
        """
        UPDATE recipes
        SET title = IFNULL(?, title),
        summary = IFNULL(?, summary),
        preparation_time = IFNULL(?, preparation_time),
        cooking_time = IFNULL(?, cooking_time),
        skill_level = IFNULL(?, skill_level),
        portions = IFNULL(?, portions),
        published = IFNULL(?, published)
        WHERE id = ? AND author_id = ?
        """, (title, summary, preparation_time,
        cooking_time, skill_level, portions, published,
        recipe_id, author_id))
    return cursor


def add_ingredients_row(db: Connection, recipe_id: int):
    """Add ingredients row to recipe
    """
    cursor = db.execute(
        """
        INSERT INTO ingredients (recipe_id, order_number)
        SELECT ?, IFNULL(MAX(order_number), 0) + 1
        FROM ingredients
        WHERE recipe_id = ?
        """, [recipe_id, recipe_id])
    return cursor


def delete_ingredients_row(db: Connection, recipe_id: int, ingredient_id: int) -> bool:
    """Delete s ingredients row from a recipe
    """
    cursor = db.execute(
        """
        DELETE FROM ingredients
        WHERE recipe_id = ? AND id = ?
        """, [recipe_id, ingredient_id])
    return cursor


def update_ingredients_row(
        db: Connection, recipe_id: int, i_id: int, fields: dict[str, str]) -> bool:
    """Update specific ingredients row. Fields must contain keys
    `amount`, `unit` and `title`.
    """
    fields = {**fields, "recipe_id": recipe_id, "i_id": i_id}
    cursor = db.execute(
        """
        UPDATE ingredients
        SET (amount,  unit,  title)
         = (:amount, :unit, :title)
        WHERE recipe_id = :recipe_id AND id = :i_id
        """, fields)
    return cursor


def move_ingredients_row_up(db: Connection, recipe_id: int, ingredient_id: int) -> bool:
    """Move ingredient up by swapping order_number values
    with the previous ingredient (in order of appearance).
    """
    cursor = db.execute(
        """
        UPDATE ingredients SET order_number = CASE
        WHEN ingredients.id = prev_id THEN this.order_number
        WHEN ingredients.id = this.id THEN prev_order_number
        END FROM ingredients AS this, (SELECT id,
            lag(id) OVER (ORDER BY order_number) AS prev_id,
            lag(order_number) OVER (ORDER BY order_number) AS prev_order_number
            FROM ingredients WHERE recipe_id = ?) AS prev
        WHERE this.id = prev.id
        AND this.id = ?
        AND ingredients.id IN (this.id, prev_id);
        """, [recipe_id, ingredient_id])
    return cursor


def move_ingredients_row_down(db: Connection, recipe_id: int, ingredient_id: int) -> bool:
    """Move ingredient down by swapping order_number values
    with the next ingredient (in order of appearance).
    """
    cursor = db.execute(
        """
        UPDATE ingredients SET order_number = CASE
        WHEN ingredients.id = next_id THEN this.order_number
        WHEN ingredients.id = this.id THEN next_order_number
        END FROM ingredients AS this, (SELECT id,
            lead(id) OVER (ORDER BY order_number) AS next_id,
            lead(order_number) OVER (ORDER BY order_number) AS next_order_number
            FROM ingredients WHERE recipe_id = ?) AS next
        WHERE this.id = next.id
        AND this.id = ?
        AND ingredients.id IN (this.id, next_id);
        """, [recipe_id, ingredient_id])
    return cursor
