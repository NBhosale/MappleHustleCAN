import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas.items import (
    ItemCategoryCreate,
    ItemCategoryResponse,
    ItemCreate,
    ItemResponse,
    ItemTagCreate,
    ItemTagResponse,
)
from app.services import items as item_service
from app.utils.deps import require_provider

router = APIRouter(prefix="/items", tags=["Items"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Categories ---
@router.post("/categories", response_model=ItemCategoryResponse)
def create_category(
    category: ItemCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    try:
        return item_service.create_category(db, category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories", response_model=List[ItemCategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return item_service.list_categories(db)


# --- Items ---
@router.post("/", response_model=ItemResponse)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    try:
        return item_service.create_item(db, item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    return item_service.list_items(db)


@router.get("/provider/{provider_id}", response_model=List[ItemResponse])
def list_provider_items(provider_id: uuid.UUID, db: Session = Depends(get_db)):
    return item_service.list_provider_items(db, provider_id)


# --- Tags ---
@router.post("/{item_id}/tags", response_model=ItemTagResponse)
def add_item_tag(
    item_id: uuid.UUID,
    tag: ItemTagCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    try:
        return item_service.add_item_tag(db, item_id, tag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{item_id}/tags", response_model=List[ItemTagResponse])
def list_item_tags(item_id: uuid.UUID, db: Session = Depends(get_db)):
    return item_service.list_item_tags(db, item_id)
