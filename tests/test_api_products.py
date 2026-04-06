def test_create_product(client):
    payload = {
        "name": "Torta Tres Leches",
        "description": "Prueba de creación de producto API",
        "price": 15000,
    }
    response = client.post("/api/v1/products/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["price"] == payload["price"]
    assert "id" in data