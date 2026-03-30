import pytest
from pykochbuch.models.ingredient import Ingredient
from pykochbuch.models.unit import Unit

def test_creation_of_ingredient_correctly():
    ingredient=Ingredient("Mehl", 500, Unit.GRAM)
    assert ingredient.name == "mehl"

def test_creation_of_ingredient_with_empty_name():
    with pytest.raises(ValueError):
        Ingredient("", 100, Unit.GRAM)

def test_creation_of_ingredient_with_negative_amount():
        with pytest.raises(ValueError):
             Ingredient("Mehl", -1, Unit.GRAM)

def test_scaling():
    ingredient=Ingredient("Mehl", 500, Unit.GRAM)
    ingredient_4_persons = ingredient.scale(4)
    ingredient_8_persons = ingredient.scale(8)
    assert ingredient_4_persons == Ingredient("Mehl", 2000, Unit.GRAM)
    assert ingredient_8_persons == Ingredient("Mehl", 4000, Unit.GRAM)