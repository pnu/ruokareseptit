"""User authentication"""

from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.security import generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/register")
def register():
    """Registration form"""
    return render_template("auth/register.html")

@bp.route("/register", methods=["POST"])
def register_submit():
    """Registration form submit"""
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

def flash_error(message: str):
    """Flash form validation error"""
    flash(message, "form_validation_error")

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

def strong_password(password: str) -> bool:
    """Check if password is strong enough"""
    return len(password) >= 8

def valid_username(username: str) -> bool:
    """Check if username is valid"""
    return len(username) >= 4 and username.isalnum()
