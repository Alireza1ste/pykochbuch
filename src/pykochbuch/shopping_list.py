from __future__ import annotations
from pykochbuch.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook
from pykochbuch.ingredient import Ingredient
from dataclasses import dataclass, field
from pykochbuch.unit import Unit, CONVERSIONS, units_are_compatible, convert
import re

@dataclass
class ShoppingList:
    shopping_list_dict:dict=field(default_factory=dict)
    def add_recipe(self, recipe: Recipe):
        for ingredient in recipe.ingredients:
            if ingredient.name not in self.shopping_list_dict:
                self.shopping_list_dict[ingredient.name] = [ingredient.amount, ingredient.unit]
            else:
                if units_are_compatible(ingredient.unit, self.shopping_list_dict[ingredient.name][1]):
                    converted_amount=convert(ingredient.amount, ingredient.unit,
                                             self.shopping_list_dict[ingredient.name][1])
                    self.shopping_list_dict[ingredient.name][0]+=converted_amount
                else:
                    raise ValueError(f"The units of {ingredient.name} are not compatible.")
        # return self.shopping_list_dict
    
    @property
    def items(self) -> list[Ingredient]:
        return [Ingredient(name=key, amount=value[0], unit=value[1])
                for key, value in self.shopping_list_dict.items()]
        
    @classmethod
    def from_recipes(cls, recepes:list[Recipe]) -> ShoppingList:
        # shopping_list_list = [] wrong!!!!!!!
        # ingredient_list=[]
        # for recipe in recepes:
        #     cls.add_recipe(recipe)
        #     ingredient_list=self.items()
        #     for ingredient in ingredient_list:
        #         shopping_list_list.append(ingredient)
        # ----------------------------------------------
        new_list = cls()
        for recipe in recepes:
            new_list.add_recipe(recipe)
        return new_list

    def __str__(self) -> str:
        header = "Shopping List:\n"
        lines = [f"- {ingredient.name} {ingredient.amount} {ingredient.unit}" for ingredient in self.items]
        return header + "\n".join(lines)