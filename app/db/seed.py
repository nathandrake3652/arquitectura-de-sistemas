from app.db.session import SessionLocal
from app.models.ingredient import Ingredient
from app.models.order_ticket import OrderTicket
from app.models.product import Product
from app.models.recipe_item import RecipeItem
from app.models.stock_movement import StockMovement
from app.models.unit import Unit


def _get_or_create_unit(db, name: str, abbreviation: str, base_factor: float) -> Unit:
    unit = db.query(Unit).filter(Unit.abbreviation == abbreviation).first()
    if unit:
        return unit
    unit = Unit(name=name, abbreviation=abbreviation, base_factor=base_factor)
    db.add(unit)
    db.flush()
    return unit


def _get_or_create_ingredient(
    db,
    name: str,
    unit_id: int,
    stock_fisico: float,
    stock_reservado: float,
    stock_minimo: float,
    price: int,
) -> Ingredient:
    ingredient = db.query(Ingredient).filter(Ingredient.name == name).first()
    if ingredient:
        ingredient.unit_id = unit_id
        ingredient.stock_fisico = stock_fisico
        ingredient.stock_reservado = stock_reservado
        ingredient.stock_minimo = stock_minimo
        ingredient.price = price
        return ingredient

    ingredient = Ingredient(
        name=name,
        unit_id=unit_id,
        stock_fisico=stock_fisico,
        stock_reservado=stock_reservado,
        stock_minimo=stock_minimo,
        price=price,
    )
    db.add(ingredient)
    db.flush()
    return ingredient


def _get_or_create_product(db, name: str, description: str, price: int) -> Product:
    product = db.query(Product).filter(Product.name == name).first()
    if product:
        product.description = description
        product.price = price
        return product

    product = Product(name=name, description=description, price=price)
    db.add(product)
    db.flush()
    return product


def _upsert_recipe_item(
    db,
    product_id: int,
    ingredient_id: int,
    unit_id: int,
    quantity: float,
) -> RecipeItem:
    recipe_item = (
        db.query(RecipeItem)
        .filter(
            RecipeItem.product_id == product_id,
            RecipeItem.ingredient_id == ingredient_id,
        )
        .first()
    )
    if recipe_item:
        recipe_item.unit_id = unit_id
        recipe_item.quantity = quantity
        return recipe_item

    recipe_item = RecipeItem(
        product_id=product_id,
        ingredient_id=ingredient_id,
        unit_id=unit_id,
        quantity=quantity,
    )
    db.add(recipe_item)
    db.flush()
    return recipe_item

def _create_stock_movement(db, ingredient_id: int, cantidad: float, tipo: str, motivo: str):
    # Verificamos si existe por si ejecutamos el seed múltiples veces (solo revisando motivo y cantidad)
    mov = db.query(StockMovement).filter(
        StockMovement.ingredient_id == ingredient_id,
        StockMovement.cantidad == cantidad,
        StockMovement.tipo == tipo,
        StockMovement.motivo == motivo
    ).first()
    if not mov:
        mov = StockMovement(ingredient_id=ingredient_id, cantidad=cantidad, tipo=tipo, motivo=motivo)
        db.add(mov)
        db.flush()
    return mov


def _get_or_create_order_ticket(db, product_id: int, order_quantity: int, status: str) -> OrderTicket:
    ticket = db.query(OrderTicket).filter(
        OrderTicket.product_id == product_id,
        OrderTicket.order_quantity == order_quantity,
        OrderTicket.status == status
    ).first()
    if not ticket:
        ticket = OrderTicket(product_id=product_id, order_quantity=order_quantity, status=status)
        db.add(ticket)
        db.flush()
    return ticket


def populate_seed_data() -> None:
    with SessionLocal() as db:
        # Units
        unit_g = _get_or_create_unit(db, "Gramo", "g", 1.0)
        unit_kg = _get_or_create_unit(db, "Kilogramo", "kg", 1000.0)
        unit_ml = _get_or_create_unit(db, "Mililitro", "ml", 1.0)
        unit_l = _get_or_create_unit(db, "Litro", "l", 1000.0)
        unit_u = _get_or_create_unit(db, "Unidad", "u", 1.0)

        # Ingredients
        ing_harina = _get_or_create_ingredient(
            db, "Harina", unit_g.id, stock_fisico=5000.0, stock_reservado=0.0, stock_minimo=1000.0, price=1000
        )
        ing_huevos = _get_or_create_ingredient(
            db, "Huevos", unit_u.id, stock_fisico=30.0, stock_reservado=0.0, stock_minimo=12.0, price=250
        )
        ing_leche = _get_or_create_ingredient(
            db, "Leche", unit_ml.id, stock_fisico=10000.0, stock_reservado=0.0, stock_minimo=2000.0, price=1500
        )
        ing_azucar = _get_or_create_ingredient(
            db, "Azucar", unit_g.id, stock_fisico=4000.0, stock_reservado=0.0, stock_minimo=800.0, price=1000
        )
        ing_levadura = _get_or_create_ingredient(
            db, "Levadura", unit_g.id, stock_fisico=15.0, stock_reservado=0.0, stock_minimo=50.0, price=500
        )

        #Movements
        _create_stock_movement(db, ing_harina.id, 5000.0, "entrada_compra", "Stock Inicial (Carga de Sistema)")
        _create_stock_movement(db, ing_huevos.id, 32.0, "entrada_compra", "Stock Inicial (Carga de Sistema)")
        _create_stock_movement(db, ing_leche.id, 10000.0, "entrada_compra", "Stock Inicial (Carga de Sistema)")
        _create_stock_movement(db, ing_azucar.id, 4000.0, "entrada_compra", "Stock Inicial (Carga de Sistema)")
        _create_stock_movement(db, ing_levadura.id, 15.0, "entrada_compra", "Stock Inicial (Carga de Sistema)")
        #Merma
        _create_stock_movement(db, ing_huevos.id, 2.0, "salida_merma", "Huevos rotos en almacén")

        # Products
        prod_pastel = _get_or_create_product(
            db,
            name="Pastel Prueba",
            description="Producto base para probar check/confirm",
            price=15000,
        )
        prod_panqueques = _get_or_create_product(
            db,
            name="Panqueques",
            description="Producto alternativo para pruebas de catalogo",
            price=9000,
        )

        # Recipes (intentionally mixed units to test unit conversion)
        _upsert_recipe_item(db, prod_pastel.id, ing_harina.id, unit_kg.id, 0.5)   # 500 g
        _upsert_recipe_item(db, prod_pastel.id, ing_huevos.id, unit_u.id, 3.0)    # 3 unidades
        _upsert_recipe_item(db, prod_pastel.id, ing_leche.id, unit_l.id, 0.3)     # 300 ml
        _upsert_recipe_item(db, prod_pastel.id, ing_azucar.id, unit_g.id, 120.0)  # 120 g

        _upsert_recipe_item(db, prod_panqueques.id, ing_harina.id, unit_g.id, 200.0)
        _upsert_recipe_item(db, prod_panqueques.id, ing_huevos.id, unit_u.id, 2.0)
        _upsert_recipe_item(db, prod_panqueques.id, ing_leche.id, unit_ml.id, 350.0)

        db.commit()


if __name__ == "__main__":
    print("Iniciando poblado de datos...")
    populate_seed_data()
    print("Seed completado: unidades, ingredientes, productos y recetas listos.")