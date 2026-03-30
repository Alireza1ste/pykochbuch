from enum import Enum
class Unit(Enum):
    GRAM = "g" # print(Unit.GRAM.value)->"gr"
    KILOGRAM = "kg"
    MILLILITER = "ml"
    LITER = "l"
    PIECE = "pc"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"

CONVERSIONS: dict[tuple[Unit, Unit], float] = {
    (Unit.GRAM, Unit.KILOGRAM): 0.001,
    (Unit.KILOGRAM, Unit.GRAM): 1000,
    (Unit.MILLILITER, Unit.LITER): 0.001,
    (Unit.LITER, Unit.MILLILITER): 1000
}

def units_are_compatible(a: Unit, b: Unit) -> bool:
    return a == b or (a, b) in CONVERSIONS

def convert(amount: float, from_unit: Unit, to_unit: Unit) -> float:
    if from_unit == to_unit:
        return amount
    factor = CONVERSIONS.get((from_unit, to_unit))
    if factor == None:
        raise ValueError(f"Cannot convert {from_unit.value} to {to_unit.value}")
    return factor * amount