from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class IngredientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    unit_id: int
    stock_fisico: float = Field(default=0.0, ge=0)
    stock_reservado: float = Field(default=0.0, ge=0)
    stock_minimo: float = Field(default=0.0, ge=0)


class IngredientCreate(IngredientBase):
    pass


class IngredientRead(IngredientBase):
    id: int
    stock_disponible: float

    model_config = ConfigDict(from_attributes=True)
