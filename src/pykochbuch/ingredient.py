from dataclasses import dataclass
from pykochbuch.unit import Unit
@dataclass(frozen=True)
class Ingredient:
    name: str
    amount: float
    unit: Unit

    def __post_init__(self):
        normalized_name=self.name.strip().lower()
        if not normalized_name:
            raise ValueError("Name cannot be empty or just whitespace.")
        if self.amount <= 0:
            raise ValueError("Amount cannot be negative.")
        object.__setattr__(self, 'name' ,normalized_name)
    
    def scale(self,factor: float) -> Ingredient:
        return Ingredient(self.name, self.amount*factor, self.unit)
    
    def __str__(self) -> str:
        return f"{self.amount} {self.unit.value} {self.name}"