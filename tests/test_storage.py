import pytest,re, json
from pykochbuch.unit import Unit
from pykochbuch.ingredient import Ingredient
from pykochbuch.recipe import Recipe
from pykochbuch.recipe_book import RecipeBook
from pykochbuch.shopping_list import ShoppingList
from pykochbuch.storage import _dict_to_recipe, _recipe_to_dict, InMemoryStore, JsonStore, SqliteStore
from pathlib import Path
from tempfile import TemporaryDirectory

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

@pytest.fixture
def pancakes() -> Recipe:
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
    return r1

@pytest.fixture
def cake() -> Recipe:    
    r1=Recipe(
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
    return r1

@pytest.fixture
def temp_path():
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

def test_save_and_load(temp_path, pancakes, cake):
    store = JsonStore(temp_path / "recipes.json")
    store.save_recipe(pancakes)
    store.save_recipe(cake)
    result = store.get_recipe("Pancakes")
    assert result.title == "Pancakes"
    result = store.get_recipe("Cake")
    assert result.title == "Cake"

# js=JsonStore(path= Path("src/pykochbuch/all_recipes.json"))
# my_path=js.path

def test_saving_and_loading_round_trip(temp_path, pancakes):
    test_file = temp_path / "round_trip.json"
    local_store = JsonStore(path= test_file)
    local_store.save_recipe(pancakes)
    with open(test_file, "r", encoding= "utf-8") as file:
        json_list = json.load(file)
        python_data=_dict_to_recipe(json_list[0])
        assert python_data == Recipe(
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


def test_saving_and_loading_empty_recipe(temp_path):
    test_file = temp_path / "empty_recipe.json"
    local_store = JsonStore(path= test_file)
    with pytest.raises(ValueError):
        empty=Recipe(title="", servings=1)
        local_store.save_recipe(empty)

def test_saving_duplicated_recipe(temp_path, pancakes):
    test_file = temp_path / "duplicated_recipe.json"
    local_store = JsonStore(path= test_file)
    local_store.save_recipe(pancakes) 
    with pytest.raises(ValueError):
        local_store.save_recipe(pancakes)  

def test_getting_unknown_recipe(temp_path, pancakes):
    test_file = temp_path / "duplicated_recipe.json"
    local_store = JsonStore(path= test_file)
    local_store.save_recipe(pancakes) 
    with pytest.raises(KeyError):
        local_store.get_recipe("Pizza")

def test_saving_and_loading_several_recipes_round_trip(temp_path, pancakes, cake):
    test_file = temp_path / "round_trip_several_recipes.json"
    local_store = JsonStore(path= test_file)
    local_store.save_recipe(pancakes)
    local_store.save_recipe(cake)
    with open(test_file, "r", encoding= "utf-8") as file:
        json_list = json.load(file)
        python_data=local_store.get_all_recipes()
        assert python_data == [
            Recipe(
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
        ),
            Recipe(
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
        ]  

@pytest.fixture(params=["memory", "json", "sqlite"])
def store(request, temp_path):
    if request.param == "memory":
        return InMemoryStore(_book=RecipeBook())
    elif request.param == "json":
        return JsonStore(temp_path / "recipes.json")
    return SqliteStore(":memory:") 

def test_saving_and_loading_round_trip_all_three(store, pancakes):
    store.save_recipe(pancakes)
    result = store.get_recipe("Pancakes")
    assert result.title == "Pancakes"
    assert result.servings == 4
    assert len(result.ingredients) == 3
    assert result.instructions == pancakes.instructions
    assert result.tags == frozenset(["easy"])

def test_get_all_empty(store):
    assert store.get_all_recipes() == []

def test_duplicate_raises(store, pancakes):
    store.save_recipe(pancakes)
    with pytest.raises(ValueError, match="already exists"):
        store.save_recipe(pancakes)

def test_delete_recipe(store, pancakes):
    store.save_recipe(pancakes)
    store.delete_recipe("Pancakes")
    assert store.get_all_recipes() == []

def test_delete_nonexistent_raises(store):
    with pytest.raises(KeyError):
        store.delete_recipe("Unknown")

def test_recipe_without_tags(store):
    recipe = Recipe(
        title="Simple Soup",
        servings=2,
        ingredients=(Ingredient("water", 1, Unit.LITER),),
        instructions=("Boil water",),
    )
    store.save_recipe(recipe)
    result = store.get_recipe("Simple Soup")
    assert result.title == "Simple Soup"
    assert result.tags == frozenset()