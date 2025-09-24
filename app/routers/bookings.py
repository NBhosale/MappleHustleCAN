import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas.bookings import BookingCreate, BookingResponse
from app.services import booking as booking_service
from app.utils.deps import get_current_user, require_client, require_provider
from app.utils.validation import ValidationError, validate_booking_request

router = APIRouter(prefix="/bookings", tags=["Bookings"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Create Booking (Client only) ---
@router.post("/", response_model=BookingResponse)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    try:
        # Comprehensive booking validation
        validate_booking_request(
            db,
            str(current_user.id),
            str(booking.provider_id),
            str(booking.service_id),
            booking.start_date,
            booking.end_date
        )

        return booking_service.create_booking(
            db=db,
            client_id=current_user.id,
            provider_id=booking.provider_id,
            service_id=booking.service_id,
            start_date=booking.start_date,
            end_date=booking.end_date,
            total_amount=booking.total_amount,
            platform_fee=booking.platform_fee,
            tip=booking.tip
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e.detail))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Get Booking by ID ---
@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    booking = booking_service.get_booking(db, booking_id, current_user.id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


# --- List Client Bookings ---
@router.get("/client/me", response_model=List[BookingResponse])
def list_client_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(require_client),
):
    return booking_service.list_client_bookings(db, current_user.id)


# --- List Provider Bookings ---
@router.get("/provider/me", response_model=List[BookingResponse])
def list_provider_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    return booking_service.list_provider_bookings(db, current_user.id)


# --- Update Booking Status (Provider only) ---
@router.post("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: uuid.UUID,
    status: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    try:
        return booking_service.update_booking_status(
            db, booking_id, status, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
