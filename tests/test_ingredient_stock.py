from app.models.ingredient import Ingredient

def test_stock_disponible():
    ingredient = Ingredient(
        id=1,
        name="Harina",
        unit_id=2,
        stock_fisico=25.0,
        stock_reservado=10.0,
        stock_minimo=5.0
    )
    assert ingredient.stock_disponible == 15.0