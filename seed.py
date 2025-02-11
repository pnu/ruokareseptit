"""Generate random content to the database
"""
import random
import sqlite3
import string

db = sqlite3.connect("instance/ruokareseptit.sqlite")
db.execute("DELETE FROM users WHERE username like \"nobody_%\"")
db.execute("DELETE FROM users WHERE username like \"test_%\"")
db.execute("DELETE FROM recipes WHERE title like \"%[TEST]%\"")

def random_text_generator(n: int) -> str:
    """n random words
    """
    words = []
    for _ in range(n):
        word_length = random.randint(2, 10)
        word = ''.join(random.choice(string.ascii_letters) for _ in range(word_length))
        words.append(word)
    return " ".join(words)

def insert_random_recipe(author_id):
    """Insert a random recipe into the database
    """
    title = random_text_generator(random.randint(1, 5)) + " [TEST]"
    text_paragraphs = [random_text_generator(random.randrange(10, 50))
                       for _ in range(random.randint(1, 5))]
    summary = "\n\n".join(text_paragraphs)
    prep_time = random.randint(0, 120)
    cook_time = random.randint(0, 600)
    skill = random.randint(1,4)
    portions = random.randint(1, 20)
    pub = random.randint(0, 1)
    curs = db.execute(
        """
        INSERT INTO recipes (title, summary, preparation_time,
        cooking_time, skill_level, portions, published, author_id)
        VALUES (?,?,?,?,?,?,?,?)
        """, [title.title(), summary, prep_time, cook_time, skill, portions, pub, author_id])
    recipe_id = curs.lastrowid
    for i in range(random.randint(3,10)):
        db.execute(
            """
            INSERT INTO ingredients (recipe_id, order_number, amount, unit, title)
            VALUES (?,?,?,?,?)
            """,
            [recipe_id, i, random.randint(1, 15), random_text_generator(1),
             random_text_generator(random.randint(2, 5)).title()])
    for i in range(random.randint(3, 10)):
        text_paragraphs = [random_text_generator(random.randrange(10, 50))
                    for _ in range(random.randint(1, 3))]
        instructions = "\n\n".join(text_paragraphs)
        db.execute(
            """
            INSERT INTO instructions (recipe_id, order_number, instructions)
            VALUES (?,?,?)
            """, [recipe_id, i, instructions])

def add_user_review(user_id, recipe_id):
    """Give a random user review
    """
    text_paragraphs = [random_text_generator(random.randrange(10, 20))
                for _ in range(random.randint(1, 3))]
    review = "\n\n".join(text_paragraphs)
    rating = random.randint(1, 5)
    db.execute(
        """
        INSERT INTO user_review (user_id, recipe_id, rating, review)
        VALUES (?,?,?,?)
        """, [user_id, recipe_id, rating, review])

def main():
    """Create some testdata in the database
    """
    print("Creating empty users `nobody_N` where N is 1..1000000 ...")
    for i in range(1, 10**6 + 1):
        print(f"{i}/{10**6}                  ", end="\r")
        cur = db.execute("INSERT INTO users (username, password_hash) VALUES (?,?)",
                ["nobody_" + str(i), str(i)])
    print()

    print("Creating empty recipes `[TEST] N` where N is 1..1000000 ...")
    for i in range(1, 10**6 + 1):
        print(f"{i}/{10**6}                  ", end="\r")
        cur = db.execute(
            """
            INSERT INTO recipes (title, summary)
            VALUES (?,?)
            """, ["[TEST] " + str(i), "[TEST] " + str(i)])
    print()

    user_count = 10000
    print("Creating `test_N` users and 0..10 recipes with random content for each...")
    for i in range(1, user_count + 1):
        print(f"{i}/{user_count} ", end="")
        cur = db.execute("INSERT INTO users (username, password_hash) VALUES (?,?)",
                ["test_" + str(i), str(i)])
        user_id = cur.lastrowid
        for _ in range(random.randint(0, 10)):
            print(".", end="")
            insert_random_recipe(user_id)
        print("                     ", end="\r")
    print()
    rows = db.execute(
            """
            SELECT id from recipes
            WHERE title like "%[TEST]"
            AND published = 1
            """).fetchall()
    test_recipes = [row[0] for row in rows]
    print("Number of published test recipies:", len(test_recipes))
    print("Every `test_N` user will give 5..20 reviews with text to a random published recipe...")
    rows = db.execute(
            """
            SELECT id from users
            WHERE username like "test_%"
            """).fetchall()
    test_users = [row[0] for row in rows]
    n_users = len(test_users)
    for i, user in enumerate(test_users):
        print(f"{i + 1}/{n_users} ", end="")
        for _ in range(random.randint(5, 20)):
            print(".", end="")
            add_user_review(user, random.choice(test_recipes))
        print("                     ", end="\r")
    print()
    print("Every `nobody_N` user will give 0..5 numerical reviews (no text)...")
    rows = db.execute(
            """
            SELECT id from users
            WHERE username like "nobody_%"
            """).fetchall()
    nobody_users = [row[0] for row in rows]
    n_users = len(nobody_users)
    for i, user in enumerate(nobody_users):
        print(f"{i + 1}/{n_users}           ", end="\r")
        for _ in range(random.randint(0, 5)):
            rating = random.randint(1, 5)
            recipe_id = random.choice(test_recipes)
            db.execute(
                """
                INSERT INTO user_review (user_id, recipe_id, rating)
                VALUES (?,?,?)
                """, [user_id, recipe_id, rating])
    print()

    print("Commit and vacuum...")
    db.commit()
    db.execute("VACUUM")
    db.close()
    print("Thanks, bye.")


main()
