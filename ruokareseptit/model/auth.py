""" Authentication related handlers and SQL queries
"""

import functools
from sqlite3 import Cursor

from flask import redirect
from flask import url_for
from flask import g
from flask import request
from flask import session
from flask import current_app
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from ruokareseptit.model.db import get_db


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


def register_before_request(app):
    """Register before request action
    """
    @app.before_request
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


# SQL queries for READ operations ########################################


def auth_user_id(db: Cursor, username: str, password: str) -> int | None:
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


# SQL queries for CREATE / UPDATE operations #############################


def insert_user(db: Cursor, username: str, password: str):
    """Insert new user to database.
    """
    cursor = db.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?, ?)
        """, [username, generate_password_hash(password)])
    return cursor
