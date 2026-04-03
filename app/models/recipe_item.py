from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

#type_checking para evitar la importación circular
if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.ingredient import Ingredient
    from app.models.unit import Unit

class RecipeItem(Base):
    __tablename__ = "recipe_items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id", ondelete="RESTRICT"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="recipe_items")
    ingredient: Mapped["Ingredient"] = relationship()
    unit: Mapped["Unit"] = relationship()