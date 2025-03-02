""" SQL queries for recipes
"""

import re
from sqlite3 import Cursor
from flask import current_app


# SQL queries for READ operations ########################################


def search_recipes_title(db: Cursor, search_term: str, page: int):
    """Search all published recipes, paginated. Returns a tuple of
    Cursor, number of recipes and number of pages.
    """
    search_term = "%" + search_term + "%"
    total_rows: int = db.execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE published = 1
        AND title LIKE ?
        """, [search_term]).fetchone()[0]
    page_size = int(current_app.config["RECIPE_LIST_PAGE_SIZE"])
    total_pages = (total_rows - 1) // page_size + 1
    offset = max(min(total_pages - 1, page - 1), 0) * page_size
    pub_recipes = db.execute(
        """
        SELECT recipes.*, AVG(user_reviews.rating) AS rating,
        COUNT(user_reviews.rating) AS rating_count
        FROM recipes LEFT JOIN user_reviews
        ON recipes.id = user_reviews.recipe_id
        WHERE published = 1
        AND title LIKE ?
        GROUP BY recipes.id
        ORDER BY rating DESC
        LIMIT ? OFFSET ?
        """, [search_term, page_size, offset]
    )
    return pub_recipes, total_rows, total_pages


def list_published_recipes(db: Cursor, page: int):
    """Query all published recipes, paginated. Returns a tuple of
    Cursor, number of recipes and number of pages.
    """
    total_rows: int = db.execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE published = 1
        """).fetchone()[0]
    page_size = int(current_app.config["RECIPE_LIST_PAGE_SIZE"])
    total_pages = (total_rows - 1) // page_size + 1
    offset = max(min(total_pages - 1, page - 1), 0) * page_size
    pub_recipes = db.execute(
        """
        SELECT recipes.*, AVG(user_reviews.rating) AS rating,
        COUNT(user_reviews.rating) AS rating_count
        FROM recipes LEFT JOIN user_reviews
        ON recipes.id = user_reviews.recipe_id
        WHERE published = 1
        GROUP BY recipes.id
        ORDER BY rating DESC
        LIMIT ? OFFSET ?
        """, [page_size, offset]
    )
    return pub_recipes, total_rows, total_pages


def fetch_published_recipe_context(db: Cursor, recipe_id: int):
    """Fetch a recipe from database. The recipe must be
    published. Returns a dict to be used as a `render_template`
    context.
    """
    recipe_row = db.execute(
        """
        SELECT recipes.*, users.username, AVG(user_reviews.rating) AS rating,
        COUNT(user_reviews.rating) AS rating_count
        FROM recipes LEFT JOIN user_reviews
        ON recipes.id = user_reviews.recipe_id
        JOIN users
        ON recipes.author_id = users.id
        WHERE recipes.id = ? AND published = 1
        """, [recipe_id]).fetchone()
    if recipe_row["title"] is None:
        # have to check for title nullness because row is returned and it has
        # rating_count (0) even for recipies that do not exist in the database
        return None

    related = fetch_recipe_related(db, recipe_id)
    return {"recipe": recipe_row, **related}


