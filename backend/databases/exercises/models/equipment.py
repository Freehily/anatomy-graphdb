from sqlalchemy import Column, Integer, String

from . import Base


class EquipmentType(Base):
    """
    Lookup table for exercise equipment.
    """

    __tablename__ = 'equipment'

    equipment_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)  # e.g. "Kettlebell"
