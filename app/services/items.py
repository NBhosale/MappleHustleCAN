from sqlalchemy.orm import Session

from app.models.items import Item, ItemCategory, ItemTag
from app.repositories import items as item_repo


def create_category(db: Session, name, description):
    category = ItemCategory(name=name, description=description)
    return item_repo.create_category(db, category)


def create_item(
        db: Session,
        provider_id,
        category_id,
        name,
        description,
        price,
        inventory_quantity,
        images,
        shipping_options,
        is_featured=False):
    item = Item(
        provider_id=provider_id,
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        inventory_quantity=inventory_quantity,
        images=images,
        shipping_options=shipping_options,
        is_featured=is_featured,
    )
    return item_repo.create_item(db, item)


def add_item_tag(db: Session, item_id, tag):
    tag_obj = ItemTag(item_id=item_id, tag=tag)
    return item_repo.add_item_tag(db, tag_obj)
