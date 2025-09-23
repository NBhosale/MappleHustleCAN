from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.payments import Payment, Refund
from app.schemas.payments import (
    PaymentCreate,
    PaymentResponse,
    RefundCreate,
    RefundResponse,
    PaymentStatus,
)
from app.utils.deps import get_current_user, require_admin

router = APIRouter(prefix="/payments", tags=["Payments"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Create Payment (Booking or Order) ---
@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    new_payment = Payment(
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        booking_id=payment.booking_id,
        order_id=payment.order_id,
        stripe_transaction_id=payment.stripe_transaction_id,
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment


# --- List My Payments ---
@router.get("/me", response_model=list[PaymentResponse])
def list_my_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Payment).filter(
        (Payment.booking_id != None) | (Payment.order_id != None)
    ).all()


# --- Update Payment Status (Admin only) ---
@router.put("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(
    payment_id: str,
    status: PaymentStatus,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = status
    db.commit()
    db.refresh(payment)
    return payment


# --- Create Refund ---
@router.post("/refunds", response_model=RefundResponse)
def create_refund(
    refund: RefundCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    payment = db.query(Payment).filter(Payment.id == refund.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    new_refund = Refund(
        payment_id=refund.payment_id,
        amount=refund.amount,
        reason=refund.reason,
        stripe_refund_id=refund.stripe_refund_id,
    )
    db.add(new_refund)

    # Update payment with refund reference
    payment.refund_id = new_refund.id
    payment.status = PaymentStatus.refunded

    db.commit()
    db.refresh(new_refund)
    return new_refund


# --- List Refunds ---
@router.get("/refunds", response_model=list[RefundResponse])
def list_refunds(
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    return db.query(Refund).all()
