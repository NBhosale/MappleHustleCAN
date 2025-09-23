from sqlalchemy import Column, String
from app.db import Base

class CanadianProvince(Base):
    __tablename__ = "canadian_provinces"

    code = Column(String(2), primary_key=True)  # e.g., "ON", "QC"
    name = Column(String(100), nullable=False)  # e.g., "Ontario", "Quebec"
