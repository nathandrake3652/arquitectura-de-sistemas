from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import OrderCheckRequest, OrderConfirmRequest, OrderFinishRequest
from app.services.order_service import InsufficientStockError, OrderService


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/check", status_code=status.HTTP_200_OK, tags=["Gestion de Pedidos"],
             responses={
                 400: {"description": "Stock Insuficiente (DomainException)"},
                 404: {"description": "Producto no encontrado"}
             },
             summary="Verificar requisitos de un pedido",)
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


@router.post("/orders/check", status_code=status.HTTP_200_OK, tags=["UI Orders"])
def check_order_htmx(
    request: Request,
    product_id: int = Form(...),
    order_quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    try:
        result = service.analyze_order_requirements(
            product_id=product_id,
            order_quantity=order_quantity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(request, 
            "order_check_result.html",
            {
                "result": result,
            },
        )
    return result


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


@router.post("/orders/confirm", status_code=status.HTTP_200_OK, tags=["UI Orders"])
def confirm_order_htmx(
    request: Request,
    product_id: int = Form(...),
    order_quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    try:
        result = service.confirm_order(
            product_id=product_id,
            order_quantity=order_quantity,
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

    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse( request, 
            "order_confirm_result.html",
            {
                "result": result,
            },
        )
    return result


@router.post("/finish", status_code=status.HTTP_200_OK)
def finish_order(payload: OrderFinishRequest, db: Session = Depends(get_db)):
    service = OrderService(db)
    try:
        return service.finish_order(
            product_id=payload.product_id,
            order_quantity=payload.order_quantity,
            status=payload.status,
        )
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Reserva insuficiente para finalizar el pedido",
                "shortages": exc.shortages,
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
