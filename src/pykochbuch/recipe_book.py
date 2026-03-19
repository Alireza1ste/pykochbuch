from __future__ import annotations
from pykochbuch.recipe import Recipe
from dataclasses import dataclass, field
import re
@dataclass
class RecipeBook:
    recepes :dict[str, Recipe]= field(default_factory= dict)

    def add_recipe(self, recipe: Recipe) -> None:
        if recipe.title in self.recepes:
            raise ValueError(f"The recipe {recipe.title} already exists. Duplicates Cannot be added.")
        else:
            self.recepes[recipe.title]=recipe
    
    def remove_recipe(self, title: str) -> None:
        if title not in self.recepes:
            raise KeyError(f"The recipe {title} was not found.")
        else:
            del self.recepes[title]
    
    def get_recipe(self, title: str) -> Recipe:
        if title not in self.recepes.keys():
            raise KeyError(f"There is no recipe for {title}.")
        return self.recepes[title]
    
    @property
    def recipes(self) -> list[Recipe]:
        return [recipe for recipe in self.recepes.values()]
    
    def search_by_title(self, query:str) -> list[Recipe]:
        # pattern = re.compile(query, re.IGNORECASE) :alternative
        # return [recipe for recipe in self.recepes.values() if pattern.search(recipe.title)]
        return [
            recipe for recipe in self.recepes.values()
                if re.search(query, recipe.title, re.IGNORECASE)
                ]
    
    def search_by_ingredient(self, name: str) -> list[Recipe]:
        search_name = name.strip().lower()
        return [
            recipe for recipe in self.recepes.values()
            if any(ingredient.name.lower() == search_name for ingredient in recipe.ingredients)
        ]
        # Alternative 
        # result=[]
        # for recipe in self.recepes.values():
        #     for ingredient in recipe.ingredients:
        #         if ingredient.name.lower() == search_name:
        #             result.append(recipe)
        #             break # <--- "I found it in this recipe! Move to the next recipe."
        # return result
    
    def search_by_tag(self, tag:str) -> list[Recipe]:
        search_tag = tag.strip().lower()
        return [
            recipe for recipe in self.recepes.values()
            if search_tag in recipe.tags# alternative: if any(t == search_tag for t in recipe.tags)
        ]
    
    def filter_by_max_time(self, minutes: float) -> list[Recipe]:
        if minutes < 0:
            raise ValueError("The preparation time cannot be negative.")
        return [
            recipe for recipe in self.recepes.values()
            if recipe.prep_time_minutes <= minutes
        ]
    
    def search(self, title:str | None = None,
               ingredient:str | None = None,
                tag: str | None = None,
                 max_time:float | None = None) -> list[Recipe]:
        result = set(self.recepes.values())
        if title:
            result &= set(self.search_by_title(title))
        
        if ingredient:
            result &= set(self.search_by_ingredient(ingredient))
        
        if tag:
            result &= set(self.search_by_tag(tag))
        
        if max_time:
            result &= set(self.filter_by_max_time(max_time))
        
        return list(result)