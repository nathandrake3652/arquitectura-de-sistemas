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
from app.schemas.order import InventoryAdjustmentRequest
from app.services.inventory_service import InventoryService

router = APIRouter(tags=["Gestión de Inventario e Ingredientes"])


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


@router.post("/{ingredient_id}/adjustments", status_code=status.HTTP_200_OK)
def adjust_ingredient_stock(
    ingredient_id: int,
    payload: InventoryAdjustmentRequest,
    db: Session = Depends(get_db),
):
    service = InventoryService(db)
    try:
        return service.adjust_stock(
            ingredient_id=ingredient_id,
            tipo=payload.tipo,
            cantidad=payload.cantidad,
            motivo=payload.motivo,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "no encontrado" in message.lower() else status.HTTP_409_CONFLICT
        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc
