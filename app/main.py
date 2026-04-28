from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Form, Query, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.exceptions import DomainException
from fastapi.responses import JSONResponse, HTMLResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.crud.ingredient import get_ingredient, get_ingredients, create_ingredient, delete_ingredient
from app.crud.product import get_products, create_product, delete_product
from app.crud.recipe_item import create_recipe_item
from app.models.unit import Unit
from app.schemas.ingredient import IngredientCreate
from app.schemas.product import ProductCreate
from app.schemas.recipe_item import RecipeItemCreate
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
async def read_root(request: Request, db: Session = Depends(get_db)):
    ingredients = get_ingredients(db)
    products = get_products(db)
    units = db.query(Unit).all()
    return templates.TemplateResponse(request, "index.html", {"ingredients": ingredients, "products": products, "units": units})

@app.post("/ui/ingredient/add", tags=["UI"])
async def ui_add_ingredient(
    request: Request,
    name: str = Form(...),
    unit_id: int = Form(...),
    stock_fisico: float = Form(default=0.0),
    stock_minimo: float = Form(default=0.0),
    price: int = Form(default=0),
    db: Session = Depends(get_db)
):
    try:
        payload = IngredientCreate(name=name, unit_id=unit_id, stock_fisico=stock_fisico, stock_minimo=stock_minimo, price=price)
        create_ingredient(db, payload)
    except ValueError as e:
        pass
    return Response(status_code=200, headers={"HX-Redirect": "/"})

@app.post("/ui/ingredient/{id}/delete", tags=["UI"])
async def ui_delete_ingredient(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    try:
        delete_ingredient(db, id)
    except Exception:
        pass
    return Response(status_code=200, headers={"HX-Redirect": "/"})

@app.post("/ui/product/add", tags=["UI"])
async def ui_add_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(default=""),
    price: int = Form(...),
    ingredient_id: list[int] = Form(default=[]),
    unit_id: list[int] = Form(default=[]),
    quantity: list[float] = Form(default=[]),
    db: Session = Depends(get_db)
):
    try:
        payload = ProductCreate(name=name, description=description, price=price)
        product = create_product(db, payload)
        
        # Save recipe items if they and their sizes align
        for ing_id, u_id, qty in zip(ingredient_id, unit_id, quantity):
            if qty > 0:
                recipe_payload = RecipeItemCreate(
                    product_id=product.id,
                    ingredient_id=ing_id,
                    unit_id=u_id,
                    quantity=qty
                )
                create_recipe_item(db, recipe_payload)
    except ValueError:
        pass
    return Response(status_code=200, headers={"HX-Redirect": "/"})

@app.post("/ui/product/{id}/delete", tags=["UI"])
async def ui_delete_product(
    request: Request,
    id: int,
    db: Session = Depends(get_db)
):
    try:
        delete_product(db, id)
    except Exception:
        pass
    return Response(status_code=200, headers={"HX-Redirect": "/"})

@app.get("/ui/inventory", tags=["UI"])
async def render_inventory(request: Request, db: Session = Depends(get_db)):
    ingredients = get_ingredients(db)
    order_service = OrderService(db)
    pending_orders = order_service.list_pending_orders()
    return templates.TemplateResponse(request,"inventory.html", {"ingredients": ingredients, "pending_orders": pending_orders})


@app.get("/ui/pos", tags=["UI"])
async def render_pos(request: Request, db: Session = Depends(get_db)):
    products = get_products(db)
    return templates.TemplateResponse(request, "pos.html", {"products": products})

@app.post("/ui/pos/check", tags=["UI"])
async def ui_check_order(
    request: Request, 
    product_id: int = Form(...), 
    order_quantity: int = Form(...), 
    db: Session = Depends(get_db)
):
    """Recibe la solicitud en HTML, analiza ingredientes y retorna HTML parcial"""
    order_service = OrderService(db)
    result = order_service.analyze_order_requirements(product_id, order_quantity)
    return templates.TemplateResponse(request, "order_check_result.html", {"result": result})

@app.post("/ui/pos/confirm", tags=["UI"])
async def ui_confirm_order(
    request: Request, 
    product_id: int = Form(...), 
    order_quantity: int = Form(...), 
    db: Session = Depends(get_db)
):
    """Confirma el pedido y muestra el ticket dinámicamente con HTMX"""
    order_service = OrderService(db)
    result = order_service.confirm_order(product_id, order_quantity)
    return templates.TemplateResponse(request, "order_confirm_result.html", {"result": result})

@app.post("/ui/pos/pending", tags=["UI"])
async def ui_pending_order(
    request: Request, 
    product_id: int = Form(...), 
    order_quantity: int = Form(...), 
    db: Session = Depends(get_db)
):
    """Guarda un pedido sin stock como pendiente"""
    order_service = OrderService(db)
    result = order_service.create_pending_order(product_id, order_quantity)
    return templates.TemplateResponse(request, "order_pending_result.html", {"result": result})

