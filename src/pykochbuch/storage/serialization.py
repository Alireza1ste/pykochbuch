from pykochbuch.models.unit import Unit
from pykochbuch.models.ingredient import Ingredient
from pykochbuch.models.recipe import Recipe


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
