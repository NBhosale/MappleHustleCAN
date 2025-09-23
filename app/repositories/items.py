from sqlalchemy.orm import Session
from app.models.items import Item, ItemCategory, ItemTag
from uuid import UUID


def create_category(db: Session, category: ItemCategory) -> ItemCategory:
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_item(db: Session, item: Item) -> Item:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def add_item_tag(db: Session, tag: ItemTag) -> ItemTag:
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
