"""Database connection and utilities
"""

import sqlite3
from datetime import datetime
import click
from flask import current_app
from flask import g


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        if current_app.debug:
            g.db.set_trace_callback(print)
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Close the connection.
    """
    if e is not None:
        print("Unhandled exception:", e)
    db = g.pop("db", None)
    if db is not None:
        db.close()


def log_db_error(err: sqlite3.Error):
    """Log database error
    """
    print(f"Database error: {err.sqlite_errorcode} {err.sqlite_errorname}")


def init_db():
    """Clear existing data and create new tables.
    """
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables.
    """
    init_db()
    click.echo("Initialized the database.")


sqlite3.register_converter(
    "timestamp",
    lambda v: datetime.fromisoformat(v.decode())
)


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
