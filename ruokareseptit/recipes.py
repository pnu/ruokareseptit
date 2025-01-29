"""Published recipe listings
"""

from sqlite3 import Cursor

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
        with get_db() as db:
            page = int(request.args.get("page", 0))
            pub_recipes, remaining = list_published_recipes(db, page)
            context = {"recipes": pub_recipes}
            if remaining > 0:
                context["next_page"] = url_for("recipes.index", page=page + 1)
            if page > 0:
                context["prev_page"] = url_for("recipes.index", page=page - 1)
            return render_template("recipes/list.html", **context)

    with get_db() as db:
        recipe_context = fetch_published_recipe_context(db, recipe_id)
        if recipe_context is None:
            return redirect(url_for("recipes.index"))
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


# SQL queries for READ operations ########################################


def list_published_recipes(db: Cursor, page: int):
    """Query all published recipes, paginated. Returns a tuple of
    Cursor and number of remaining recipes after this page.
    """
    total_rows = db.execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE published = 1
        """).fetchone()[0]
    page_size = current_app.config["RECIPE_LIST_PAGE_SIZE"]
    offset = page * page_size
    pub_recipes = db.execute(
        """
        SELECT recipes.*, AVG(user_review.rating) AS rating
        FROM recipes LEFT JOIN user_review
        ON recipes.id = user_review.recipe_id
        WHERE published = 1
        GROUP BY recipes.id
        ORDER BY rating DESC
        LIMIT ? OFFSET ?
        """, [page_size, offset]
    )
    recipes_remaining = max(total_rows - offset - page_size, 0)
    return pub_recipes, recipes_remaining


def fetch_published_recipe_context(db: Cursor, recipe_id: int):
    """Fetch a recipe from database. The recipe must be
    published. Returns a dict to be used as a `render_template`
    context.
    """
    recipe_row = db.execute(
        """
        SELECT recipes.*, users.username
        FROM recipes
        JOIN users
        ON recipes.author_id = users.id
        WHERE recipes.id = ? AND published = 1
        """, [recipe_id]).fetchone()
    if recipe_row is None:
        return None

    related = fetch_recipe_related(db, recipe_id)
    return {"recipe": recipe_row, **related}


def fetch_recipe_related(db: Cursor, recipe_id):
    """Fetch content from related tables. Returns a dict of each
    key `ingredients`, `instructions`, `categories` and `user_reviews`.
    """
    ingredients_limit = current_app.config["RECIPE_INGREDIENTS_MAX"]
    ingredients = db.execute(
        """
        SELECT * FROM ingredients WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, ingredients_limit])

    instructions_limit = current_app.config["RECIPE_INSTRUCTIONS_MAX"]
    instructions = db.execute(
        """
        SELECT * FROM instructions WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, instructions_limit])

    categories_limit = current_app.config["RECIPE_CATEGORIES_MAX"]
    categories = db.execute(
        """
        SELECT categories.title
        FROM recipe_category
        JOIN categories
        ON recipe_category.category_id = categories.id
        WHERE recipe_category.recipe_id = ?
        LIMIT ?
        """, [recipe_id, categories_limit])

    user_reviews_limit = current_app.config["RECIPE_USER_REVIEWS_MAX"]
    user_reviews = db.execute(
        """
        SELECT user_review.*, users.username
        FROM user_review JOIN users ON user_review.user_id = users.id
        WHERE user_review.recipe_id = ?
        LIMIT ?
        """, [recipe_id, user_reviews_limit])

    return {
        "ingredients": ingredients,
        "instructions": instructions,
        "categories": categories,
        "user_reviews": user_reviews
    }
