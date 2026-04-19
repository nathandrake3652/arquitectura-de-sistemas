from app.db.session import Base, engine
from app.models.user import User
from app.models.unit import Unit
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe_item import RecipeItem
from app.models.stock_movement import StockMovement

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
