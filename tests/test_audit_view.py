import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db


@pytest.fixture
def client(db_session):
    """Cliente de prueba con inyección de dependencia."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


class TestAuditView:
    def test_audit_page_loads(self, client):
        """Verifica que la página de auditoría carga correctamente."""
        response = client.get("/ui/audit")
        assert response.status_code == 200
        assert "Auditoría" in response.text
        assert "Trazabilidad" in response.text

    def test_audit_page_has_filters(self, client):
        """Verifica que la página contiene filtros."""
        response = client.get("/ui/audit")
        assert response.status_code == 200
        assert "ingredient_id" in response.text
        assert "movement_type" in response.text
        assert "Entrada de Compra" in response.text
        assert "Salida por Merma" in response.text

    def test_audit_page_has_summary(self, client):
        """Verifica que la página muestra resumen estadístico."""
        response = client.get("/ui/audit")
        assert response.status_code == 200
        assert "Entradas de Compra" in response.text
        assert "Salidas por Merma" in response.text
        assert "Salidas por Producción" in response.text

    def test_audit_page_with_ingredient_filter(self, client, db_session):
        """Verifica filtro por ingrediente."""
        from app.crud.ingredient import get_ingredients
        
        ingredients = get_ingredients(db_session)
        if ingredients:
            first_ingredient = ingredients[0]
            response = client.get(f"/ui/audit?ingredient_id={first_ingredient.id}")
            assert response.status_code == 200
            assert first_ingredient.name in response.text

    def test_audit_page_with_empty_ingredient_filter(self, client):
        """Verifica que el filtro vacío no rompe la vista."""
        response = client.get("/ui/audit?ingredient_id=")
        assert response.status_code == 200
        assert "Auditoría y Trazabilidad" in response.text

    def test_audit_page_with_movement_type_filter(self, client):
        """Verifica filtro por tipo de movimiento."""
        response = client.get("/ui/audit?movement_type=entrada_compra")
        assert response.status_code == 200
        assert "Entrada de Compra" in response.text

    def test_audit_page_with_type_and_empty_ingredient(self, client):
        """Verifica que el tipo de movimiento funciona aunque el ingrediente esté en blanco."""
        response = client.get("/ui/audit?ingredient_id=&movement_type=salida_merma")
        assert response.status_code == 200
        assert "Salida por Merma" in response.text

    def test_audit_movements_table(self, client):
        """Verifica que la tabla de movimientos existe."""
        response = client.get("/ui/audit")
        assert response.status_code == 200
        assert "movements-table" in response.text
        assert "<table" in response.text
        assert "Fecha" in response.text
        assert "Ingrediente" in response.text
        assert "Tipo" in response.text
        assert "Cantidad" in response.text
        assert "Motivo" in response.text

    def test_audit_partial_response_for_htmx(self, client):
        """Verifica que HTMX recibe solo el fragmento de resultados."""
        response = client.get("/ui/audit", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "audit-panel" in response.text
        assert "movements-table" in response.text
        assert "<html" not in response.text
