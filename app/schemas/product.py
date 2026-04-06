from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: int = Field(gt=0)


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ProductWithRecipe(ProductRead):
    """Producto con sus recetas asociadas"""
    recipe_items: List[dict] = []

    model_config = ConfigDict(from_attributes=True)
