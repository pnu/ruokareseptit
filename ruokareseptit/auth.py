"""User authentication
"""

import functools

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

    username = request.form["username"]
    password = request.form["password"]
    user_in_db = auth_user(username, password)

    if user_in_db is None:
        flash_error("Väärä käyttäjätunnus tai salasana.")
        return render_template("auth/login.html")

    session.clear()
    session["uid"] = user_in_db["id"]
    next_url = request.args.get("next", url_for("home.index"))
    flash("Kirjautuminen onnistui. Tervetuloa!")
    return redirect(next_url)


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
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if not valid_username(username):
        flash_error("Käyttäjätunnus ei ole vaatimusten mukainen.")
        username = None
    elif not strong_password(password1):
        flash_error("Salasana ei ole vaatimusten mukainen.")
    elif username == password1:
        flash_error("Salasana ei voi olla sama kuin käyttätunnus.")
    elif password1 != password2:
        flash_error("Salasanat eivät täsmää.")
    elif insert_user(username, password1) is None:
        flash_error("Käyttäjätunnus " + username + " on jo varattu.")
        username = None
    else:
        flash("Käyttäjätunnus " + username + " on luotu.")
        next_url = request.args.get("next", url_for("home.index"))
        return redirect(url_for(
            "auth.login", next=next_url, username=username
        ))

    return render_template("auth/register.html", username=username)

# Utility functions


def flash_error(message: str):
    """Flash form validation error
    """
    flash(message, "form_validation_error")


def strong_password(password: str) -> bool:
    """Check if password is strong enough
    """
    return len(password) >= 8


def valid_username(username: str) -> bool:
    """Check if username is valid
    """
    return len(username) >= 4 and username.isalnum()


def insert_user(username: str, password: str) -> int:
    """Insert new user to database. Return uid if successful,
    None otherwise.
    """
    try:
        with get_db() as db:
            res = db.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """, [username, generate_password_hash(password)])
            return res.lastrowid
    except db.IntegrityError:
        return None


def auth_user(username: str, password: str) -> dict | None:
    """Authenticate user
    """
    user = get_db().execute(
        """
        SELECT id, password_hash
        FROM users
        WHERE username = ?
        """, [username]).fetchone()

    if user is None:
        return None
    if current_app.config["ALLOW_ANY_PASSWORD"]:
        # Allows login with any password, only for testing
        return user

    return check_password_hash(user["password_hash"], password)
