import pytest
from pykochbuch.unit import Unit
from pykochbuch.ingredient import Ingredient
from pykochbuch.recipe import Recipe

i1=Ingredient("flour", 500, Unit.GRAM)
i2=Ingredient("water", 200, Unit.MILLILITER)

def test_recipe_with_empty_name():
    with pytest.raises(ValueError):
        r = Recipe("",
           "Preparing pizza dough for one person.",
           1,
           15,
           (i1, i2),
           ("mixing flour with watter and resting for 10 minutes",),
           tags=frozenset(["vegan", "italian"]),)


i1=Ingredient("flour", 500, Unit.GRAM)
i2=Ingredient("water", 200, Unit.MILLILITER)
r = Recipe("Pizza dough",
           "Preparing pizza dough for one person.",
           1,
           15,
           (i1, i2),
           ("mixing flour with watter and resting for 10 minutes",),
           tags=frozenset(["vegan", "italian"]),)

def test_scale():
    assert r.scale(3) == Recipe("Pizza dough",
           "Preparing pizza dough for one person.",
           3,
           45,
           (i1.scale(3), i2.scale(3)),
           ("mixing flour with watter and resting for 10 minutes",),
           tags=frozenset(["vegan", "italian"]),)

def test_scale_to_serving_n_equals_0():
   with pytest.raises(ValueError):
       r.scale_to_servings(0)