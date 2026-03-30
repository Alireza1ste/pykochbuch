from dataclasses import dataclass
from pykochbuch.models.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook
from pykochbuch.storage.base import RecipeStore

@dataclass
class InMemoryStore(RecipeStore):
    _book: RecipeBook

    def save_recipe(self, recipe: Recipe) -> None: 
        self._book.add_recipe(recipe)

    def get_recipe(self, title: str) -> Recipe:
        return self._book.get_recipe(title)

    def get_all_recipes(self) -> list[Recipe]:
        return self._book.recipes
    
    def delete_recipe(self, title: str) -> None:
        self._book.remove_recipe(title)

    def search_by_title(self, query: str) -> list[Recipe]:
        return self._book.search_by_title(query)