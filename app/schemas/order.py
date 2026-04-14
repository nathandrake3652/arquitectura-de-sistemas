from pydantic import BaseModel, Field


class OrderCheckRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)


class OrderConfirmRequest(BaseModel):
    product_id: int
    order_quantity: int = Field(gt=0)
