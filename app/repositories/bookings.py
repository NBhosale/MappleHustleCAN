from sqlalchemy.orm import Session
from app.models.bookings import Booking, Review
from uuid import UUID
from typing import List


def create_booking(db: Session, booking: Booking) -> Booking:
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_by_id(db: Session, booking_id: UUID) -> Booking | None:
    return db.query(Booking).filter(Booking.id == booking_id).first()


def get_bookings_for_client(db: Session, client_id: UUID) -> List[Booking]:
    return db.query(Booking).filter(Booking.client_id == client_id).all()


def get_bookings_for_provider(db: Session, provider_id: UUID) -> List[Booking]:
    return db.query(Booking).filter(Booking.provider_id == provider_id).all()


def update_booking_status(db: Session, booking: Booking, status: str) -> Booking:
    booking.status = status
    db.commit()
    db.refresh(booking)
    return booking
