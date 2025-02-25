"""Published recipe listings
"""

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request

from ruokareseptit.model.db import get_db
from ruokareseptit.model.recipes import list_published_recipes
from ruokareseptit.model.recipes import fetch_published_recipe_context

from . import categories
from . import search

bp = Blueprint("recipes", __name__, url_prefix="/recipes", template_folder="templates")
bp.register_blueprint(categories.bp)
bp.register_blueprint(search.bp)


@bp.route("/", defaults={"recipe_id": None})
@bp.route("/<int:recipe_id>")
def index(recipe_id: int):
    """View published recipes
    """
    if recipe_id is None:
        with get_db() as db:
            page = int(request.args.get("page", 1))
            recipes, count, pages = list_published_recipes(db, page)
            page = max(min(pages, page), 1)
            context = {"recipes": recipes, "recipes_count": count,
                       "page_number": page, "total_pages": pages }
            if page < pages:
                context["next_page"] = url_for(".index", page=page + 1)
            if page > 1:
                context["prev_page"] = url_for(".index", page=page - 1)
            return render_template("recipes/list.html", **context)

    with get_db() as db:
        recipe_context = fetch_published_recipe_context(db, recipe_id)
        if recipe_context is None:
            return redirect(url_for(".index"))
        return render_template("recipes/view.html", **recipe_context)
