from datetime import datetime

from sqlalchemy.orm import Session

from app.models.orders import Order, OrderItem, OrderShipment
from app.repositories import orders as order_repo


def create_order(
        db: Session,
        client_id,
        total_amount,
        tax_amount,
        platform_fee=None,
        items=None):
    order = Order(
        client_id=client_id,
        total_amount=total_amount,
        tax_amount=tax_amount,
        platform_fee=platform_fee,
        status="pending",
        created_at=datetime.utcnow(),
    )
    saved_order = order_repo.create_order(db, order)

    if items:
        for item in items:
            db_item = OrderItem(
                order_id=saved_order.id,
                item_id=item.item_id,
                quantity=item.quantity,
                price=item.price,
            )
            order_repo.create_order_item(db, db_item)

    return saved_order


def add_shipment(db: Session, order_id, carrier, tracking_number):
    shipment = OrderShipment(
        order_id=order_id,
        carrier=carrier,
        tracking_number=tracking_number,
        shipped_at=datetime.utcnow(),
    )
    return order_repo.create_shipment(db, shipment)
