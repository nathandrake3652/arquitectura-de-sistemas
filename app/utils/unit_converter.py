from app.models.unit import Unit

def convert(value: float, from_unit: Unit, to_unit: Unit) -> float:
    if from_unit.id == to_unit.id:
        return value
    conversion_ratio = from_unit.base_factor / to_unit.base_factor
    return value * conversion_ratio