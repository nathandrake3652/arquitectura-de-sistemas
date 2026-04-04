from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.ingredient import (
    create_ingredient,
    get_ingredients,
    get_ingredient,
    update_ingredient_stock,
)
from app.db.session import get_db
from app.schemas.ingredient import IngredientCreate, IngredientRead

router = APIRouter()


@router.get("", response_model=list[IngredientRead])
def list_ingredients(db: Session = Depends(get_db)):
    return get_ingredients(db)


@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
def add_ingredient(payload: IngredientCreate, db: Session = Depends(get_db)):
    try:
        return create_ingredient(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{ingredient_id}", response_model=IngredientRead)
def get_ingredient_detail(ingredient_id: int, db: Session = Depends(get_db)):
    ingredient = get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {ingredient_id} not found",
        )
    return ingredient
