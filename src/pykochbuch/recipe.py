from __future__ import annotations
from pykochbuch.ingredient import Ingredient
from dataclasses import dataclass, field
@dataclass
class Recipe:
    title: str
    description: str = ""
    servings: int = 1
    prep_time_minutes: float = 0
    ingredients: tuple[Ingredient, ...] = ()
    instructions: tuple[str, ...] = ()
    tags:frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        title_normalized = self.title.strip()
        if not title_normalized:
            raise ValueError("Title cannot be empty.")
        if self.servings <=0:
            raise ValueError("Number of people to be served should be positive.")
        if len(self.ingredients) < 1:
            raise ValueError("There should be at least one ingredient.")
        if len(self.instructions) < 1:
            raise ValueError("There should be at least one instruction.")

    def scale(self, factor: float) -> Recipe:
        return Recipe(
            title = self.title,
            description = self.description,
            servings = round(self.servings*factor),
            prep_time_minutes = round(self.prep_time_minutes * factor),
            ingredients = tuple(ingredient.scale(factor) for ingredient in self.ingredients),
            instructions = self.instructions,
            tags = self.tags,)
    
    def scale_to_servings(self, n: float):
        if n <=0:
            raise ValueError("Number of people to be served should be positive.")
        return self.scale(n/self.servings)