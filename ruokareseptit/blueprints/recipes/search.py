"""Search recipes
"""

from flask import Blueprint
from flask import render_template
from flask import url_for
from flask import request

from ruokareseptit.model.db import get_db
from ruokareseptit.model.recipes import search_recipes_title

bp = Blueprint("search", __name__, url_prefix="/search",
               template_folder="templates")


@bp.route("/")
def index():
    """Contact page
    """
    search_term = request.args.get("q")
    if search_term and search_term != "":
        with get_db() as db:
            page = int(request.args.get("page", 0))
            recipes, count, pages = search_recipes_title(db, search_term, page)
            page = max(min(pages, page), 1)
            context = {"recipes": recipes, "recipes_count": count,
                       "search_term": search_term, "page_number": page,
                       "total_pages": pages}
            if page < pages:
                next_p = url_for(".index", q=search_term, page=page + 1)
                context["next_page"] = next_p
            if page > 1:
                prev_p = url_for(".index", q=search_term, page=page - 1)
                context["prev_page"] = prev_p
            return render_template("recipes/search/search.html", **context)
    context = {}
    return render_template("recipes/search/search.html", **context)
