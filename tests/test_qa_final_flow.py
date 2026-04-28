from app.models.stock_movement import StockMovement
from app.models.unit import Unit


def test_full_flow_ingreso_confirm_entrega_historial(client, db_session):
    # Unit setup for the ingredient and recipe endpoint payloads.
    unit_g = Unit(name="Gramo QA", abbreviation="g-qa", base_factor=1.0)
    db_session.add(unit_g)
    db_session.commit()
    db_session.refresh(unit_g)

    ingredient_response = client.post(
        "/api/v1/ingredients",
        json={
            "name": "Harina QA Final",
            "unit_id": unit_g.id,
            "stock_fisico": 0.0,
            "stock_reservado": 0.0,
            "stock_minimo": 100.0,
        },
    )
    assert ingredient_response.status_code == 201
    ingredient = ingredient_response.json()

    ingreso_response = client.post(
        f"/api/v1/ingredients/{ingredient['id']}/adjustments",
        json={
            "tipo": "entrada_compra",
            "cantidad": 1200.0,
            "motivo": "Ingreso inicial QA final",
        },
    )
    assert ingreso_response.status_code == 200

    product_response = client.post(
        "/api/v1/products",
        json={
            "name": "Producto QA Final",
            "description": "Producto para flujo completo",
            "price": 10000,
        },
    )
    assert product_response.status_code == 201
    product = product_response.json()

    recipe_response = client.post(
        "/api/v1/recipe-items",
        json={
            "product_id": product["id"],
            "ingredient_id": ingredient["id"],
            "unit_id": unit_g.id,
            "quantity": 400.0,
        },
    )
    assert recipe_response.status_code == 201

    check_payload = {
        "product_id": product["id"],
        "order_quantity": 2,
    }

    check_response = client.post("/api/v1/check", json=check_payload)
    assert check_response.status_code == 200
    check_data = check_response.json()
    assert check_data["can_be_fulfilled"] is True

    confirm_response = client.post("/api/v1/confirm", json=check_payload)
    assert confirm_response.status_code == 200

    finish_response = client.post(
        "/api/v1/finish",
        json={
            "product_id": product["id"],
            "order_quantity": 2,
            "status": "entregado",
        },
    )
    assert finish_response.status_code == 200

    ingredient_after = client.get(f"/api/v1/ingredients/{ingredient['id']}")
    assert ingredient_after.status_code == 200
    ingredient_data = ingredient_after.json()
    assert ingredient_data["stock_fisico"] == 400.0
    assert ingredient_data["stock_reservado"] == 0.0
    assert ingredient_data["stock_disponible"] == 400.0

    movements = (
        db_session.query(StockMovement)
        .filter(StockMovement.ingredient_id == ingredient["id"])
        .order_by(StockMovement.id)
        .all()
    )
    assert len(movements) == 2
    assert movements[0].tipo == "entrada_compra"
    assert movements[0].cantidad == 1200.0
    assert movements[1].tipo == "salida_produccion"
    assert movements[1].cantidad == 800.0
    assert "entregado" in movements[1].motivo.lower()
