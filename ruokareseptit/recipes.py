"""Published recipe listings
"""

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import current_app

from .db import get_db

bp = Blueprint("recipes", __name__, url_prefix="/recipes")


@bp.route("/", defaults={"recipe_id": None})
@bp.route("/<int:recipe_id>")
def index(recipe_id: int):
    """View published recipes
    """
    if recipe_id is None:
        page = int(request.args.get("page", 0))
        pub_recipes, remaining = list_published_recipes(page)
        context = {"recipes": pub_recipes}
        if remaining > 0:
            context["next_page"] = url_for("recipes.index", page=page + 1)
        if page > 0:
            context["prev_page"] = url_for("recipes.index", page=page - 1)
        return render_template("recipes/list.html", **context)

    recipe_context = fetch_published_recipe_context(recipe_id)
    if recipe_context is None:
        return redirect(url_for("recipes.list"))

    return render_template("recipes/view.html", **recipe_context)


@bp.route("/browse")
def browse():
    """Browse recipes
    """
    context = {}
    return render_template("recipes/browse.html", **context)


@bp.route("/browse/abc")
def browse_abc():
    """Browse category ABC
    """
    context = {"title": "Kategoria: ABC"}
    return render_template("recipes/placeholder.html", **context)


@bp.route("/browse/xyz")
def browse_xyz():
    """Browse category XYZ
    """
    context = {"title": "Kategoria: XYZ"}
    return render_template("recipes/placeholder.html", **context)


@bp.route("/search")
def search():
    """Contact page
    """
    context = {}
    return render_template("recipes/search.html", **context)


# Utility functions


def list_published_recipes(page: int):
    """Query all published recipes
    """
    total_rows = get_db().execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE published = 1
        """).fetchone()[0]
    page_size = current_app.config["RECIPE_LIST_PAGE_SIZE"]
    offset = page * page_size
    pub_recipes = get_db().execute(
        """
        SELECT *
        FROM recipes
        LIMIT ? OFFSET ?
        """, [page_size, offset]
    )
    recipes_remaining = total_rows - offset - page_size
    return pub_recipes, recipes_remaining


def fetch_published_recipe_context(recipe_id: int):
    """Fetch a recipe from database. The recipe must be
    published. Returns a dict to be used as a `render_template`
    context.
    """
    recipe_row = get_db().execute(
        """
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users
        ON recipes.author_id = users.id
        WHERE recipes.id = ? AND published = 1
        """, [recipe_id]).fetchone()

    if recipe_row is None:
        return None

    ingredients, instructions, categories = fetch_recipe_related(recipe_id)

    return {
        "recipe": recipe_row,
        "ingredients": ingredients,
        "instructions": instructions,
        "categories": categories
    }


def fetch_recipe_related(recipe_id):
    """Fetch content from tables related to recipe
    """
    ingredients_limit = current_app.config["RECIPE_INGREDIENTS_MAX"]
    ingredients = get_db().execute(
        """
        SELECT * FROM ingredients WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, ingredients_limit])

    instructions_limit = current_app.config["RECIPE_INSTRUCTIONS_MAX"]
    instructions = get_db().execute(
        """
        SELECT * FROM instructions WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, instructions_limit])

    categories_limit = current_app.config["RECIPE_CATEGORIES_MAX"]
    categories = get_db().execute(
        """
        SELECT categories.title
        FROM recipe_category
        JOIN categories
        ON recipe_category.category_id = categories.id
        WHERE recipe_category.recipe_id = ?
        LIMIT ?
        """, [recipe_id, categories_limit])

    return ingredients, instructions, categories
