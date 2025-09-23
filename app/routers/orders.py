from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.orders import Order, OrderItem, OrderShipment
from app.schemas.orders import (
    OrderCreate,
    OrderResponse,
    OrderItemCreate,
    OrderItemResponse,
    OrderShipmentCreate,
    OrderShipmentResponse,
    OrderStatus,
)
from app.utils.deps import get_current_user, require_client, require_provider

router = APIRouter(prefix="/orders", tags=["Orders"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Place Order (Client) ---
@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    if str(order.client_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only place orders for yourself")

    new_order = Order(
        client_id=order.client_id,
        total_amount=order.total_amount,
        tax_amount=order.tax_amount,
        platform_fee=order.platform_fee,
        status=order.status,
        tracking_number=order.tracking_number,
        shipped_at=order.shipped_at,
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Add order items
    for item in order.items:
        new_item = OrderItem(
            order_id=new_order.id,
            item_id=item.item_id,
            quantity=item.quantity,
            price=item.price,
        )
        db.add(new_item)
    db.commit()
    db.refresh(new_order)

    return new_order


# --- View My Orders (Client) ---
@router.get("/me", response_model=list[OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    return db.query(Order).filter(Order.client_id == current_user.id).all()


# --- Add Shipment (Provider/Admin) ---
@router.post("/{order_id}/shipments", response_model=OrderShipmentResponse)
def add_shipment(
    order_id: str,
    shipment: OrderShipmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_shipment = OrderShipment(
        order_id=order_id,
        carrier=shipment.carrier,
        tracking_number=shipment.tracking_number,
        shipped_at=shipment.shipped_at,
        delivered_at=shipment.delivered_at,
    )
    db.add(new_shipment)

    # Update order status
    order.status = OrderStatus.shipped
    db.commit()
    db.refresh(new_shipment)

    return new_shipment


# --- Update Order Status (Admin/Provider) ---
@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    status: OrderStatus,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    db.commit()
    db.refresh(order)
    return order
