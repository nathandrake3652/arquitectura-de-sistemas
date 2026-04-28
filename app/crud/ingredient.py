from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.ingredient import Ingredient
from app.models.unit import Unit
from app.schemas.ingredient import IngredientCreate


def create_ingredient(db: Session, payload: IngredientCreate) -> Ingredient:
    # Validar que la unidad existe
    unit = db.query(Unit).filter(Unit.id == payload.unit_id).first()
    if not unit:
        raise ValueError(f"Unit with id {payload.unit_id} does not exist")
    
    try:
        ingredient = Ingredient(
            name=payload.name,
            unit_id=payload.unit_id,
            stock_fisico=payload.stock_fisico,
            stock_reservado=payload.stock_reservado,
            stock_minimo=payload.stock_minimo,
            price=payload.price,
        )
        db.add(ingredient)
        db.commit()
        db.refresh(ingredient)
        return ingredient
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Ingredient with name '{payload.name}' already exists")


def get_ingredients(db: Session) -> list[Ingredient]:
    return db.query(Ingredient).all()


def get_ingredient(db: Session, ingredient_id: int) -> Ingredient:
    return db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()


def update_ingredient_stock(db: Session, ingredient_id: int, stock_fisico: float = None, 
                           stock_reservado: float = None, stock_minimo: float = None) -> Ingredient:
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise ValueError(f"Ingredient with id {ingredient_id} does not exist")
    
    if stock_fisico is not None:
        ingredient.stock_fisico = stock_fisico
    if stock_reservado is not None:
        ingredient.stock_reservado = stock_reservado
    if stock_minimo is not None:
        ingredient.stock_minimo = stock_minimo
    
    db.commit()
    db.refresh(ingredient)
    return ingredient


def delete_ingredient(db: Session, ingredient_id: int) -> bool:
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise ValueError(f"Ingredient with id {ingredient_id} does not exist")
    
    db.delete(ingredient)
    db.commit()
    return True

