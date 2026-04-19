from typing import Literal

from pydantic import BaseModel, Field


class OrderCheckRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)


class OrderConfirmRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)


class OrderFinishRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)
    status: Literal["cocinado", "entregado"]


class InventoryAdjustmentRequest(BaseModel):
    tipo: Literal["entrada_compra", "salida_merma"]
    cantidad: float = Field(gt=0)
    motivo: str = Field(min_length=3, max_length=255)
