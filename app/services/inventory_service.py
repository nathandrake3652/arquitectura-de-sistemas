from sqlalchemy.orm import Session
from app.models.ingredient import Ingredient
from app.models.unit import Unit
from app.utils.unit_converter import convert


class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_stock_status(self, ingredient_id: int) -> dict:
        #Devuelve el estado actual de un ingrediente
        ingredient = self.db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            raise ValueError(f"Ingrediente con id {ingredient_id} no encontrado")
        return {
            "id": ingredient.id,
            "name": ingredient.name,
            "stock_fisico": ingredient.stock_fisico,
            "stock_reservado": ingredient.stock_reservado,
            "stock_disponible": ingredient.stock_disponible
        }
    
    def check_availability(self, ingredient_id: int, required_quantity:float, recipe_unit_id: int) -> bool:
        #Verifica si hay stock suficiente y aplica la conversion de unidades
        ingredient = self.db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        recipe_unit = self.db.query(Unit).filter(Unit.id == recipe_unit_id).first()

        if not ingredient or not recipe_unit:
            raise ValueError("Ingrediente o unidad no encontrados")
        
        #Conversion de unidades
        quantity_in_inventory_unit = convert( value=required_quantity, from_unit=recipe_unit, to_unit=ingredient.unit)
        return ingredient.stock_disponible >= quantity_in_inventory_unit