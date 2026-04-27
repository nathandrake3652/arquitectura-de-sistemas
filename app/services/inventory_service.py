from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.ingredient import Ingredient
from app.models.stock_movement import StockMovement
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

    def calculate_requirement(self, ingredient: Ingredient, recipe_unit: Unit, required_quantity: float) -> dict:
        """Calcula cantidades requeridas/faltantes en la unidad del inventario."""
        required_in_inventory_unit = convert(
            value=required_quantity,
            from_unit=recipe_unit,
            to_unit=ingredient.unit,
        )
        missing_quantity = max(0.0, required_in_inventory_unit - ingredient.stock_disponible)

        return {
            "required_in_recipe_unit": required_quantity,
            "recipe_unit": recipe_unit.abbreviation,
            "required_in_inventory_unit": required_in_inventory_unit,
            "inventory_unit": ingredient.unit.abbreviation,
            "available_in_inventory_unit": ingredient.stock_disponible,
            "missing_in_inventory_unit": missing_quantity,
            "is_available": missing_quantity == 0,
        }

    def adjust_stock(self, ingredient_id: int, tipo: str, cantidad: float, motivo: str) -> dict:
        ingredient = (
            self.db.query(Ingredient)
            .filter(Ingredient.id == ingredient_id)
            .with_for_update()
            .first()
        )
        if not ingredient:
            raise ValueError(f"Ingrediente con id {ingredient_id} no encontrado")

        if tipo == "entrada_compra":
            ingredient.stock_fisico += cantidad
        elif tipo == "salida_merma":
            if ingredient.stock_fisico - cantidad < ingredient.stock_reservado:
                raise ValueError("No hay stock disponible suficiente para registrar merma")
            ingredient.stock_fisico -= cantidad
        else:
            raise ValueError("Tipo de ajuste no soportado")

        movement = StockMovement(
            ingredient_id=ingredient.id,
            cantidad=cantidad,
            tipo=tipo,
            motivo=motivo,
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(ingredient)
        self.db.refresh(movement)

        #Evaluar el estado del stock disponible para alerta
        alert_triggered = ingredient.stock_disponible < ingredient.stock_minimo

        return {
            "ingredient_id": ingredient.id,
            "ingredient_name": ingredient.name,
            "tipo": movement.tipo,
            "cantidad": movement.cantidad,
            "motivo": movement.motivo,
            "fecha": movement.fecha.isoformat(),
            "stock_fisico": ingredient.stock_fisico,
            "stock_reservado": ingredient.stock_reservado,
            "stock_disponible": ingredient.stock_disponible,
            "low_stock_alert": alert_triggered,
            "min_stock_level": ingredient.stock_minimo
        }

    def get_stock_movements(self, ingredient_id: int = None, movement_type: str = None) -> list:
        """Obtiene historial de movimientos de stock con filtros opcionales."""
        query = self.db.query(StockMovement).order_by(StockMovement.fecha.desc())
        
        if ingredient_id:
            query = query.filter(StockMovement.ingredient_id == ingredient_id)
        
        if movement_type:
            query = query.filter(StockMovement.tipo == movement_type)
        
        movements = query.all()
        return movements

    def get_movements_with_details(self, ingredient_id: int = None, movement_type: str = None, fecha: str = None, page: int = 1, per_page: int = 10) -> dict:
        """Obtiene movimientos con detalles del ingrediente para display."""
        query = self.db.query(StockMovement).order_by(StockMovement.fecha.desc())
        
        if ingredient_id:
            query = query.filter(StockMovement.ingredient_id == ingredient_id)
        if movement_type:
            query = query.filter(StockMovement.tipo == movement_type)
        if fecha:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            # Filtra ignorando horas (convirtiendo a date)
            query = query.filter(func.date(StockMovement.fecha) == fecha_obj)
            
        total_items = query.count()
        total_pages = (total_items + per_page - 1) // per_page
        
        start_idx = (page - 1) * per_page
        movements = query.offset(start_idx).limit(per_page).all()
        
        result = []
        for movement in movements:
            ingredient = self.db.query(Ingredient).filter(Ingredient.id == movement.ingredient_id).first()
            result.append({
                "id": movement.id,
                "ingredient_name": ingredient.name if ingredient else "Desconocido",
                "ingredient_id": movement.ingredient_id,
                "cantidad": movement.cantidad,
                "tipo": movement.tipo,
                "motivo": movement.motivo,
                "fecha": movement.fecha,
                "unit": ingredient.unit.abbreviation if ingredient else ""
            })
        
        return {
            "movimientos": result,
            "total_pages": max(total_pages, 1),
            "current_page": page,
            "has_items": total_items > 0
        }

    def get_movements_summary(self) -> dict:
        """Obtiene resumen de movimientos en total de dinero."""
        from app.models.order_ticket import OrderTicket

        movements = self.db.query(StockMovement).all()
        
        summary = {
            "entrada_compra": {"count": 0, "total": 0},
            "salida_merma": {"count": 0, "total": 0},
            "salida_produccion": {"count": 0, "total": 0},
        }
        
        for movement in movements:
            ingredient = movement.ingredient
            # El precio de ingredientes en gramos o mililitros representa el precio por Kilo o Litro
            if ingredient.unit.abbreviation in ['g', 'ml']:
                precio_unitario = ingredient.price / 1000.0
            else:
                precio_unitario = ingredient.price

            if movement.tipo == "salida_produccion":
                summary["salida_produccion"]["count"] += 1
            else:
                if movement.tipo not in summary:
                    summary[movement.tipo] = {"count": 0, "total": 0}
                valor_movimiento = float(movement.cantidad) * float(precio_unitario)
                summary[movement.tipo]["count"] += 1
                summary[movement.tipo]["total"] += valor_movimiento

        # El costo/ingreso de producción ahora se valora usando el precio del producto vendido
        orders = self.db.query(OrderTicket).filter(OrderTicket.status.in_(["entregado", "listo", "confirmado", "preparando"])).all()
        total_produccion = sum(float(order.order_quantity) * float(order.product.price) for order in orders)
        summary["salida_produccion"]["total"] = total_produccion
        
        return summary