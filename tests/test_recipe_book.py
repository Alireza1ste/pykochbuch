import pytest
from pykochbuch.unit import Unit
from pykochbuch.ingredient import Ingredient
from pykochbuch.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook

i1=Ingredient("flour", 500, Unit.GRAM)
i2=Ingredient("water", 200, Unit.MILLILITER)
r = Recipe("Pizza dough",
           "Preparing pizza dough for one person.",
           1,
           15,
           (i1, i2),
           ("mixing flour with watter and resting for 10 minutes",),
           {"for lunch",},
           )
rb = RecipeBook()
rb.add_recipe(r)

def test_recipe_double_title():
    with pytest.raises(ValueError):
        rb.add_recipe(r)

def test_removing_unknown_recipe():
    with pytest.raises(KeyError):
        rb.remove_recipe("Pizza")