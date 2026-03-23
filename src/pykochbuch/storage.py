# import json
# def geo_serializer(obj):
#     if isinstance(obj, Point):
#         return {"_type": "point", "x": obj.x, "y": obj.y}
#     if isinstance(obj, Line):
#         return {"_type": "line", "start": obj.start, "end": obj.end}
#     raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

import pytest,re
from pykochbuch.unit import Unit
from pykochbuch.ingredient import Ingredient
from pykochbuch.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook
from pykochbuch.shopping_list import ShoppingList
import json

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




