from pydantic import BaseModel, Field


class RecipeItemBase(BaseModel):
    product_id: int
    ingredient_id: int
    unit_id: int
    quantity: float = Field(gt=0)


class RecipeItemCreate(RecipeItemBase):
    pass


class RecipeItemRead(RecipeItemBase):
    id: int

    class Config:
        from_attributes = True
