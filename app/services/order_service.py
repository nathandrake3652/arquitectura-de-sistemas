from sqlalchemy.orm import Session
from app.core.exceptions import DomainException
from app.models.product import Product
from app.models.ingredient import Ingredient
from app.models.stock_movement import StockMovement
from app.services.inventory_service import InventoryService


class InsufficientStockError(DomainException):
    def __init__(self, shortages: list[dict]):
        self.shortages = shortages
        super().__init__("Stock insuficiente para confirmar el pedido")

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
            requirement_detail = self.inventory_service.calculate_requirement(
                ingredient=item.ingredient,
                recipe_unit=item.unit,
                required_quantity=total_required,
            )

            requirements.append({
                "ingredient_id": item.ingredient_id,
                "ingredient_name": item.ingredient.name,
                **requirement_detail,
            })

        return {
            "product_id": product.id,
            "product_name": product.name,
            "order_quantity": order_quantity,
            "ingredients_requirements": requirements,
            "can_be_fulfilled": all(req["is_available"] for req in requirements)
        }

    def confirm_order(self, product_id: int, order_quantity: int) -> dict:
        """Confirma un pedido de forma atómica moviendo stock disponible a reservado."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Producto no encontrado")
        if not product.recipe_items:
            raise ValueError("El producto no tiene receta asociada")

        recipe_items_by_ingredient: dict[int, list] = {}
        for item in product.recipe_items:
            recipe_items_by_ingredient.setdefault(item.ingredient_id, []).append(item)

        locked_ingredients: dict[int, Ingredient] = {}
        requirements: dict[int, dict] = {}
        shortages: list[dict] = []

        for ingredient_id, items in recipe_items_by_ingredient.items():
            ingredient = (
                self.db.query(Ingredient)
                .filter(Ingredient.id == ingredient_id)
                .with_for_update()
                .one()
            )
            locked_ingredients[ingredient_id] = ingredient

            required_in_inventory_unit = 0.0
            for item in items:
                required_in_inventory_unit += self.inventory_service.calculate_requirement(
                    ingredient=ingredient,
                    recipe_unit=item.unit,
                    required_quantity=item.quantity * order_quantity,
                )["required_in_inventory_unit"]

            requirements[ingredient_id] = {
                "ingredient_id": ingredient.id,
                "ingredient_name": ingredient.name,
                "required_in_inventory_unit": required_in_inventory_unit,
                "inventory_unit": ingredient.unit.abbreviation,
            }

            missing = max(
                0.0,
                required_in_inventory_unit - ingredient.stock_disponible,
            )
            if missing > 0:
                shortages.append(
                    {
                        "ingredient_id": ingredient.id,
                        "ingredient_name": ingredient.name,
                        "required_in_inventory_unit": required_in_inventory_unit,
                        "available_in_inventory_unit": ingredient.stock_disponible,
                        "missing_in_inventory_unit": missing,
                        "inventory_unit": ingredient.unit.abbreviation,
                    }
                )

        if shortages:
            self.db.rollback()
            raise InsufficientStockError(shortages)

        for ingredient_id, requirement in requirements.items():
            ingredient = locked_ingredients[ingredient_id]
            ingredient.stock_reservado += requirement["required_in_inventory_unit"]

        self.db.commit()

        return {
            "product_id": product.id,
            "product_name": product.name,
            "order_quantity": order_quantity,
            "reserved_ingredients": [
                {
                    "ingredient_id": req["ingredient_id"],
                    "ingredient_name": req["ingredient_name"],
                    "reserved_in_inventory_unit": req["required_in_inventory_unit"],
                    "inventory_unit": req["inventory_unit"],
                }
                for req in requirements.values()
            ],
            "status": "confirmed",
        }

    def finish_order(self, product_id: int, order_quantity: int, status: str) -> dict:
        """Finaliza producción de un pedido: consume físico y libera reservado."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Producto no encontrado")
        if not product.recipe_items:
            raise ValueError("El producto no tiene receta asociada")

        recipe_items_by_ingredient: dict[int, list] = {}
        for item in product.recipe_items:
            recipe_items_by_ingredient.setdefault(item.ingredient_id, []).append(item)

        requirements: dict[int, dict] = {}
        shortages: list[dict] = []

        for ingredient_id, items in recipe_items_by_ingredient.items():
            ingredient = (
                self.db.query(Ingredient)
                .filter(Ingredient.id == ingredient_id)
                .with_for_update()
                .one()
            )

            required_in_inventory_unit = 0.0
            for item in items:
                required_in_inventory_unit += self.inventory_service.calculate_requirement(
                    ingredient=ingredient,
                    recipe_unit=item.unit,
                    required_quantity=item.quantity * order_quantity,
                )["required_in_inventory_unit"]

            requirements[ingredient.id] = {
                "ingredient": ingredient,
                "ingredient_id": ingredient.id,
                "ingredient_name": ingredient.name,
                "required_in_inventory_unit": required_in_inventory_unit,
                "inventory_unit": ingredient.unit.abbreviation,
            }

            if ingredient.stock_reservado < required_in_inventory_unit:
                shortages.append(
                    {
                        "ingredient_id": ingredient.id,
                        "ingredient_name": ingredient.name,
                        "required_reserved": required_in_inventory_unit,
                        "current_reserved": ingredient.stock_reservado,
                        "missing_reserved": required_in_inventory_unit - ingredient.stock_reservado,
                        "inventory_unit": ingredient.unit.abbreviation,
                    }
                )

        if shortages:
            self.db.rollback()
            raise InsufficientStockError(shortages)

        for requirement in requirements.values():
            ingredient = requirement["ingredient"]
            consumed = requirement["required_in_inventory_unit"]

            ingredient.stock_reservado -= consumed
            ingredient.stock_fisico -= consumed

            self.db.add(
                StockMovement(
                    ingredient_id=ingredient.id,
                    cantidad=consumed,
                    tipo="salida_produccion",
                    motivo=f"{status}: {product.name}",
                )
            )

        self.db.commit()

        return {
            "product_id": product.id,
            "product_name": product.name,
            "order_quantity": order_quantity,
            "status": status,
            "consumed_ingredients": [
                {
                    "ingredient_id": req["ingredient_id"],
                    "ingredient_name": req["ingredient_name"],
                    "consumed_in_inventory_unit": req["required_in_inventory_unit"],
                    "inventory_unit": req["inventory_unit"],
                }
                for req in requirements.values()
            ],
        }