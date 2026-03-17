from __future__ import annotations
from pykochbuch.recipe import Recipe
from dataclasses import dataclass, field
@dataclass
class RecipeBook:
    recepes :dict[str, Recipe]= field(default_factory= dict)

    def add_recipe(self, recipe: Recipe) -> dict:
        if recipe.title in self.recepes:
            raise ValueError(f"The recipe {recipe.title} already exists. Duplicates Cannot be added.")
        else:
            self.recepes[recipe.title]=recipe
    
    def remove_recipe(self, title: str) -> dict:
        if title not in self.recepes:
            raise KeyError(f"The recipe {title} was not found.")
        else:
            del self.recepes[title]
    
    def get_recipe(self, title: str) -> Recipe:
        if title not in self.recepes:
            raise KeyError(f"There is no recipe for {title}.")
        return self.recepes.get(title)
    
    @property
    def recipes(self) -> list[Recipe]:
        return [recipe for recipe in self.recepes.values()]