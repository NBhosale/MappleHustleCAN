from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db import SessionLocal
from app.schemas.provinces import (
    ProvinceResponse,
    TaxRuleResponse,
)
from app.services import provinces as province_service
from app.utils.deps import require_admin

router = APIRouter(prefix="/provinces", tags=["Provinces & Taxes"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Provinces ---
@router.get("/", response_model=List[ProvinceResponse])
def list_provinces(db: Session = Depends(get_db)):
    return province_service.list_provinces(db)


@router.get("/{province_code}", response_model=ProvinceResponse)
def get_province(province_code: str, db: Session = Depends(get_db)):
    province = province_service.get_province(db, province_code)
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    return province


# --- Tax Rules ---
@router.get("/{province_code}/taxes", response_model=List[TaxRuleResponse])
def list_tax_rules(province_code: str, db: Session = Depends(get_db)):
    return province_service.list_tax_rules(db, province_code)


@router.post("/{province_code}/taxes", response_model=TaxRuleResponse)
def add_tax_rule(
    province_code: str,
    tax_rule: TaxRuleResponse,  # could also define TaxRuleCreate schema
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    try:
        return province_service.add_tax_rule(db, province_code, tax_rule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
