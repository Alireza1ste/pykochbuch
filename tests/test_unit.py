import pytest
from pykochbuch.unit import Unit, units_are_compatible, CONVERSIONS, convert
# from pykochbuch import unit

def test_compatible_units():
    assert units_are_compatible(Unit.GRAM, Unit.KILOGRAM)
    assert units_are_compatible(Unit.GRAM, Unit.GRAM)
    assert not units_are_compatible(Unit.GRAM, Unit.LITER)

def test_gram_to_kilogram():
    assert convert(1000, Unit.GRAM, Unit.KILOGRAM) == pytest.approx(1.0)

def test_milliliter_to_liter():
    assert convert(1000, Unit.MILLILITER, Unit.LITER) == pytest.approx(1.0)

def test_same_unit_returns_unchanged():
    assert convert(500, Unit.GRAM, Unit.GRAM) == pytest.approx(500.0)
    
def test_incompatible_units_raise():
    with pytest.raises(ValueError):
        convert(100, Unit.GRAM, Unit.LITER)