@app.get("/ui/inventory/pending/{order_id}/details", tags=["UI"])
async def ui_pending_order_details(
    request: Request, 
    order_id: int, 
    db: Session = Depends(get_db)
):
    from app.models.order_ticket import OrderTicket
    order = db.query(OrderTicket).filter(OrderTicket.id == order_id).first()
    if not order:
        raise DomainException("Pedido pendiente no encontrado")
        
    order_service = OrderService(db)
    analysis = order_service.analyze_order_requirements(order.product_id, order.order_quantity)
    return templates.TemplateResponse(request,"inventory_pending_modal.html", {"order": order, "analysis": analysis})

@app.post("/ui/inventory/pending/{order_id}/approve", tags=["UI"])
async def ui_approve_pending_order(
    request: Request, 
    order_id: int, 
    db: Session = Depends(get_db)
):
    from app.models.order_ticket import OrderTicket
    order_service = OrderService(db)
    inventory_service = InventoryService(db)
    
    order = db.query(OrderTicket).filter(OrderTicket.id == order_id).first()
    if not order:
        raise DomainException("Pedido pendiente no encontrado")
        
    # Calculamos cuanto falta HOY y forzamos la entrada
    analysis = order_service.analyze_order_requirements(order.product_id, order.order_quantity)
    for req in analysis["ingredients_requirements"]:
        if not req["is_available"]:
            missing = req["missing_in_inventory_unit"]
            inventory_service.adjust_stock(
                ingredient_id=req["ingredient_id"],
                tipo="entrada_compra",
                cantidad=missing,
                motivo=f"Auto-compra para Pedido #{order_id}"
            )
            
    # Ahora que lo forzamos a existir, confirmamos
    order_service.approve_pending_order(order_id)
    
    response = HTMLResponse("<script>window.location.reload();</script>")
    response.headers["HX-Refresh"] = "true"
    return response

@app.get("/ui/kitchen", tags=["UI"])
async def render_kitchen(request: Request, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    orders = order_service.list_kitchen_orders()
    return templates.TemplateResponse(request, "kitchen.html", {"orders": orders})


@app.post("/ui/kitchen/{order_id}/ready", tags=["UI"])
async def mark_order_ready(request: Request, order_id: int, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    order_service.mark_order_ready(order_id)
    order = order_service.get_kitchen_order(order_id)
    return templates.TemplateResponse(request, "kitchen_order_row.html", {"order": order})


@app.post("/ui/kitchen/{order_id}/deliver", tags=["UI"])
async def mark_order_delivered(request: Request, order_id: int, db: Session = Depends(get_db)):
    order_service = OrderService(db)
    order_service.mark_order_delivered(order_id)
    order = order_service.get_kitchen_order(order_id)
    return templates.TemplateResponse(request, "kitchen_order_row.html", {"order": order})

@app.get("/ui/kitchen/history", tags=["UI"])
async def render_kitchen_history(
    request: Request, 
    page: int = Query(default=1), 
    db: Session = Depends(get_db)
):
    """Endpoint llamado por HTMX para paginar el historial de pedidos entregados."""
    order_service = OrderService(db)
    history_data = order_service.get_kitchen_history(page=page)
    
    return templates.TemplateResponse(
        request,
        "kitchen_history.html", 
        {"history": history_data}
    )

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

    return templates.TemplateResponse(request, "inventory_row.html", {"ingredient": update_ingredient})


@app.get("/ui/audit", tags=["UI"])
async def render_audit(
    request: Request,
    ingredient_id: str | None = Query(default=None),
    movement_type: str | None = Query(default=None),
    fecha: str | None = Query(default=None),
    page: int = Query(default=1),
    per_page: int = Query(default=5),
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
    history_data = inventory_service.get_movements_with_details(
        ingredient_id=ingredient_filter,
        movement_type=movement_type or None,
        fecha=fecha or None,
        page=page
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
        "history": history_data,
        "summary": summary,
        "ingredients": ingredients,
        "movement_types": movement_types,
        "selected_ingredient_id": ingredient_filter,
        "selected_movement_type": movement_type or None,
        "selected_fecha": fecha or "",
    }

    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(request,"audit_panel.html", context)

    return templates.TemplateResponse(request, "audit.html", context)

def format_datetime_local(dt: datetime, fmt="%Y-%m-%d %H:%M:%S", tz_name="America/Santiago"):
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone(ZoneInfo(tz_name))
    return local_dt.strftime(fmt)
templates.env.filters["local_time"] = format_datetime_local