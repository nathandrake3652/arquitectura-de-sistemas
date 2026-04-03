from sqlalchemy import Column, Integer, String, Float
from app.db.session import Base

class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    abbreviation = Column(String, unique=True, nullable=False)
    base_factor = Column(Float, nullable=False)