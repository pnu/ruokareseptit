"""User edit pages and features
"""

from flask import Blueprint
from flask import render_template
from flask import g
from flask import url_for
from flask import request
from flask import flash
from flask import redirect

from ruokareseptit.model.db import get_db
from ruokareseptit.model.auth import login_required
from ruokareseptit.model.recipes import list_user_recipes
from ruokareseptit.model.recipes import fetch_author_recipe_context
from ruokareseptit.model.recipes import insert_recipe
from ruokareseptit.model.recipes import update_author_recipe
from ruokareseptit.model.recipes import update_recipe_ingredients
from ruokareseptit.model.recipes import update_recipe_instructions
from ruokareseptit.model.recipes import delete_author_recipe

bp = Blueprint("recipes", __name__, url_prefix="/recipes", template_folder="templates")


@bp.route("/", defaults={"recipe_id": None, "tab": None})
@bp.route("/<int:recipe_id>", defaults={"tab": 1})
@bp.route("/<int:recipe_id>/", defaults={"tab": 1})
@bp.route("/<int:recipe_id>/<int:tab>")
@login_required
def index(recipe_id: int, tab: int):
    """Own recipes
    """
    if recipe_id is None:
        with get_db() as db:
            page = int(request.args.get("page", 0))
            rows, count, pages = list_user_recipes(db, g.user["id"], page)
            page = max(min(pages, page), 1)
            context = {"recipes": rows, "recipes_count": count,
                       "page_number": page, "total_pages": pages }
            if page < pages:
                context["next_page"] = url_for(".index", page=page + 1)
            if page > 1:
                context["prev_page"] = url_for(".index", page=page - 1)
            return render_template("my/recipes/list.html", **context)

    with get_db() as db:
        recipe_context = fetch_author_recipe_context(db, recipe_id, g.user["id"])
        if recipe_context is None:
            return redirect(url_for(".index"))

        back = request.args.get("back", url_for(".index"))
        submit_url = url_for(".update", recipe_id=recipe_id,
                             tab=tab, back=back)
        recipe_context["submit_url"] = submit_url
        tmpl = ["main", "ingredients", "instructions"][tab - 1]
        return render_template("my/recipes/update/" + tmpl + ".html", **recipe_context)


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create new recipe
    """
    if request.method == "GET":
        return render_template("my/recipes/create.html", **request.args)

    recipe_id = None
    if validate_create_form(request.form) is False:
        return redirect(url_for(".create", **request.form))

    try:
        with get_db() as db:
            cursor = insert_recipe(db, g.user["id"], request.form)
            recipe_id = cursor.lastrowid
    except db.IntegrityError:
        flash("Reseptin luonti epäonnistui.")
        return redirect(url_for(".create", **request.form))

    flash("Uusi resepti on luotu.")
    return redirect(url_for(".index", recipe_id=recipe_id))


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


@bp.route("/update/<int:recipe_id>", methods=["POST"])
@login_required
def update(recipe_id: int):
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
            update_recipe_instructions(db, recipe_id, request.form)
    except db.IntegrityError:
        flash("Reseptin päivittäminen epäonnistui.")
        return redirect(url_for(".index", **edit_params))

    if request.form.get("return"):
        return redirect(request.args.get("back", url_for(".index")))

    if request.form.get("delete"):
        back = request.args.get("back", url_for(".index"))
        return redirect(url_for(
            ".delete", recipe_id=recipe_id, next=back))

    edit_params["tab"] = int(request.form.get("tab", edit_params["tab"]))
    return redirect(url_for(".index", **edit_params))


@bp.route("/delete/<int:recipe_id>")
@login_required
def delete(recipe_id: int):
    """Delete recipe
    """
    try:
        with get_db() as db:
            c = delete_author_recipe(db, recipe_id, g.user["id"])
            if c.rowcount > 0:
                flash("Resepti on poistettu.")
    except db.IntegrityError:
        flash("Reseptin poistaminen epäonnistui.", "error")

    return redirect(request.args.get("next", url_for(".index")))


# Utility functions ######################################################


def flash_error(message: str):
    """Flash form validation error
    """
    flash(message, "form_validation_error")
