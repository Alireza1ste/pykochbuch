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
    
    
