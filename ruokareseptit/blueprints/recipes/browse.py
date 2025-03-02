"""Published recipe listings
"""

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import g
from flask import flash

from ruokareseptit.model.db import get_db, log_db_error
from ruokareseptit.model.recipes import list_published_recipes
from ruokareseptit.model.recipes import fetch_published_recipe_context
from ruokareseptit.model.reviews import insert_review

bp = Blueprint("browse", __name__, url_prefix="/", template_folder="templates")


@bp.route("/", defaults={"recipe_id": None})
@bp.route("/<int:recipe_id>")
def index(recipe_id: int):
    """View published recipes
    """
    if not recipe_id:
        with get_db() as db:
            page = int(request.args.get("page", 1))
            recipes, count, pages = list_published_recipes(db, page)
            page = max(min(pages, page), 1)
            context = {"recipes": recipes, "recipes_count": count,
                       "page_number": page, "total_pages": pages}
            if page < pages:
                next_p = url_for(".index", page=page + 1)
                context["next_page"] = next_p
            if page > 1:
                prev_p = url_for(".index", page=page - 1)
                context["prev_page"] = prev_p
            return render_template("recipes/browse/list.html", **context)

    with get_db() as db:
        recipe_context = fetch_published_recipe_context(db, recipe_id)
        if recipe_context is None:
            return redirect(url_for(".index"))
        return render_template("recipes/browse/view.html", **recipe_context)


@bp.route("/<int:recipe_id>/review")
def review(recipe_id: int):
    """Add user review to a recipe
    """
    try:
        with get_db() as db:
            cursor = insert_review(db, g.user["id"], recipe_id)
            review_id = cursor.lastrowid
    except db.Error as err:
        log_db_error(err)
        flash("Arvostelun luominen epäonnistui.")
        return redirect(request.args.get("back", url_for(".index")))

    return redirect(url_for("my.reviews.index", review_id=review_id,
                            **request.args))
