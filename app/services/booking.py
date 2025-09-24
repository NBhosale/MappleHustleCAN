from datetime import datetime

from sqlalchemy.orm import Session

from app.models.bookings import Booking
from app.repositories import bookings as booking_repo


def create_booking(
        db: Session,
        client_id,
        provider_id,
        service_id,
        start_date,
        end_date,
        total_amount,
        platform_fee=0.0,
        tip=None):
    if start_date >= end_date:
        raise ValueError("Start date must be before end date")

    booking = Booking(
        client_id=client_id,
        provider_id=provider_id,
        service_id=service_id,
        start_date=start_date,
        end_date=end_date,
        total_amount=total_amount,
        platform_fee=platform_fee,
        tip=tip,
        status="pending",
        created_at=datetime.utcnow(),
    )
    return booking_repo.create_booking(db, booking)


def accept_booking(db: Session, booking: Booking):
    if booking.status != "pending":
        raise ValueError("Booking is not pending")
    return booking_repo.update_booking_status(db, booking, "accepted")


def complete_booking(db: Session, booking: Booking):
    if booking.status != "accepted":
        raise ValueError("Booking must be accepted before completion")
    return booking_repo.update_booking_status(db, booking, "completed")


def cancel_booking(db: Session, booking: Booking, reason: str = None):
    booking.cancellation_reason = reason
    return booking_repo.update_booking_status(db, booking, "canceled")
