"""
Provinces service for MapleHustleCAN
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.provinces import CanadianProvince


def list_provinces(db: Session) -> List[CanadianProvince]:
    """List all Canadian provinces"""
    return db.query(CanadianProvince).all()


def get_province(
        db: Session,
        province_code: str) -> Optional[CanadianProvince]:
    """Get a specific province by code"""
    return db.query(CanadianProvince).filter(
        CanadianProvince.code == province_code).first()


def list_tax_rules(db: Session, province_code: str) -> List[dict]:
    """List tax rules for a province (placeholder)"""
    # TODO: Implement tax rules functionality
    return []


def add_tax_rule(db: Session, province_code: str, tax_rule: dict) -> dict:
    """Add a tax rule for a province (placeholder)"""
    # TODO: Implement tax rules functionality
    return {"status": "success", "message": "Tax rule added"}
