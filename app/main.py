from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.exceptions import DomainException
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.crud.ingredient import get_ingredient, get_ingredients
from app.crud.product import get_products
from app.db.base import init_db
from app.db.session import get_db
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
# Garantiza que la carpeta exista para evitar fallos al montar archivos estaticos.
Path("app/static").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router, prefix="/api/v1")

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    #Aquí se maneja cualquier excepción de DomainException y se formatea la res en JSON
    return JSONResponse(
        status_code=400,
        content={
            "error_type": exc.__class__.__name__,
            "message": exc.message,
            "path": request.url.path
        }
    )


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "environment": settings.app_env}

@app.get("/", tags=["UI"])
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ui/inventory", tags=["UI"])
async def render_inventory(request: Request, db: Session = Depends(get_db)):
    ingredients = get_ingredients(db)
    return templates.TemplateResponse("inventory.html", {"request": request, "ingredients": ingredients})


@app.get("/ui/pos", tags=["UI"])
async def render_pos(request: Request, db: Session = Depends(get_db)):
    products = get_products(db)
    return templates.TemplateResponse("pos.html", {"request": request, "products": products})


@app.get("/ui/kitchen", tags=["UI"])
async def render_kitchen(request: Request, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    orders = order_service.list_kitchen_orders()
    return templates.TemplateResponse("kitchen.html", {"request": request, "orders": orders})


@app.post("/ui/kitchen/{order_id}/ready", tags=["UI"])
async def mark_order_ready(request: Request, order_id: int, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    order_service.mark_order_ready(order_id)
    order = order_service.get_kitchen_order(order_id)
    return templates.TemplateResponse("kitchen_order_row.html", {"request": request, "order": order})


@app.post("/ui/kitchen/{order_id}/deliver", tags=["UI"])
async def mark_order_delivered(request: Request, order_id: int, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    order_service.mark_order_delivered(order_id)
    order = order_service.get_kitchen_order(order_id)
    return templates.TemplateResponse("kitchen_order_row.html", {"request": request, "order": order})

@app.post("/ui/inventory/{ingredient_id}/adjust", tags=["UI"])
async def adjust_inventory(
    request: Request,
    ingredient_id: int,
    amount: float = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    if amount == 0:
        raise DomainException("El ajuste no puede ser 0")

    tipo = "entrada_compra" if amount > 0 else "salida_merma"
    cantidad = abs(amount)

    inventory_service = InventoryService(db)
    inventory_service.adjust_stock(
        ingredient_id=ingredient_id,
        tipo=tipo,
        cantidad=cantidad,
        motivo=reason,
    )

    update_ingredient = get_ingredient(db, ingredient_id)

    return templates.TemplateResponse("inventory_row.html", {"request": request, "ingredient": update_ingredient})


@app.get("/ui/audit", tags=["UI"])
async def render_audit(
    request: Request,
    ingredient_id: str | None = Query(default=None),
    movement_type: str = None,
    db: Session = Depends(get_db)
):
    """Vista de auditoría y trazabilidad de movimientos de stock."""
    inventory_service = InventoryService(db)

    ingredient_filter = None
    if ingredient_id not in (None, ""):
        try:
            ingredient_filter = int(ingredient_id)
        except ValueError:
            raise DomainException("El ingrediente seleccionado no es válido")
    
    # Obtener movimientos con filtros
    movements = inventory_service.get_movements_with_details(
        ingredient_id=ingredient_filter,
        movement_type=movement_type or None
    )
    
    # Obtener resumen estadístico
    summary = inventory_service.get_movements_summary()
    
    # Obtener ingredientes para el filtro
    ingredients = get_ingredients(db)
    
    # Tipos de movimiento disponibles
    movement_types = [
        {"value": "entrada_compra", "label": "Entrada de Compra"},
        {"value": "salida_merma", "label": "Salida por Merma"},
        {"value": "salida_produccion", "label": "Salida por Producción"},
    ]

    context = {
        "request": request,
        "movements": movements,
        "summary": summary,
        "ingredients": ingredients,
        "movement_types": movement_types,
        "selected_ingredient_id": ingredient_filter,
        "selected_movement_type": movement_type or None,
    }

    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse("audit_panel.html", context)

    return templates.TemplateResponse("audit.html", context)