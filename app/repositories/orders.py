from sqlalchemy.orm import Session
from app.models.orders import Order, OrderItem, OrderShipment
from uuid import UUID


def create_order(db: Session, order: Order) -> Order:
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def create_order_item(db: Session, item: OrderItem) -> OrderItem:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_shipment(db: Session, shipment: OrderShipment) -> OrderShipment:
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


def get_order_by_id(db: Session, order_id: UUID) -> Order | None:
    return db.query(Order).filter(Order.id == order_id).first()
