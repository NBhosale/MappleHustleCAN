from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db import SessionLocal
from app.schemas.orders import (
    OrderCreate, OrderResponse,
    OrderItemResponse, OrderShipmentCreate, OrderShipmentResponse,
)
from app.services import orders as order_service
from app.utils.deps import require_client, require_provider
from app.utils.validation import (
    validate_order_request,
    ValidationError
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Orders ---
@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    try:
        # Validate order request (inventory, user status, etc.)
        validate_order_request(db, str(current_user.id), order.items)
        
        return order_service.create_order(db, order, current_user.id)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e.detail))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[OrderResponse])
def list_my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    return order_service.list_orders_by_client(db, current_user.id)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# --- Order Items ---
@router.get("/{order_id}/items", response_model=List[OrderItemResponse])
def list_order_items(order_id: uuid.UUID, db: Session = Depends(get_db)):
    return order_service.list_order_items(db, order_id)


# --- Shipments ---
@router.post("/{order_id}/shipments", response_model=OrderShipmentResponse)
def create_shipment(
    order_id: uuid.UUID,
    shipment: OrderShipmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    try:
        return order_service.create_shipment(db, order_id, shipment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{order_id}/shipments", response_model=List[OrderShipmentResponse])
def list_shipments(order_id: uuid.UUID, db: Session = Depends(get_db)):
    return order_service.list_shipments(db, order_id)
