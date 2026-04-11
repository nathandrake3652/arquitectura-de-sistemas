from sqlalchemy.orm import Session
from app.models.product import Product
from app.services.inventory_service import InventoryService

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)

    def analyze_order_requirements(self, product_id: int, order_quantity: int) -> dict:
        #Consulta la receta del producto, multiplica por la cantidad y calcula ingredientes necesarios
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Producto no encontrado")
        
        requirements = []
        for item in product.recipe_items:
            total_required = item.quantity * order_quantity
            #consulta con inventoryService si hay stock
            is_available = self.inventory_service.check_availability(
                ingredient_id=item.ingredient_id,
                required_quantity=total_required,
                recipe_unit_id=item.unit_id
            )
        
            requirements.append({
                "ingredient_id": item.ingredient_id,
                "ingredient_name": item.ingredient.name,
                "required_quantity": total_required,
                "unit": item.unit.abbreviation,
                "is_available": is_available
            })

        return {
            "product_name": product.name,
            "order_quantity": order_quantity,
            "ingredients_requirements": requirements,
            "can_be_fulfilled": all(req["is_available"] for req in requirements)
        }