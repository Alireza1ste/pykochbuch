import pytest,re
from pykochbuch.unit import Unit
from pykochbuch.ingredient import Ingredient
from pykochbuch.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook
from pykochbuch.shopping_list import ShoppingList

@pytest.fixture
def pancakes_cake() -> RecipeBook:
    r1=Recipe(
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
    rb=RecipeBook()
    rb.add_recipe(r1)
    r2=Recipe(
        title="Cake",
        servings=8,
        prep_time_minutes=60,
        ingredients=(
            Ingredient("flour", 300, Unit.GRAM),
            Ingredient("sugar", 200, Unit.GRAM),
            Ingredient("eggs", 3, Unit.PIECE),
        ),
        instructions=("Mix", "Bake"),
        tags=frozenset(["difficult"]),
    )
    rb.add_recipe(r2)
    return rb

# In pytest, you don't call the fixture like a function. Instead, you pass its name as an argument to your test.
def test_partial_match_title(pancakes_cake):
    rn1=pancakes_cake.search_by_title("^C")
    rn2=pancakes_cake.search_by_title("anc")
    assert rn1[0].title == "Cake"
    assert rn2[0].title == "Pancakes"

def test_search_ingredients(pancakes_cake):
    i1=pancakes_cake.search_by_ingredient("milk")
    i2=pancakes_cake.search_by_ingredient("sugar")
    i3=pancakes_cake.search_by_ingredient("flour")

    assert len(i1) == 1
    assert len(i2) == 1
    assert len(i3) == 2
    assert i1[0].title == "Pancakes"
    assert i2[0].title == "Cake"
    assert i3[0].title == "Pancakes"
    assert i3[1].title == "Cake"

def test_search_tags(pancakes_cake):
    t1=pancakes_cake.search_by_tag("easy")
    t2=pancakes_cake.search_by_tag("difficult")

    assert len(t1) == 1
    assert len(t2) == 1
    assert t1[0].title == "Pancakes"
    assert t2[0].title == "Cake"

def test_time_filter(pancakes_cake):
    ti1=pancakes_cake.filter_by_max_time(20)
    ti2=pancakes_cake.filter_by_max_time(60)

    assert len(ti1) == 1
    assert len(ti2) == 2
    assert ti1[0].title == "Pancakes"
    assert ti2[0].title == "Pancakes"
    assert ti2[1].title == "Cake"

def test_merge_same_unit(pancakes_cake):
    sh= ShoppingList()
    pancakes_cake_list=[value for value in pancakes_cake.recepes.values()]
    sh = ShoppingList.from_recipes(pancakes_cake_list)

    assert sh.shopping_list_dict == {
        "flour" : [550, Unit.GRAM],
        "milk" : [500, Unit.MILLILITER],
        "eggs" : [5, Unit.PIECE],
        "sugar" : [200, Unit.GRAM],
    }

def test_empty_recipe_book():
    sh= ShoppingList()
    pancakes_cake_list= []
    sh = ShoppingList.from_recipes(pancakes_cake_list)

    assert sh.shopping_list_dict == {}