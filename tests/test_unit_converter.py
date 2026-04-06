from app.utils.unit_converter import convert
from app.models.unit import Unit

def test_convert_gram_to_kilogram():
    unit_g = Unit(id=1, name="gram", abbreviation="g", base_factor=1.0)
    unit_kg = Unit(id=2, name="kilogram", abbreviation="kg", base_factor=1000.0)
    resultado = convert(1000, unit_g, unit_kg)
    assert resultado == 1.0