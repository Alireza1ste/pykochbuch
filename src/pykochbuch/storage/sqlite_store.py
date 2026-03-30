from pathlib import Path
import re, sqlite3
from dataclasses import dataclass, field
from pykochbuch.models.unit import Unit
from pykochbuch.models.ingredient import Ingredient
from pykochbuch.models.recipe import Recipe
from pykochbuch.storage.base import RecipeStore

@dataclass
class SqliteStore(RecipeStore):
    db_path: str | Path
    connection : sqlite3.Connection = field(init=False)

    def __post_init__(self):
        self.connection = sqlite3.connect(str(self.db_path))
        # Enable Foreign Key support (SQLite has it off by default!)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()
    
    def _create_tables(self):
        cur = self.connection.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                servings INTEGER NOT NULL,
                prep_time_minutes INTEGER NOT NULL DEFAULT 0);""")
        cur.execute(
            """CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                unit TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                instruction TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );""")
        cur.execute(
            """CREATE TABLE IF NOT EXISTS recipe_tags (
                recipe_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY (recipe_id, tag),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            );""")
        
        self.connection.commit()
    
    def save_recipe(self, recipe: Recipe) -> None:
        cur = self.connection.cursor()
        try:
            cur.execute(
            "INSERT INTO recipes (title, description, servings, prep_time_minutes) "
            "VALUES (?, ?, ?, ?)",
            (recipe.title, recipe.description, recipe.servings, recipe.prep_time_minutes),
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Recipe '{recipe.title}' already exists.")
        recipe_id = cur.lastrowid

        for ingredient in recipe.ingredients:
            cur.execute(
                "INSERT INTO ingredients (recipe_id, name, amount, unit) "
                "VALUES (?, ?, ?, ?)",
                (recipe_id, ingredient.name, ingredient.amount, ingredient.unit.value)
            )
        
        for step_number, instruction in enumerate(recipe.instructions, 1):
            cur.execute(
                "INSERT INTO instructions (recipe_id, step_number, instruction) "
                "VALUES (?, ?, ?)",
                (recipe_id, step_number, instruction),
            )
        
        for tag in recipe.tags:
            cur.execute(
                "INSERT INTO recipe_tags (recipe_id, tag) VALUES (?, ?)",
                (recipe_id, tag),
            )
        self.connection.commit()
    
    def _load_recipe_by_row(self, row: tuple) -> Recipe:
        cursor = self.connection.cursor()
        (recipe_id, title, description, servings, prep_time_minutes) = row
        cursor.execute(
            "SELECT name, amount, unit FROM ingredients WHERE recipe_id = ?",
            (recipe_id,),
        )
        ingredients = tuple(
            Ingredient(name=name, amount=amount, unit=Unit(unit))
            for name, amount, unit in cursor.fetchall()
        )
        cursor.execute(
            "SELECT instruction FROM instructions WHERE recipe_id = ? "
            "ORDER BY step_number",
            (recipe_id,),
        )
        instructions = tuple(row[0] for row in cursor.fetchall())
        cursor.execute(
            "SELECT tag FROM recipe_tags WHERE recipe_id = ?", (recipe_id,)
        )
        tags = frozenset(row[0] for row in cursor.fetchall())
        return Recipe(
            title=title,
            description=description,
            servings=servings,
            prep_time_minutes=prep_time_minutes,
            ingredients=ingredients,
            instructions=instructions,
            tags=tags,
            )

    def get_recipe(self, title: str) -> Recipe:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT id, title, description, servings, prep_time_minutes "
            "FROM recipes WHERE LOWER(title) = LOWER(?)",
            (title,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Recipe '{title}' not found")
        return self._load_recipe_by_row(row)
    
    def get_all_recipes(self):
        cur = self.connection.cursor()
        cur.execute(
            "SELECT id, title, description, servings, prep_time_minutes "
            "FROM recipes;"
        )
        return [self._load_recipe_by_row(row) for row in cur.fetchall()]
    
    def delete_recipe(self, title):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT id FROM recipes WHERE LOWER(title) = LOWER(?)",
            (title,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"Recipe '{title}' not found")
        cursor.execute(
            "DELETE FROM recipes WHERE id = ?",
            (row[0],),
        )
        self.connection.commit()
    
    def search_by_title(self, query):
        pattern = re.compile(query, re.IGNORECASE)
        all_recipes = self.get_all_recipes()
        return [r for r in all_recipes if pattern.search(r.title)]

