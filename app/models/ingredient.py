from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.unit import Unit

class Ingredient(Base):
    __tablename__ = "ingredients"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    stock_fisico: Mapped[float] = mapped_column(Float, default=0.0)
    stock_reservado: Mapped[float] = mapped_column(Float, default=0.0)
    stock_minimo: Mapped[float] = mapped_column(Float, default=0.0)

    unit: Mapped["Unit"] = relationship()

    @property
    def stock_disponible(self) -> float:
        return self.stock_fisico - self.stock_reservado