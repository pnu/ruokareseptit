"""Generate random content to the database
"""
import csv
import random
import sqlite3
import urllib.request
import os

db = sqlite3.connect("instance/ruokareseptit.sqlite")

SANA_URL = "https://kaino.kotus.fi/lataa/nykysuomensanalista2024.csv"
SANA_FILENAME = "instance/nykysuomensanalista2024.csv"
if not os.path.isfile(SANA_FILENAME):
    print("Fetching", SANA_URL, "...")
    urllib.request.urlretrieve(SANA_URL, SANA_FILENAME)

sanasto = []
substantiivit = []
with open(SANA_FILENAME, encoding="utf-8", newline="") as csvfile:
    sana_rows = csv.reader(csvfile, delimiter="\t")
    for row in sana_rows:
        hakusana = row[0]
        sanasto.append(hakusana)
        if "substantiivi" in row[2]:
            substantiivit.append(hakusana)

categories = [x.capitalize() for x in random.choices(substantiivit, k=20)]

def random_title() -> str:
    """Generate random title of 1..3 words
    """
    k = random.randint(1, 3)
    w = random.choices(sanasto, k=k)
    w[0] = w[0].title()
    return " ".join(w)

def random_noun() -> str:
    """Random noun
    """
    return random.choice(substantiivit)

def random_sentences(n: int) -> str:
    """Generate n random sentences
    """
    all_words = []
    for _ in range(n):
        k = random.randint(2, 10)
        w = random.choices(sanasto, k=k)
        w[0] = w[0].title()
        w[-1] += "."
        all_words.extend(w)
    return " ".join(all_words)

def random_paragraph(n: int) -> str:
    """Generate n random paragraphs
    """
    p = []
    for _ in range(n):
        p.append(random_sentences(random.randint(3,10)))
    return "\n\n".join(p)

def insert_random_recipe(author_id):
    """Insert a random recipe into the database
    """
    title = random_title() + " [TEST]"
    summary = random_paragraph(random.randint(1,3))
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
        """, [title, summary, prep_time, cook_time, skill, portions, pub, author_id])
    recipe_id = curs.lastrowid
    for i in range(random.randint(3,10)):
        db.execute(
            """
            INSERT INTO ingredients (recipe_id, order_number, amount, unit, title)
            VALUES (?,?,?,?,?)
            """,
            [recipe_id, i, random.randint(1, 15), random_noun(), random_title()])
    for i in range(random.randint(3, 10)):
        instructions = random_paragraph(random.randint(1,2))
        db.execute(
            """
            INSERT INTO instructions (recipe_id, order_number, instructions)
            VALUES (?,?,?)
            """, [recipe_id, i, instructions])
    for i in range(random.randint(0, 6)):
        category = random.choice(categories)
        db.execute(
            """
            INSERT INTO categories (title)
            VALUES (?) ON CONFLICT DO NOTHING
            """, [category])
        cid = db.execute(
            """
            SELECT id FROM categories
            WHERE title = ?
            """, [category]).fetchone()[0]
        db.execute(
            """
            INSERT INTO recipe_category (recipe_id, category_id)
            VALUES (?,?) ON CONFLICT DO NOTHING
            """, [recipe_id, cid])
    return recipe_id

def add_user_review(user_id, recipe_id):
    """Give a random user review
    """
    review = random_paragraph(random.randint(1,3))
    rating = random.randint(1, 5)
    db.execute(
        """
        INSERT INTO user_reviews (author_id, recipe_id, rating, review)
        VALUES (?,?,?,?)
        """, [user_id, recipe_id, rating, review])

def main():
    """Create some testdata in the database
    """
    test_users = []
    test_recipes = []
    start_from_user_id = db.execute("SELECT IFNULL(MAX(id),0) from users").fetchone()[0]
    i_0 = start_from_user_id + 1
    i_n = i_0 + 10000
    print(f"Creating 10000 users `test_N` where N is {i_0}..{i_n - 1} and 0..10 recipes for each...")
    for i in range(i_0, i_n):
        print(f"test_{i} ", end="")
        db.execute("INSERT INTO users (id, username, password_hash) VALUES (?,?,?)",
                   [i, "test_" + str(i), ""])
        test_users.append(i)
        for _ in range(random.randint(0, 10)):
            print(".", end="")
            recipe_id = insert_random_recipe(i)
            test_recipes.append(recipe_id)
        print(" " * 10, end="\r")
    print("Number of new test recipies:", len(test_recipes))

    print("Every new `test_N` user gives 5..20 reviews...")
    for i, user in enumerate(test_users):
        print(f"{i + 1}/{len(test_users)} ", end="")
        for _ in range(random.randint(5, 20)):
            print(".", end="")
            add_user_review(user, random.choice(test_recipes))
        print(" " * 20, end="\r")

    nobody_users = []
    start_from_user_id = db.execute("SELECT max(id) from users").fetchone()[0]
    i_0 = start_from_user_id + 1
    i_n = i_0 + 10**6
    print(f"Creating 10**6 empty users `nobody_N` where N is {i_0}..{i_n - 1} ...")
    for i in range(i_0, i_n):
        print(f"nobody_{i}                  ", end="\r")
        db.execute("INSERT INTO users (id, username, password_hash) VALUES (?,?,?)",
                   [i, "nobody_" + str(i), ""])
        nobody_users.append(i)

    print("Every new `nobody_N` user gives 0..5 numerical reviews to random recipes...")
    for i, user_id in enumerate(nobody_users):
        print(f"{i + 1}/{len(nobody_users)}           ", end="\r")
        for _ in range(random.randint(0, 5)):
            recipe_id = random.choice(test_recipes)
            rating = recipe_id % 4  # 0..3
            rating += random.randint(1, 2)  # 1..5
            db.execute(
                """
                INSERT INTO user_reviews (author_id, recipe_id, rating)
                VALUES (?,?,?)
                """, [user_id, recipe_id, rating])

    print("Commit and vacuum...")
    db.commit()
    db.execute("VACUUM")
    db.close()
    print("Thanks, bye.")

main()
