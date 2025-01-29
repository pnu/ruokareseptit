"""User authentication
"""

import functools
from sqlite3 import Connection

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from flask import g
from flask import current_app
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


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
        return redirect(url_for("auth.login", **redir_params))

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
        return redirect(url_for("auth.register", **redir_params))

    try:
        with get_db() as db:
            password = request.form["password1"]
            insert_user(db, username, password)
    except db.IntegrityError:
        flash_error("Käyttäjätunnus " + username + " on jo varattu.")
        return redirect(url_for("auth.register", **redir_params))

    flash("Käyttäjätunnus " + username + " on luotu.")
    redir_params["username"] = username
    return redirect(url_for("auth.login", **redir_params))


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


# Flask request handling, context processors and decorators


@bp.before_app_request
def g_user():
    """Set g.user if logged in. Clear session if user
    has been deleted from db.
    """
    if session.get("uid") is None:
        g.user = None
        return
    uid = session.get("uid")
    user_in_db = get_db().execute(
        """
        SELECT id, username
        FROM users
        WHERE id = ?
        """, [uid]).fetchone()
    if user_in_db is None:
        session.clear()
    g.user = user_in_db


def login_required(view):
    """View decorator to check if user is logged in.
    Redirects to the login page if not.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.url))
        return view(**kwargs)
    return wrapped_view


# Utility functions


def flash_error(message: str):
    """Flash form validation error
    """
    flash(message, "form_validation_error")


# SQL queries for CREATE / UPDATE operations #############################


def insert_user(db: Connection, username: str, password: str):
    """Insert new user to database.
    """
    cursor = db.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?, ?)
        """, [username, generate_password_hash(password)])
    return cursor


# SQL queries for READ operations ########################################


def auth_user_id(db: Connection, username: str, password: str) -> int | None:
    """Return user id for username if password is correct.
    """
    user: dict[str, any] = db.execute(
        """
        SELECT id, username, password_hash
        FROM users
        WHERE username = ?
        """, [username]).fetchone()
    if user is None:
        return None
    if current_app.debug:
        # In debug mode accept any password
        return user["id"]
    if check_password_hash(user["password_hash"], password) is False:
        return None
    return user["id"]
