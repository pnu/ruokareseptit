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
        SELECT user_reviews.*, recipes.title, recipes.published
        FROM user_reviews LEFT JOIN recipes
        ON user_reviews.recipe_id = recipes.id
        WHERE user_reviews.author_id = ?
        ORDER BY user_reviews.rating DESC
        LIMIT ? OFFSET ?
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
        SELECT user_reviews.*, recipes.title, recipes.published
        FROM user_reviews LEFT JOIN recipes
        ON user_reviews.recipe_id = recipes.id
        WHERE user_reviews.author_id = ?
        AND user_reviews.id = ?
        """, [author_id, recipe_id]).fetchone()

    if review_row:
        return {"review": review_row}
    return None

# SQL queries for authenticated CREATE / UPDATE operations ###############


def insert_review(db: Cursor, author_id: int, recipe_id: int):
    """Insert new review to database. Fields must include keys
    `title`, `summary` and `author_id`.
    """
    cursor = db.execute(
        """
        INSERT INTO user_reviews (author_id, recipe_id)
        VALUES (?, ?)
        """, [author_id, recipe_id])
    return cursor


def update_author_review(
        db: Cursor, review_id: int, author_id: int, fields: dict[str, str]):
    """Update review to database. Recipe author_id must match.
    """
    # Need to use "?" placeholders because some (or even all)
    # of the fields may be missing. Passing a dict and using named
    # parameters would raise an error about missing value.
    rating = fields.get("rating")
    review = fields.get("review")
    cursor = db.execute(
        """
        UPDATE user_reviews
        SET rating = IFNULL(?, rating),
        review = IFNULL(?, review)
        WHERE id = ? AND author_id = ?
        """, [rating, review, review_id, author_id])
    return cursor


def delete_author_review(db: Cursor, review_id: int, author_id: int):
    """Delete review from database. Recipe author_id must match.
    """
    cursor = db.execute(
        """
        DELETE FROM user_reviews
        WHERE id = ? and author_id = ?
        """, [review_id, author_id])
    return cursor
