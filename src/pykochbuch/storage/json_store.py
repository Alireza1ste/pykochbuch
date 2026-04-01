from pathlib import Path
import re
from dataclasses import dataclass
from pykochbuch.models.recipe import Recipe
import json
from pykochbuch.storage.base import RecipeStore
from pykochbuch.storage.serialization import _dict_to_recipe, _recipe_to_dict

@dataclass
class JsonStore(RecipeStore):
    path: Path  # This is correct as a field my_path=Path("src/pykochbuch/all_recipes.json")

    # Add a check to ensure the folder exists when saving
    def _ensure_file(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_recipe(self, recipe: Recipe) -> None:
        try:
            # 1. Ensure the folder exists
            self.path.parent.mkdir(parents=True, exist_ok=True)

            # 2. Load existing data
            recipes_list = []
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    try:
                        recipes_list = json.load(f)
                    except json.JSONDecodeError:
                        recipes_list = []

            # --- 2.5 DUPLICATE CHECK (This fixes your test error) ---
            if any(r.get('title') == recipe.title for r in recipes_list):
                raise ValueError(f"Recipe '{recipe.title}' already exists.")

            # 3. Convert recipe to dict (using your serialization helper)
            from pykochbuch.storage.serialization import _recipe_to_dict
            new_data = _recipe_to_dict(recipe)

            # 4. Add to list
            recipes_list.append(new_data)

            # 5. Write to file
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(recipes_list, f, indent=4, ensure_ascii=False)
            
        except ValueError as ve:
            # Re-raise ValueErrors so the test/GUI can see them
            raise ve
        except Exception as e:
            print(f"INTERNAL STORE ERROR: {e}")
            raise e
    
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