def fetch_recipe_related(db: Cursor, recipe_id):
    """Fetch content from related tables. Returns a dict of each
    key `ingredients`, `instructions`, `categories` and `user_reviews`.
    """
    ingredients_limit = current_app.config["RECIPE_INGREDIENTS_MAX"]
    ingredients = db.execute(
        """
        SELECT * FROM ingredients WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, ingredients_limit])

    instructions_limit = current_app.config["RECIPE_INSTRUCTIONS_MAX"]
    instructions = db.execute(
        """
        SELECT * FROM instructions WHERE recipe_id = ?
        ORDER BY order_number LIMIT ?
        """, [recipe_id, instructions_limit])

    recipe_categories_limit = current_app.config["RECIPE_CATEGORIES_MAX"]
    recipe_categories = db.execute(
        """
        SELECT categories.title
        FROM recipe_category
        JOIN categories
        ON recipe_category.category_id = categories.id
        WHERE recipe_category.recipe_id = ?
        LIMIT ?
        """, [recipe_id, recipe_categories_limit])

    reviews_limit = current_app.config["RECIPE_USER_REVIEWS_MAX"]
    reviews = db.execute(
        """
        SELECT user_reviews.*, users.username
        FROM user_reviews JOIN users ON user_reviews.author_id = users.id
        WHERE user_reviews.recipe_id = ?
        ORDER BY user_reviews.review IS NOT NULL DESC
        LIMIT ?
        """, [recipe_id, reviews_limit])

    return {
        "ingredients": ingredients,
        "instructions": instructions,
        "categories": recipe_categories,
        "reviews": reviews
    }


# SQL queries for authenticated READ operations ##########################


def list_user_recipes(db: Cursor, author_id: int, page: int):
    """Query recipes of user `author_id`
    """
    total_rows = db.execute(
        """
        SELECT count(*)
        FROM recipes
        WHERE author_id = ?
        """, [author_id]).fetchone()[0]
    page_size = int(current_app.config["RECIPE_LIST_PAGE_SIZE"])
    total_pages = (total_rows - 1) // page_size + 1
    offset = max(min(total_pages - 1, page - 1), 0) * page_size
    user_recipes = db.execute(
        """
        SELECT *
        FROM recipes
        WHERE author_id = ? LIMIT ? OFFSET ?
        """, [author_id, page_size, offset]
    )
    return user_recipes, total_rows, total_pages


def fetch_author_recipe_context(db: Cursor, recipe_id: int, author_id: int):
    """Fetch a recipe from database. The recipe `author_id` in
    databse must match the `author_id` passed. Returns a dict
    to be used as a `render_template` context.
    """
    recipe_row = db.execute(
        """
        SELECT *
        FROM recipes
        WHERE id = ? AND author_id = ?
        """, [recipe_id, author_id]).fetchone()
    if recipe_row is None:
        return None

    related = fetch_recipe_related(db, recipe_id)
    return {"recipe": recipe_row, **related}


# Helper functions for mapping form data to SQL operations ###############


def update_recipe_ingredients(
        db: Cursor, recipe_id: int, fields: dict[str, str]):
    """Update all ingredients values from form keys eg.
    `ingredients_ID_amount` and `ingredients_ID_title`.
    Triggers also move, delete and add row actions.
    """
    ingredient_data = {}
    for key in fields:
        field = re.match(r"^ingredients_(\d+)_(\w+)$", key)
        if field is not None:
            i_id = field.group(1)
            column = field.group(2)
            value = fields[key]
            if column == "up":
                move_ingredients_row_up(db, recipe_id, i_id)
            elif column == "down":
                move_ingredients_row_down(db, recipe_id, i_id)
            elif column == "delete":
                delete_ingredients_row(db, recipe_id, i_id)
            else:
                if i_id not in ingredient_data:
                    ingredient_data[i_id] = {}
                ingredient_data[i_id][column] = value

    for i_id, i_fields in ingredient_data.items():
        update_ingredients_row(db, recipe_id, i_id, i_fields)

    if fields.get("ingredients_add_row", False):
        add_ingredients_row(db, recipe_id)


def update_recipe_instructions(
        db: Cursor, recipe_id: int, fields: dict[str, str]):
    """Update all instructions text from form keys eg.
    `instructions_ID_instruction`. Triggers also move,
    delete and add row actions.
    """
    instruction_data = {}
    for key in fields:
        field = re.match(r"^instructions_(\d+)_(\w+)$", key)
        if field is not None:
            i_id = field.group(1)
            column = field.group(2)
            value = fields[key]
            if column == "up":
                move_instructions_row_up(db, recipe_id, i_id)
            elif column == "down":
                move_instructions_row_down(db, recipe_id, i_id)
            elif column == "delete":
                delete_instructions_row(db, recipe_id, i_id)
            else:
                if i_id not in instruction_data:
                    instruction_data[i_id] = {}
                instruction_data[i_id][column] = value

    for i_id, i_fields in instruction_data.items():
        update_instructions_row(db, recipe_id, i_id, i_fields)

    if fields.get("instructions_add_row", False):
        add_instructions_row(db, recipe_id)


# SQL queries for authenticated CREATE / UPDATE operations ###############


def insert_recipe(db: Cursor, author_id: int, fields: dict[str, str]):
    """Insert new recipe to database. Fields must include keys
    `title`, `summary` and `author_id`.
    """
    fields = {**fields, "author_id": author_id}
    cursor = db.execute(
        """
        INSERT INTO recipes (title, summary, author_id)
        VALUES (:title, :summary, :author_id)
        """, fields)
    return cursor


def update_author_recipe(
        db: Cursor, recipe_id: int, author_id: int, fields: dict[str, str]):
    """Update recipe to database. Recipe author_id must match.
    """
    # Need to use "?" placeholders because some (or even all)
    # of the fields may be missing. Passing a dict and using named
    # parameters would raise an error about missing value.
    title = fields.get("title")
    summary = fields.get("summary")
    preparation_time = fields.get("preparation_time")
    cooking_time = fields.get("cooking_time")
    skill_level = fields.get("skill_level")
    portions = fields.get("portions")
    # For checkbox `published` we need to distinguish between
    # cases when checkbox is not checked vs. it's not part
    # of the form.
    is_pub_default = fields.get("published.default")
    published = fields.get("published", is_pub_default)
    cursor = db.execute(
        """
        UPDATE recipes
        SET title = IFNULL(?, title),
        summary = IFNULL(?, summary),
        preparation_time = IFNULL(?, preparation_time),
        cooking_time = IFNULL(?, cooking_time),
        skill_level = IFNULL(?, skill_level),
        portions = IFNULL(?, portions),
        published = IFNULL(?, published)
        WHERE id = ? AND author_id = ?
        """, (title, summary, preparation_time,
        cooking_time, skill_level, portions, published,
        recipe_id, author_id))
    return cursor


def delete_author_recipe(db: Cursor, recipe_id: int, author_id: int):
    """Delete recipe from database. Recipe author_id must match.
    """
    cursor = db.execute(
        """
        DELETE FROM recipes
        WHERE id = ? and author_id = ?
        """, [recipe_id, author_id])
    return cursor


def add_ingredients_row(db: Cursor, recipe_id: int):
    """Add ingredients row to recipe
    """
    cursor = db.execute(
        """
        INSERT INTO ingredients (recipe_id, order_number)
        SELECT ?, IFNULL(MAX(order_number), 0) + 1
        FROM ingredients
        WHERE recipe_id = ?
        """, [recipe_id, recipe_id])
    return cursor


def delete_ingredients_row(db: Cursor, recipe_id: int, ingredient_id: int) -> bool:
    """Delete s ingredients row from a recipe
    """
    cursor = db.execute(
        """
        DELETE FROM ingredients
        WHERE recipe_id = ? AND id = ?
        """, [recipe_id, ingredient_id])
    return cursor


def update_ingredients_row(
        db: Cursor, recipe_id: int, i_id: int, fields: dict[str, str]) -> bool:
    """Update specific ingredients row. Fields must contain keys
    `amount`, `unit` and `title`.
    """
    fields = {**fields, "recipe_id": recipe_id, "i_id": i_id}
    cursor = db.execute(
        """
        UPDATE ingredients
        SET (amount,  unit,  title)
         = (:amount, :unit, :title)
        WHERE recipe_id = :recipe_id AND id = :i_id
        """, fields)
    return cursor


def move_ingredients_row_up(db: Cursor, recipe_id: int, ingredient_id: int) -> bool:
    """Move ingredient up by swapping order_number values
    with the previous ingredient (in order of appearance).
    """
    cursor = db.execute(
        """
        UPDATE ingredients SET order_number = CASE
        WHEN ingredients.id = prev_id THEN this.order_number
        WHEN ingredients.id = this.id THEN prev_order_number
        END FROM ingredients AS this, (SELECT id,
            lag(id) OVER (ORDER BY order_number) AS prev_id,
            lag(order_number) OVER (ORDER BY order_number) AS prev_order_number
            FROM ingredients WHERE recipe_id = ?) AS prev
        WHERE this.id = prev.id
        AND this.id = ?
        AND ingredients.id IN (this.id, prev_id);
        """, [recipe_id, ingredient_id])
    return cursor


def move_ingredients_row_down(db: Cursor, recipe_id: int, ingredient_id: int) -> bool:
    """Move ingredient down by swapping order_number values
    with the next ingredient (in order of appearance).
    """
    cursor = db.execute(
        """
        UPDATE ingredients SET order_number = CASE
        WHEN ingredients.id = next_id THEN this.order_number
        WHEN ingredients.id = this.id THEN next_order_number
        END FROM ingredients AS this, (SELECT id,
            lead(id) OVER (ORDER BY order_number) AS next_id,
            lead(order_number) OVER (ORDER BY order_number) AS next_order_number
            FROM ingredients WHERE recipe_id = ?) AS next
        WHERE this.id = next.id
        AND this.id = ?
        AND ingredients.id IN (this.id, next_id);
        """, [recipe_id, ingredient_id])
    return cursor


def add_instructions_row(db: Cursor, recipe_id: int):
    """Add instructions row to recipe
    """
    cursor = db.execute(
        """
        INSERT INTO instructions (recipe_id, order_number)
        SELECT ?, IFNULL(MAX(order_number), 0) + 1
        FROM instructions
        WHERE recipe_id = ?
        """, [recipe_id, recipe_id])
    return cursor


def delete_instructions_row(db: Cursor, recipe_id: int, instruction_id: int) -> bool:
    """Delete s instructions row from a recipe
    """
    cursor = db.execute(
        """
        DELETE FROM instructions
        WHERE recipe_id = ? AND id = ?
        """, [recipe_id, instruction_id])
    return cursor


def update_instructions_row(
        db: Cursor, recipe_id: int, i_id: int, fields: dict[str, str]) -> bool:
    """Update specific instructions row. Fields must contain key
    `instructions`.
    """
    fields = {**fields, "recipe_id": recipe_id, "i_id": i_id}
    cursor = db.execute(
        """
        UPDATE instructions
        SET (instructions)
         = (:instructions)
        WHERE recipe_id = :recipe_id AND id = :i_id
        """, fields)
    return cursor


def move_instructions_row_up(db: Cursor, recipe_id: int, instruction_id: int) -> bool:
    """Move instruction up by swapping order_number values
    with the previous instruction (in order of appearance).
    """
    cursor = db.execute(
        """
        UPDATE instructions SET order_number = CASE
        WHEN instructions.id = prev_id THEN this.order_number
        WHEN instructions.id = this.id THEN prev_order_number
        END FROM instructions AS this, (SELECT id,
            lag(id) OVER (ORDER BY order_number) AS prev_id,
            lag(order_number) OVER (ORDER BY order_number) AS prev_order_number
            FROM instructions WHERE recipe_id = ?) AS prev
        WHERE this.id = prev.id
        AND this.id = ?
        AND instructions.id IN (this.id, prev_id);
        """, [recipe_id, instruction_id])
    return cursor


def move_instructions_row_down(db: Cursor, recipe_id: int, instruction_id: int) -> bool:
    """Move instruction down by swapping order_number values
    with the next instruction (in order of appearance).
    """
    cursor = db.execute(
        """
        UPDATE instructions SET order_number = CASE
        WHEN instructions.id = next_id THEN this.order_number
        WHEN instructions.id = this.id THEN next_order_number
        END FROM instructions AS this, (SELECT id,
            lead(id) OVER (ORDER BY order_number) AS next_id,
            lead(order_number) OVER (ORDER BY order_number) AS next_order_number
            FROM instructions WHERE recipe_id = ?) AS next
        WHERE this.id = next.id
        AND this.id = ?
        AND instructions.id IN (this.id, next_id);
        """, [recipe_id, instruction_id])
    return cursor
