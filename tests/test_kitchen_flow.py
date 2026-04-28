from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe_item import RecipeItem
from app.models.unit import Unit


def _setup_confirmed_order(client, db_session):
    unit_g = Unit(name="Gramo kitchen", abbreviation="g-kitchen", base_factor=1.0)
    db_session.add(unit_g)
    db_session.commit()
    db_session.refresh(unit_g)

    flour = Ingredient(
        name="Harina kitchen",
        unit_id=unit_g.id,
        stock_fisico=2000.0,
        stock_reservado=0.0,
        stock_minimo=100.0,
    )
    cake = Product(name="Torta kitchen", description="test kitchen", price=10000)
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

    return flour, cake, confirm_response.json()["order_id"]


def test_kitchen_screen_lists_confirmed_orders(client, db_session):
    _, cake, order_id = _setup_confirmed_order(client, db_session)

    response = client.get("/ui/kitchen")
    assert response.status_code == 200
    body = response.text
    assert f"#{order_id}" in body
    assert cake.name in body
    assert "Confirmado" in body


def test_kitchen_mark_ready_consumes_reserved_stock(client, db_session):
    flour, _, order_id = _setup_confirmed_order(client, db_session)

    response = client.post(f"/ui/kitchen/{order_id}/ready")
    assert response.status_code == 200
    assert "Listo" in response.text

    db_session.refresh(flour)
    assert flour.stock_fisico == 1500.0
    assert flour.stock_reservado == 0.0


def test_kitchen_mark_delivered_changes_status(client, db_session):
    _, _, order_id = _setup_confirmed_order(client, db_session)

    ready_response = client.post(f"/ui/kitchen/{order_id}/ready")
    assert ready_response.status_code == 200

    delivered_response = client.post(f"/ui/kitchen/{order_id}/deliver")
    assert delivered_response.status_code == 200
    assert "Entregado" in delivered_response.text

    reload_response = client.get("/ui/kitchen")
    assert reload_response.status_code == 200
    assert f"#{order_id}" not in reload_response.text
