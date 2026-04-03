from app.db.session import SessionLocal
from app.models.ingredient import Ingredient
from app.models.recipe_item import RecipeItem
from app.models.unit import Unit
from app.models.product import Product

def populate_initial_units():
    with SessionLocal() as db:
        units_to_create = [
            {"name": "Gramo", "abbreviation": "g", "base_factor": 1.0},
            {"name": "Kilogramo", "abbreviation": "kg", "base_factor": 1000.0},
            {"name": "Mililitro", "abbreviation": "ml", "base_factor": 1.0},
            {"name": "Litro", "abbreviation": "l", "base_factor": 1000.0},
            {"name": "Unidad", "abbreviation": "u", "base_factor": 1.0},
        ]

        for unit_data in units_to_create:
            existing = db.query(Unit).filter(Unit.abbreviation == unit_data["abbreviation"]).first()
            if not existing:
                new_unit = Unit(**unit_data)
                db.add(new_unit)
        
        db.commit()

        #Poblado ingredientes de prueba
        unit_g = db.query(Unit).filter(Unit.abbreviation == "g").first()
        unit_u = db.query(Unit).filter(Unit.abbreviation == "u").first()

        ing_harina = db.query(Ingredient).filter(Ingredient.name == "Harina").first()
        if not ing_harina and unit_g:
            ing_harina = Ingredient(name="Harina", unit_id=unit_g.id, stock_fisico=5000, stock_reservado=0, stock_minimo=1000)
            db.add(ing_harina)

        ing_huevos = db.query(Ingredient).filter(Ingredient.name == "Huevos").first()
        if not ing_huevos and unit_u:
            ing_huevos = Ingredient(name="Huevos", unit_id=unit_u.id, stock_fisico=30, stock_reservado=0, stock_minimo=12)
            db.add(ing_huevos)

        db.commit()

        #poblado de producto y receta de prueba
        prod_pastel = db.query(Product).filter(Product.name == "Pastel Prueba").first()
        if not prod_pastel:
            prod_pastel = Product(name="Pastel Prueba", description="Un pastel de prueba para la receta", price=15.0)
            db.add(prod_pastel)
            db.commit()
            db.refresh(prod_pastel)

            #ejemplo receta de 500gramos harina y 3 huevos
            if ing_harina and ing_huevos:
                db.add(RecipeItem(product_id=prod_pastel.id, ingredient_id=ing_harina.id, quantity=500))
                db.add(RecipeItem(product_id=prod_pastel.id, ingredient_id=ing_huevos.id, quantity=3))
                db.commit()

if __name__ == "__main__":
    print("Iniciando poblado de datos...")
    populate_initial_units()
    print("Unidades registradas en la base de datos exitosamente.")