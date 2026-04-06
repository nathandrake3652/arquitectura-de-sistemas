from pydantic import BaseModel, ConfigDict, Field


class UnitBase(BaseModel):
    name: str = Field(..., min_length=1)
    abbreviation: str = Field(..., min_length=1)
    base_factor: float = Field(gt=0)


class UnitCreate(UnitBase):
    pass


class UnitRead(UnitBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
