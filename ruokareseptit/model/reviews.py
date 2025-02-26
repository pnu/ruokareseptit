""" SQL queries for recipes
"""

from sqlite3 import Cursor
from flask import current_app


# SQL queries for authenticated READ operations ##########################


def list_user_reviews(db: Cursor, author_id: int, page: int):
    """Query reviews of user `author_id`
    """
    total_rows = db.execute(
        """
        SELECT count(*)
        FROM user_reviews
        WHERE author_id = ?
        """, [author_id]).fetchone()[0]
    page_size = int(current_app.config["REVIEW_LIST_PAGE_SIZE"])
    total_pages = (total_rows - 1) // page_size + 1
    offset = max(min(total_pages - 1, page - 1), 0) * page_size
    user_reviews = db.execute(
        """
        SELECT *
        FROM user_reviews
        WHERE author_id = ? LIMIT ? OFFSET ?
        """, [author_id, page_size, offset]
    )
    return user_reviews, total_rows, total_pages


def fetch_author_review_context(db: Cursor, recipe_id: int, author_id: int):
    """Fetch a review from database. The review `author_id` in
    databse must match the `author_id` passed. Returns a dict
    to be used as a `render_template` context.
    """
    review_row = db.execute(
        """
        SELECT *
        FROM user_reviews
        WHERE id = ? AND author_id = ?
        """, [recipe_id, author_id]).fetchone()

    if review_row is None:
        return None

    return {"review": review_row}
