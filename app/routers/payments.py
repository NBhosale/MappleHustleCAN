from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.db import SessionLocal
from app.schemas.payments import (
    PaymentCreate, PaymentResponse,
    RefundCreate, RefundResponse,
)
from app.services import payments as payment_service
from app.utils.deps import require_client, require_admin

router = APIRouter(prefix="/payments", tags=["Payments"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Payments ---
@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    try:
        return payment_service.create_payment(db, payment, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    payment = payment_service.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/", response_model=List[PaymentResponse])
def list_my_payments(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    return payment_service.list_payments_by_client(db, current_user.id)


# --- Refunds ---
@router.post("/{payment_id}/refunds", response_model=RefundResponse)
def create_refund(
    payment_id: uuid.UUID,
    refund: RefundCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    try:
        return payment_service.create_refund(db, payment_id, refund)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_id}/refunds", response_model=List[RefundResponse])
def list_refunds(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    return payment_service.list_refunds(db, payment_id)
