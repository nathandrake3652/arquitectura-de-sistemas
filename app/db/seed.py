from app.db.session import SessionLocal
from app.models.unit import Unit

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

if __name__ == "__main__":
    print("Iniciando poblado de datos...")
    populate_initial_units()
    print("Unidades registradas en la base de datos exitosamente.")