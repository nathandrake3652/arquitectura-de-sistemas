import threading
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import Base
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe_item import RecipeItem
from app.models.unit import Unit
from app.services.order_service import InsufficientStockError, OrderService


def _postgres_url() -> str:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("Concurrency integration test requires PostgreSQL")
    return settings.database_url


@pytest.fixture(scope="function")
def postgres_session_factory():
    engine = create_engine(_postgres_url())
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _create_catalog(session, suffix: str) -> tuple[Unit, Unit, Ingredient, Product]:
    unit_inventory = Unit(
        name=f"Gramo stock {suffix}",
        abbreviation=f"g-{suffix}",
        base_factor=1.0,
    )
    unit_recipe = Unit(
        name=f"Kilogramo receta {suffix}",
        abbreviation=f"kg-{suffix}",
        base_factor=1000.0,
    )
    session.add_all([unit_inventory, unit_recipe])
    session.commit()
    session.refresh(unit_inventory)
    session.refresh(unit_recipe)

    ingredient = Ingredient(
        name=f"Harina concurrencia {suffix}",
        unit_id=unit_inventory.id,
        stock_fisico=1000.0,
        stock_reservado=0.0,
        stock_minimo=0.0,
    )
    product = Product(
        name=f"Torta concurrencia {suffix}",
        description="test de concurrencia",
        price=1000,
    )
    session.add_all([ingredient, product])
    session.commit()
    session.refresh(ingredient)
    session.refresh(product)

    session.add(
        RecipeItem(
            product_id=product.id,
            ingredient_id=ingredient.id,
            unit_id=unit_recipe.id,
            quantity=1.0,
        )
    )
    session.commit()

    return unit_inventory, unit_recipe, ingredient, product


def test_two_orders_compete_for_same_stock_with_row_lock(postgres_session_factory):
    suffix = uuid.uuid4().hex[:8]
    session_a = postgres_session_factory()
    unit_inventory = unit_recipe = ingredient = product = None

    try:
        unit_inventory, unit_recipe, ingredient, product = _create_catalog(session_a, suffix)

        # Reserva el stock del primer pedido sin soltar la transacción, dejando la fila bloqueada.
        locked_ingredient = (
            session_a.query(Ingredient)
            .filter(Ingredient.id == ingredient.id)
            .with_for_update()
            .one()
        )
        locked_ingredient.stock_reservado += 800.0

        second_result: dict[str, object] = {}
        started = threading.Event()
        finished = threading.Event()

        def run_second_order() -> None:
            session_b = postgres_session_factory()
            try:
                started.set()
                service = OrderService(session_b)
                try:
                    second_result["value"] = service.confirm_order(product.id, 1)
                except Exception as exc:  # pragma: no cover - the test asserts the concrete type below
                    second_result["error"] = exc
            finally:
                session_b.close()
                finished.set()

        thread = threading.Thread(target=run_second_order, daemon=True)
        thread.start()

        assert started.wait(timeout=1), "La segunda orden no llegó a ejecutarse"
        assert not finished.wait(timeout=0.5), "La segunda orden no debería terminar antes de liberar el bloqueo"

        session_a.commit()
        thread.join(timeout=5)

        assert finished.is_set(), "La segunda orden no terminó"
        assert "error" in second_result
        assert isinstance(second_result["error"], InsufficientStockError)

        shortage = second_result["error"].shortages[0]
        assert shortage["ingredient_id"] == ingredient.id
        assert shortage["missing_in_inventory_unit"] == 800.0

        verification_session = postgres_session_factory()
        try:
            refreshed_ingredient = verification_session.query(Ingredient).filter(Ingredient.id == ingredient.id).one()
            assert refreshed_ingredient.stock_reservado == 800.0
            assert refreshed_ingredient.stock_disponible == 200.0
        finally:
            verification_session.close()
    finally:
        cleanup_session = postgres_session_factory()
        try:
            if product is not None:
                cleanup_session.query(RecipeItem).filter(RecipeItem.product_id == product.id).delete(synchronize_session=False)
            if ingredient is not None:
                cleanup_session.query(Ingredient).filter(Ingredient.id == ingredient.id).delete(synchronize_session=False)
            if product is not None:
                cleanup_session.query(Product).filter(Product.id == product.id).delete(synchronize_session=False)
            if unit_recipe is not None:
                cleanup_session.query(Unit).filter(Unit.id == unit_recipe.id).delete(synchronize_session=False)
            if unit_inventory is not None:
                cleanup_session.query(Unit).filter(Unit.id == unit_inventory.id).delete(synchronize_session=False)
            cleanup_session.commit()
        finally:
            cleanup_session.close()
            session_a.close()