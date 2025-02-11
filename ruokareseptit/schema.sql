-- Initialize the database.
-- Use `flask --app ruokareseptit init-db` to execute this script.

PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS instructions;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS recipe_category;
DROP TABLE IF EXISTS user_review;
PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL
);

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    preparation_time INTEGER,
    cooking_time INTEGER,
    skill_level INTEGER,
    portions INTEGER,
    published INTEGER DEFAULT 0,
    author_id INTEGER REFERENCES users ON DELETE SET NULL
);

CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE,
    order_number INTEGER NOT NULL,
    amount INTEGER,
    unit TEXT,
    title TEXT
);

CREATE TABLE instructions (
  id INTEGER PRIMARY KEY,
  recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE,
  order_number INTEGER,
  instructions TEXT
);

CREATE TABLE categories (
  id INTEGER PRIMARY KEY,
  title TEXT
);

CREATE TABLE recipe_category (
  recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE,
  category_id INTEGER REFERENCES categories ON DELETE CASCADE
);

CREATE TABLE user_review (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users ON DELETE SET NULL,
  recipe_id INTEGER REFERENCES recipes ON DELETE CASCADE,
  rating INTEGER,
  review TEXT
);

-- Initial content

INSERT INTO users (id, username, password_hash) VALUES
(1, 'user1', 'pass'),
(2, 'user2', 'pass');

INSERT INTO recipes (title, summary, preparation_time, cooking_time, skill_level, portions, published, author_id) VALUES
('Suolajauho', 'Perinteinen suolajauho itämaisella twistillä.', 10, 20, 1, 2, 1, 1),
('Voiperuna', 'Peruna maistuu voin kanssa hyvältä.', 10, 20, 1, 2, 1, 2);

INSERT INTO ingredients (recipe_id, order_number, amount, unit, title) VALUES
(1, 1, 2, 'dl', 'Jauhoja'),
(1, 2, 1, 'tl', 'Suolaa'),
(1, 3, 1, 'nippu', 'Korianteria'),
(2, 1, 1, 'kg', 'Pottuja'),
(2, 2, 1, 'nyrkillinen', 'Voita')
;

INSERT INTO instructions (recipe_id, order_number, instructions) VALUES
(1, 1, 'Sekoita jauhot ja suola huolellisesti.'),
(1, 2, 'Kaada seos lattialle.'),
(2, 1, 'Kuori ja keitä perunat.'),
(2, 2, 'Annostele lautaselle voin kera.');

INSERT INTO categories (title) VALUES
('Perinteinen'),
('Itämainen'),
('Arkiruoka');

INSERT INTO recipe_category (recipe_id, category_id) VALUES
(1, 1),
(1, 2),
(2, 3);

INSERT INTO user_review (user_id, recipe_id, rating, review) VALUES
(1, 1, 5, 'Erinomainen suolajauho!'),
(1, 1, 2, 'En pitänyt.'),
(1, 2, 4, 'Maistui voin kanssa todella hyvälle.');

VACUUM;
