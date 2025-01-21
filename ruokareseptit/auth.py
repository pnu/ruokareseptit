"""User authentication"""

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET","POST"])
def login():
    """Login form"""
    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form["username"]
    password = request.form["password"]
    user = auth_user(username, password)

    if user is None:
        flash_error("Väärä käyttäjätunnus tai salasana.")
        return render_template("auth/login.html")

    session.clear()
    session["user_id"] = user["id"]
    flash(f"Kirjautuminen onnistui. Tervetuloa, {user['username']}!")
    return redirect(url_for("home.index"))

@bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration form"""
    if request.method == "GET":
        return render_template("auth/register.html")

    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if not valid_username(username):
        flash_error("Käyttäjätunnus ei ole vaatimusten mukainen.")
    elif not strong_password(password1):
        flash_error("Salasana ei ole vaatimusten mukainen.")
    elif username == password1:
        flash_error("Salasana ei voi olla sama kuin käyttätunnus.")
    elif password1 != password2:
        flash_error("Salasanat eivät täsmää.")
    elif not insert_user(username, password1):
        flash_error("Käyttäjätunnus on jo varattu.")
    else:
        flash(f"Uusi käyttäjätunnus '{username}' on luotu. Voit nyt kirjautua palveluun.")
        return redirect(url_for("home.index"))

    return render_template("auth/register.html")

## Utility functions

def flash_error(message: str):
    """Flash form validation error"""
    flash(message, "form_validation_error")

def strong_password(password: str) -> bool:
    """Check if password is strong enough"""
    return len(password) >= 8

def valid_username(username: str) -> bool:
    """Check if username is valid"""
    return len(username) >= 4 and username.isalnum()

def insert_user(username: str, password: str) -> bool:
    """Insert new user to database. Return True if successful, False otherwise."""
    try:
        db = get_db()
        db.execute(
            "INSERT INTO user (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
        return True
    except db.IntegrityError:
        return False

def auth_user(username: str, password: str) -> dict | None:
    """Authenticate user"""
    user = get_db().execute("SELECT * FROM user WHERE username = ?", [username]).fetchone()

    if user is None:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None

    return user
