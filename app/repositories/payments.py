from sqlalchemy.orm import Session
from app.models.payments import Payment, Refund
from uuid import UUID


def create_payment(db: Session, payment: Payment) -> Payment:
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def create_refund(db: Session, refund: Refund) -> Refund:
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


def get_payment_by_id(db: Session, payment_id: UUID) -> Payment | None:
    return db.query(Payment).filter(Payment.id == payment_id).first()
