from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.exceptions import DomainException
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.crud.ingredient import get_ingredient, get_ingredients
from app.db.base import init_db
from app.db.session import get_db
from app.services.inventory_service import InventoryService


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
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

@app.post("/ui/inventory/{ingredient_id}/adjust", tags=["UI"])
async def adjust_inventory(
    request: Request,
    ingredient_id: int,
    amount: float = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    inventory_service = InventoryService(db)
    inventory_service.adjust_stock(
        ingredient_id=ingredient_id,
        amount=amount,
        reason=reason
    )

    update_ingredient = get_ingredient(db, ingredient_id)

    return templates.TemplateResponse("inventory_row.html", {"request": request, "ingredient": update_ingredient})