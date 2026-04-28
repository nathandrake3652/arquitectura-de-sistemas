from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.product import (
    create_product,
    get_products,
    get_product,
    update_product,
    delete_product,
)
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter(tags=["Gestión de Catalogo de Productos"])


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)):
    return get_products(db)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def add_product(payload: ProductCreate, db: Session = Depends(get_db)):
    try:
        return create_product(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{product_id}", response_model=ProductRead)
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product_endpoint(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
    try:
        return update_product(db, product_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    try:
        delete_product(db, product_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
