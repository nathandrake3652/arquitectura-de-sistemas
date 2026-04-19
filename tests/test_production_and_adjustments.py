from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe_item import RecipeItem
from app.models.stock_movement import StockMovement
from app.models.unit import Unit


def test_finish_order_consumes_physical_and_releases_reserved(client, db_session):
    unit_g = Unit(name="Gramo finish", abbreviation="g-finish", base_factor=1.0)
    db_session.add(unit_g)
    db_session.commit()
    db_session.refresh(unit_g)

    flour = Ingredient(
        name="Harina finish",
        unit_id=unit_g.id,
        stock_fisico=2000.0,
        stock_reservado=0.0,
        stock_minimo=0.0,
    )
    cake = Product(name="Torta finish", description="test", price=1000)
    db_session.add_all([flour, cake])
    db_session.commit()
    db_session.refresh(flour)
    db_session.refresh(cake)

    db_session.add(
        RecipeItem(
            product_id=cake.id,
            ingredient_id=flour.id,
            unit_id=unit_g.id,
            quantity=250.0,
        )
    )
    db_session.commit()

    confirm_response = client.post(
        "/api/v1/confirm",
        json={"product_id": cake.id, "order_quantity": 2},
    )
    assert confirm_response.status_code == 200

    finish_response = client.post(
        "/api/v1/finish",
        json={"product_id": cake.id, "order_quantity": 2, "status": "cocinado"},
    )

    assert finish_response.status_code == 200
    db_session.refresh(flour)
    assert flour.stock_reservado == 0.0
    assert flour.stock_fisico == 1500.0

    movements = db_session.query(StockMovement).filter(StockMovement.ingredient_id == flour.id).all()
    assert len(movements) == 1
    assert movements[0].tipo == "salida_produccion"
    assert movements[0].cantidad == 500.0


def test_inventory_adjustments_register_audit(client, db_session):
    unit_g = Unit(name="Gramo adjust", abbreviation="g-adjust", base_factor=1.0)
    db_session.add(unit_g)
    db_session.commit()
    db_session.refresh(unit_g)

    flour = Ingredient(
        name="Harina adjust",
        unit_id=unit_g.id,
        stock_fisico=1000.0,
        stock_reservado=100.0,
        stock_minimo=0.0,
    )
    db_session.add(flour)
    db_session.commit()
    db_session.refresh(flour)

    entry_response = client.post(
        f"/api/v1/ingredients/{flour.id}/adjustments",
        json={
            "tipo": "entrada_compra",
            "cantidad": 200.0,
            "motivo": "Compra proveedor semanal",
        },
    )
    assert entry_response.status_code == 200

    waste_response = client.post(
        f"/api/v1/ingredients/{flour.id}/adjustments",
        json={
            "tipo": "salida_merma",
            "cantidad": 150.0,
            "motivo": "Merma por vencimiento",
        },
    )
    assert waste_response.status_code == 200

    db_session.refresh(flour)
    assert flour.stock_fisico == 1050.0
    assert flour.stock_reservado == 100.0
    assert flour.stock_disponible == 950.0

    movements = db_session.query(StockMovement).filter(StockMovement.ingredient_id == flour.id).order_by(StockMovement.id).all()
    assert len(movements) == 2
    assert movements[0].tipo == "entrada_compra"
    assert movements[1].tipo == "salida_merma"


def test_inventory_merma_fails_if_invades_reserved_stock(client, db_session):
    unit_g = Unit(name="Gramo conflict", abbreviation="g-conflict", base_factor=1.0)
    db_session.add(unit_g)
    db_session.commit()
    db_session.refresh(unit_g)

    ingredient = Ingredient(
        name="Harina conflict",
        unit_id=unit_g.id,
        stock_fisico=300.0,
        stock_reservado=250.0,
        stock_minimo=0.0,
    )
    db_session.add(ingredient)
    db_session.commit()
    db_session.refresh(ingredient)

    response = client.post(
        f"/api/v1/ingredients/{ingredient.id}/adjustments",
        json={
            "tipo": "salida_merma",
            "cantidad": 100.0,
            "motivo": "Merma por daño",
        },
    )

    assert response.status_code == 409
    db_session.refresh(ingredient)
    assert ingredient.stock_fisico == 300.0

    movements = db_session.query(StockMovement).filter(StockMovement.ingredient_id == ingredient.id).all()
    assert movements == []
