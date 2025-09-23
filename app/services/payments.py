from sqlalchemy.orm import Session
from app.models.payments import Payment, Refund
from app.repositories import payments as payment_repo


def create_payment(db: Session, amount, currency, booking_id=None, order_id=None, stripe_transaction_id=None):
    payment = Payment(
        amount=amount,
        currency=currency,
        booking_id=booking_id,
        order_id=order_id,
        stripe_transaction_id=stripe_transaction_id,
    )
    return payment_repo.create_payment(db, payment)


def issue_refund(db: Session, payment_id, amount, reason, stripe_refund_id=None):
    refund = Refund(
        payment_id=payment_id,
        amount=amount,
        reason=reason,
        stripe_refund_id=stripe_refund_id,
    )
    return payment_repo.create_refund(db, refund)
