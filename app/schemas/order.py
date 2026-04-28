from typing import Literal

from pydantic import BaseModel, Field


class OrderCheckRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)

    model_config = ({
        "json_schema_extra": {
            "example": {
                "product_id": 1,
                "order_quantity": 10
            }
        }
    })


class OrderConfirmRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)


class OrderFinishRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)
    status: Literal["preparado", "entregado"]

    model_config = ({
        "json_schema_extra": {
            "example": {
                "product_id": 1,
                "order_quantity": 10,
                "status": "preparado"
            }
        }
    })


class InventoryAdjustmentRequest(BaseModel):
    tipo: Literal["entrada_compra", "salida_merma"]
    cantidad: float = Field(gt=0)
    motivo: str = Field(min_length=3, max_length=255)

    model_config = ({
        "json_schema_extra": {
            "example": {
                "tipo": "entrada_compra",
                "cantidad": 5000.0,
                "motivo": "Compra de harina para reponer stock"
            }
        }
    })
