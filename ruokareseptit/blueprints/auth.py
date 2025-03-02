"""User authentication
"""

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session

from ruokareseptit.model.db import get_db, log_db_error
from ruokareseptit.model.auth import auth_user_id, insert_user

bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder="templates")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Log in user
    """
    if request.method == "GET":
        username = request.args.get("username")
        return render_template("auth/login.html", username=username)

    next_url = request.args.get("next", url_for("home.index"))
    redir_params = {"next": next_url}
    with get_db() as db:
        username = request.form["username"]
        password = request.form["password"]
        user_id = auth_user_id(db, username, password)

    if user_id is None:
        flash_error("Väärä käyttäjätunnus tai salasana.")
        return redirect(url_for(".login", **redir_params))

    session.clear()
    session["uid"] = user_id
    flash("Kirjautuminen onnistui. Tervetuloa!")
    return redirect(next_url)


@bp.route("/logout")
def logout():
    """Log out user
    """
    session.clear()
    flash("Olet kirjautunut ulos.")
    return redirect(url_for("home.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration form
    """
    if request.method == "GET":
        username = request.args.get("username")
        return render_template("auth/register.html", username=username)

    username = request.form["username"]
    next_url = request.args.get("next", url_for("home.index"))
    redir_params = {"next": next_url}
    if validate_register_form(request.form) is False:
        return redirect(url_for(".register", **redir_params))

    try:
        with get_db() as db:
            password = request.form["password1"]
            insert_user(db, username, password)
    except db.Error as err:
        log_db_error(err)
        flash_error("Käyttäjätunnus on jo varattu.")
        return redirect(url_for(".register", **redir_params))

    flash("Käyttäjätunnus " + username + " on luotu.")
    redir_params["username"] = username
    return redirect(url_for(".login", **redir_params))


def validate_register_form(fields: dict[str, str]) -> bool:
    """Validate register form fields
    """
    username = fields.get("username")
    password1 = fields.get("password1")
    password2 = fields.get("password2")
    if len(username) < 4 or username.isalnum() is False:
        flash_error("Käyttäjätunnus ei ole vaatimusten mukainen.")
    elif len(password1) < 8:
        flash_error("Salasana ei ole vaatimusten mukainen.")
    elif username == password1:
        flash_error("Salasana ei voi olla sama kuin käyttätunnus.")
    elif password1 != password2:
        flash_error("Salasanat eivät täsmää.")
    else:
        return True
    return False


# Utility functions


def flash_error(message: str):
    """Flash form validation error
    """
    flash(message, "form_validation_error")
