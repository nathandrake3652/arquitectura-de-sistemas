from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.recipe_item import (
    create_recipe_item,
    get_recipe_items,
    get_recipe_item,
    get_recipe_items_by_product,
    delete_recipe_item,
)
from app.db.session import get_db
from app.schemas.recipe_item import RecipeItemCreate, RecipeItemRead

router = APIRouter()


@router.get("", response_model=list[RecipeItemRead])
def list_recipe_items(db: Session = Depends(get_db)):
    return get_recipe_items(db)


@router.post("", response_model=RecipeItemRead, status_code=status.HTTP_201_CREATED)
def add_recipe_item(payload: RecipeItemCreate, db: Session = Depends(get_db)):
    try:
        return create_recipe_item(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{recipe_item_id}", response_model=RecipeItemRead)
def get_recipe_item_detail(recipe_item_id: int, db: Session = Depends(get_db)):
    recipe_item = get_recipe_item(db, recipe_item_id)
    if not recipe_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecipeItem with id {recipe_item_id} not found",
        )
    return recipe_item


@router.get("/product/{product_id}", response_model=list[RecipeItemRead])
def get_product_recipes(product_id: int, db: Session = Depends(get_db)):
    return get_recipe_items_by_product(db, product_id)


@router.delete("/{recipe_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe_item_endpoint(recipe_item_id: int, db: Session = Depends(get_db)):
    try:
        delete_recipe_item(db, recipe_item_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
