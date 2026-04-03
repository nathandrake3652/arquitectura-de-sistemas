from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

#srive para no tener que importar RecipeItem en la parte superior, lo que causaría una importación circular
if TYPE_CHECKING:
    from app.models.recipe_item import RecipeItem

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, default=0)

    recipe_items: Mapped[List["RecipeItem"]] = relationship(back_populates="product", cascade="all, delete-orphan")