from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import OrderCheckRequest, OrderConfirmRequest
from app.services.order_service import InsufficientStockError, OrderService


router = APIRouter()


@router.post("/check", status_code=status.HTTP_200_OK)
def check_order(payload: OrderCheckRequest, db: Session = Depends(get_db)):
    service = OrderService(db)
    try:
        return service.analyze_order_requirements(
            product_id=payload.product_id,
            order_quantity=payload.order_quantity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/confirm", status_code=status.HTTP_200_OK)
def confirm_order(payload: OrderConfirmRequest, db: Session = Depends(get_db)):
    service = OrderService(db)
    try:
        return service.confirm_order(
            product_id=payload.product_id,
            order_quantity=payload.order_quantity,
        )
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "shortages": exc.shortages,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
