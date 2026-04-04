from sqlalchemy.orm import Session

from app.models.recipe_item import RecipeItem
from app.models.product import Product
from app.models.ingredient import Ingredient
from app.models.unit import Unit
from app.schemas.recipe_item import RecipeItemCreate


def create_recipe_item(db: Session, payload: RecipeItemCreate) -> RecipeItem:
    # Validar que el producto existe
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise ValueError(f"Product with id {payload.product_id} does not exist")
    
    # Validar que el ingrediente existe
    ingredient = db.query(Ingredient).filter(Ingredient.id == payload.ingredient_id).first()
    if not ingredient:
        raise ValueError(f"Ingredient with id {payload.ingredient_id} does not exist")
    
    # Validar que la unidad existe
    unit = db.query(Unit).filter(Unit.id == payload.unit_id).first()
    if not unit:
        raise ValueError(f"Unit with id {payload.unit_id} does not exist")
    
    recipe_item = RecipeItem(
        product_id=payload.product_id,
        ingredient_id=payload.ingredient_id,
        unit_id=payload.unit_id,
        quantity=payload.quantity,
    )
    db.add(recipe_item)
    db.commit()
    db.refresh(recipe_item)
    return recipe_item


def get_recipe_items(db: Session) -> list[RecipeItem]:
    return db.query(RecipeItem).all()


def get_recipe_item(db: Session, recipe_item_id: int) -> RecipeItem:
    return db.query(RecipeItem).filter(RecipeItem.id == recipe_item_id).first()


def get_recipe_items_by_product(db: Session, product_id: int) -> list[RecipeItem]:
    return db.query(RecipeItem).filter(RecipeItem.product_id == product_id).all()


def delete_recipe_item(db: Session, recipe_item_id: int) -> bool:
    recipe_item = db.query(RecipeItem).filter(RecipeItem.id == recipe_item_id).first()
    if not recipe_item:
        raise ValueError(f"RecipeItem with id {recipe_item_id} does not exist")
    
    db.delete(recipe_item)
    db.commit()
    return True
