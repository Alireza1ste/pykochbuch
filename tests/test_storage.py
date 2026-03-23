import pytest,re
from pykochbuch.unit import Unit
from pykochbuch.ingredient import Ingredient
from pykochbuch.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook
from pykochbuch.shopping_list import ShoppingList
from pykochbuch.storage import _dict_to_recipe, _recipe_to_dict

@pytest.fixture
def _recipe() -> Recipe:
    r=Recipe(
        title="Pancakes",
        servings=4,
        prep_time_minutes=20,
        ingredients=(
            Ingredient("flour", 250, Unit.GRAM),
            Ingredient("milk", 500, Unit.MILLILITER),
            Ingredient("eggs", 2, Unit.PIECE),
        ),
        instructions=("Mix", "Cook"),
        tags=frozenset(["easy"]),        
    )
    return r

def test_dict_to_recipe_recipe_to_dict(_recipe):
    assert _dict_to_recipe(_recipe_to_dict(_recipe)) == Recipe(

        title="Pancakes",
        servings=4,
        prep_time_minutes=20,
        ingredients=(
            Ingredient("flour", 250, Unit.GRAM),
            Ingredient("milk", 500, Unit.MILLILITER),
            Ingredient("eggs", 2, Unit.PIECE),
        ),
        instructions=("Mix", "Cook"),
        tags=frozenset(["easy"]),        
    )