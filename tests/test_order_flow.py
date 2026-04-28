from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe_item import RecipeItem
from app.models.unit import Unit


def test_check_reports_exact_shortage(client, db_session):
    unit_g = Unit(name="Gramo", abbreviation="g", base_factor=1.0)
    unit_kg = Unit(name="Kilogramo", abbreviation="kg", base_factor=1000.0)
    db_session.add_all([unit_g, unit_kg])
    db_session.commit()
    db_session.refresh(unit_g)
    db_session.refresh(unit_kg)

    flour = Ingredient(
        name="Harina check",
        unit_id=unit_g.id,
        stock_fisico=800,
        stock_reservado=100,
        stock_minimo=0,
    )
    cake = Product(name="Torta check", description="test", price=1000)
    db_session.add_all([flour, cake])
    db_session.commit()
    db_session.refresh(flour)
    db_session.refresh(cake)

    db_session.add(
        RecipeItem(
            product_id=cake.id,
            ingredient_id=flour.id,
            unit_id=unit_kg.id,
            quantity=1.0,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/check",
        json={"product_id": cake.id, "order_quantity": 1},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["can_be_fulfilled"] is False
    req = data["ingredients_requirements"][0]
    assert req["required_in_inventory_unit"] == 1000.0
    assert req["available_in_inventory_unit"] == 700.0
    assert req["missing_in_inventory_unit"] == 300.0


def test_confirm_reserves_stock_atomically(client, db_session):
    unit_g = Unit(name="Gramo confirm", abbreviation="g-c", base_factor=1.0)
    unit_kg = Unit(name="Kilogramo confirm", abbreviation="kg-c", base_factor=1000.0)
    db_session.add_all([unit_g, unit_kg])
    db_session.commit()
    db_session.refresh(unit_g)
    db_session.refresh(unit_kg)

    flour = Ingredient(
        name="Harina confirm",
        unit_id=unit_g.id,
        stock_fisico=2000,
        stock_reservado=100,
        stock_minimo=0,
    )
    cake = Product(name="Torta confirm", description="test", price=1000)
    db_session.add_all([flour, cake])
    db_session.commit()
    db_session.refresh(flour)
    db_session.refresh(cake)

    db_session.add(
        RecipeItem(
            product_id=cake.id,
            ingredient_id=flour.id,
            unit_id=unit_kg.id,
            quantity=0.5,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/confirm",
        json={"product_id": cake.id, "order_quantity": 2},
    )

    assert response.status_code == 200
    db_session.refresh(flour)
    assert flour.stock_reservado == 1100.0
    assert flour.stock_disponible == 900.0


def test_confirm_rolls_back_when_any_ingredient_is_missing(client, db_session):
    unit_g = Unit(name="Gramo rb", abbreviation="g-rb", base_factor=1.0)
    db_session.add(unit_g)
    db_session.commit()
    db_session.refresh(unit_g)

    flour = Ingredient(
        name="Harina rb",
        unit_id=unit_g.id,
        stock_fisico=1000,
        stock_reservado=0,
        stock_minimo=0,
    )
    eggs = Ingredient(
        name="Huevos rb",
        unit_id=unit_g.id,
        stock_fisico=2,
        stock_reservado=0,
        stock_minimo=0,
    )
    cake = Product(name="Torta rb", description="test", price=1000)
    db_session.add_all([flour, eggs, cake])
    db_session.commit()
    db_session.refresh(flour)
    db_session.refresh(eggs)
    db_session.refresh(cake)

    db_session.add_all(
        [
            RecipeItem(
                product_id=cake.id,
                ingredient_id=flour.id,
                unit_id=unit_g.id,
                quantity=100.0,
            ),
            RecipeItem(
                product_id=cake.id,
                ingredient_id=eggs.id,
                unit_id=unit_g.id,
                quantity=5.0,
            ),
        ]
    )
    db_session.commit()

    response = client.post(
        "/api/v1/confirm",
        json={"product_id": cake.id, "order_quantity": 1},
    )

    assert response.status_code == 409
    db_session.refresh(flour)
    db_session.refresh(eggs)
    assert flour.stock_reservado == 0
    assert eggs.stock_reservado == 0
