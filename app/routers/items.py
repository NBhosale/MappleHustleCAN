from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.items import Item, ItemCategory, ItemTag
from app.schemas.items import (
    ItemCategoryCreate,
    ItemCategoryResponse,
    ItemCreate,
    ItemResponse,
    ItemTagCreate,
    ItemTagResponse,
)
from app.utils.deps import get_current_user, require_provider

router = APIRouter(prefix="/items", tags=["Items"])

# Dependency
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
    current_user=Depends(get_current_user),  # could restrict to admin if you want
):
    new_category = ItemCategory(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@router.get("/categories", response_model=list[ItemCategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(ItemCategory).all()


# --- Items ---
@router.post("/", response_model=ItemResponse)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    if str(item.provider_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only create items for yourself")

    new_item = Item(**item.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get("/", response_model=list[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()


@router.get("/provider/me", response_model=list[ItemResponse])
def list_my_items(
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    return db.query(Item).filter(Item.provider_id == current_user.id).all()


# --- Tags ---
@router.post("/{item_id}/tags", response_model=ItemTagResponse)
def add_tag(
    item_id: str,
    tag: ItemTagCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if str(item.provider_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only tag your own items")

    new_tag = ItemTag(item_id=item_id, tag=tag.tag)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


@router.get("/{item_id}/tags", response_model=list[ItemTagResponse])
def list_tags(item_id: str, db: Session = Depends(get_db)):
    return db.query(ItemTag).filter(ItemTag.item_id == item_id).all()
