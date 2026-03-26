from pathlib import Path
import pytest,re
from dataclasses import dataclass, field
from pykochbuch.unit import Unit
from pykochbuch.ingredient import Ingredient
from pykochbuch.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook
from pykochbuch.shopping_list import ShoppingList
import json, sqlite3

def _recipe_to_dict(recipe: Recipe) -> dict:
    return{
        "title": recipe.title,
        "description": recipe.description,
        "servings": recipe.servings,
        "prep_time_minutes": recipe.prep_time_minutes,
        "ingredients":[
            {
                "name": ingredient.name,
                "amount": ingredient.amount,
                "unit": ingredient.unit.value,
            } for ingredient in recipe.ingredients
        ],
        "instructions": list(recipe.instructions),
        "tags": sorted(list(recipe.tags)),
    }

def _dict_to_recipe(data: dict) -> Recipe:
    return Recipe(
        title= data["title"],
        description= data.get("description", ""),
        servings= data["servings"],
        prep_time_minutes= data.get("prep_time_minutes", 0),
        ingredients= tuple(
            Ingredient(
                name= ingredient["name"],
                amount= ingredient["amount"],
                unit= Unit(ingredient["unit"]) 
        ) for ingredient in data["ingredients"]
        ),
        instructions= tuple(data["instructions"]),
        tags= frozenset(data.get("tags", [])),
    )

@dataclass
class JsonStore:
    path: Path# my_path=Path("src/pykochbuch/all_recipes.json")

    def save_recipe(self, recipe: Recipe):
        existing_recipes= []
        if self.path.exists():
            with open(self.path, "r", encoding= "utf-8") as file:
                try:
                    existing_recipes= json.load(file)#what if the file is empty? it is not false to be empty.
                except json.JSONDecodeError:
                    existing_recipes=[]
        
        for recipe_dict in existing_recipes:
            if recipe_dict["title"] == recipe.title:
                raise ValueError(f"The recipe {recipe.title} already exists.")
        
        new_recipe_dict = _recipe_to_dict(recipe)
        existing_recipes.append(new_recipe_dict)
            
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(existing_recipes, file, indent=4, ensure_ascii= False)
    
    def get_recipe(self, title):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as file:
                try:
                    existing_recipes= json.load(file)
                    for recipe_dict in existing_recipes:
                        if recipe_dict["title"] == title:
                            return _dict_to_recipe(recipe_dict)
                except json.JSONDecodeError:#syntax error
                    pass
        raise KeyError(f"The recipe '{title}' was not found.")

    def get_all_recipes(self):
        all_recipes=[]
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as file:
                try:
                    existing_recipes= json.load(file)
                    for recipe_dict in existing_recipes:
                        all_recipes.append(_dict_to_recipe(recipe_dict))
                except json.JSONDecodeError:
                    pass
        return all_recipes
    
    def delete_recipe(self, title):
        existing_recipes= []
        if self.path.exists():
            with open(self.path, "r", encoding= "utf-8") as file:
                try:
                    existing_recipes= json.load(file)
                except json.JSONDecodeError:
                    existing_recipes=[]
        
        recipe_found=False
        for recipe_dict in existing_recipes[:]:
            if recipe_dict["title"] == title:
                existing_recipes.remove(recipe_dict)
                recipe_found = True
                break
        if not recipe_found:
            raise KeyError(f"The recipe {title} does not exist.")
            
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(existing_recipes, file, indent=4, ensure_ascii= False)
        
    def search_by_title(self, query):
        found_query=[]
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as file:
                try:
                    existing_recipes= json.load(file)
                    for recipe_dict in existing_recipes:
                        if re.search(query, recipe_dict["title"], re.IGNORECASE):
                            found_recipe=_dict_to_recipe(recipe_dict)
                            found_query.append(found_recipe)
                except json.JSONDecodeError:#syntax error
                    pass
        if not found_query:
            raise KeyError(f"The recipe '{query}' was not found.")
        return found_query

@dataclass
class SqliteStore:
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
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                instruction TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );""")
        cur.execute(
            """CREATE TABLE IF NOT EXISTS recipe_tags (
                recipe_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY (recipe_id, tag),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id)
            );""")
        
        self.connection.commit()
    
    def save_recipe(self, recipe: Recipe) -> None:
        cur = self.connection.cursor()
        try:
            cur.execute(
            "INSERT INTO recipes (title, description, servings, prep_time_minutes)"
            "VALUES (?, ?, ?, ?)",
            (recipe.title, recipe.description, recipe.servings, recipe.prep_time_minutes),
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Recipe '{recipe.title}' already exists.")
        recipe_id = cur.lastrowid

        for ingredient in recipe.ingredients:
            cur.execute(
                "INSERT INTO ingredients (recipe_id, name, amount, unit)"
                "VALUES (?, ?, ?, ?)",
                (recipe_id, ingredient.name, ingredient.amount, ingredient.unit)
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