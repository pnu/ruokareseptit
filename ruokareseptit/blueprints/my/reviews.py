"""Users' own reviews
"""

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import g
from flask import flash

from ruokareseptit.model.db import get_db, log_db_error
from ruokareseptit.model.auth import login_required
from ruokareseptit.model.reviews import list_user_reviews
from ruokareseptit.model.reviews import fetch_author_review_context
from ruokareseptit.model.recipes import fetch_published_recipe_context
from ruokareseptit.model.reviews import update_author_review
from ruokareseptit.model.reviews import delete_author_review


bp = Blueprint("reviews", __name__, url_prefix="/reviews",
               template_folder="templates")


@bp.route("/", defaults={"review_id": None})
@bp.route("/<int:review_id>")
@login_required
def index(review_id: int):
    """Own reviews
    """
    if not review_id:
        with get_db() as db:
            page = int(request.args.get("page", 0))
            rows, count, pages = list_user_reviews(db, g.user["id"], page)
            page = max(min(pages, page), 1)
            context = {"reviews": rows, "reviews_count": count,
                       "page_number": page, "total_pages": pages}
            if page < pages:
                next_p = url_for(".index", page=page + 1)
                context["next_page"] = next_p
            if page > 1:
                prev_p = url_for(".index", page=page - 1)
                context["prev_page"] = prev_p
            return render_template("my/reviews/list.html", **context)

    with get_db() as db:
        review_context = fetch_author_review_context(db, review_id,
                                                     g.user["id"])
        if not review_context:
            return redirect(url_for(".index"))

        recipe_id = review_context["review"]["recipe_id"]
        recipe_context = fetch_published_recipe_context(db, recipe_id)
        if recipe_context:
            review_context = {**review_context, **recipe_context}

        back = request.args.get("back", url_for(".index"))
        submit_url = url_for(".update", review_id=review_id, back=back)
        review_context["submit_url"] = submit_url
        return render_template("my/reviews/update.html", **review_context)


@bp.route("/update/<int:review_id>", methods=["POST"])
@login_required
def update(review_id: int):
    """Update review
    """
    edit_params = {
        "review_id": review_id,
        "back": request.args.get("back", "")
    }
    try:
        with get_db() as db:
            update_author_review(db, review_id, g.user["id"], request.form)
    except db.IntegrityError as err:
        log_db_error(err)
        flash("Arvostelun päivittäminen epäonnistui.")
        return redirect(url_for(".index", **edit_params))

    if request.form.get("return"):
        return redirect(request.args.get("back", url_for(".index")))

    if request.form.get("delete"):
        back = request.args.get("back", url_for(".index"))
        return redirect(url_for(
            ".delete", review_id=review_id, next=back))

    return redirect(url_for(".index", **edit_params))


@bp.route("/delete/<int:review_id>")
@login_required
def delete(review_id: int):
    """Delete recipe
    """
    try:
        with get_db() as db:
            c = delete_author_review(db, review_id, g.user["id"])
            if c.rowcount > 0:
                flash("Arvostelu on poistettu.")
    except db.Error as err:
        log_db_error(err)
        flash("Arvostelun poistaminen epäonnistui.", "error")

    return redirect(request.args.get("next", url_for(".index")))
