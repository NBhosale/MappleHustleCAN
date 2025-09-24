import uuid
from typing import List, Optional

from pydantic import BaseModel


# --- Item Categories ---
class ItemCategoryBase(BaseModel):
    name: str
    description: Optional[str]


class ItemCategoryCreate(ItemCategoryBase):
    pass


class ItemCategoryResponse(ItemCategoryBase):
    id: uuid.UUID

    class Config:
        orm_mode = True


# --- Items ---
class ItemBase(BaseModel):
    name: str
    description: Optional[str]
    price: float
    inventory_quantity: int = 1
    images: List[str] = []
    shipping_options: dict = {}
    is_featured: bool = False


class ItemCreate(ItemBase):
    provider_id: uuid.UUID
    category_id: Optional[uuid.UUID]


class ItemResponse(ItemBase):
    id: uuid.UUID
    provider_id: uuid.UUID
    category_id: Optional[uuid.UUID]

    class Config:
        orm_mode = True


# --- Tags ---
class ItemTagBase(BaseModel):
    tag: str


class ItemTagCreate(ItemTagBase):
    pass


class ItemTagResponse(ItemTagBase):
    id: uuid.UUID
    item_id: uuid.UUID

    class Config:
        orm_mode = True
