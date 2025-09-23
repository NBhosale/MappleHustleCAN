"""
Business rule validation utilities for MapleHustleCAN
"""
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.services import Availability, Service
from app.models.bookings import Booking
from app.models.items import Item
from app.models.users import User
from app.models.provinces import CanadianProvince
from fastapi import HTTPException, status


class ValidationError(HTTPException):
    """Custom validation error for business rules"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


# ============================================================================
# SERVICE AVAILABILITY VALIDATION
# ============================================================================

def validate_service_availability_conflicts(
    db: Session,
    provider_id: str,
    start_date: date,
    start_time: time,
    end_time: time,
    exclude_availability_id: Optional[str] = None
) -> None:
    """
    Validate that the requested time slot doesn't conflict with existing availability.
    
    Args:
        db: Database session
        provider_id: Provider's user ID
        start_date: Requested start date
        start_time: Requested start time
        end_time: Requested end time
        exclude_availability_id: ID to exclude from conflict check (for updates)
    
    Raises:
        ValidationError: If conflicts are found
    """
    # Check for overlapping availability slots
    query = db.query(Availability).filter(
        and_(
            Availability.provider_id == provider_id,
            Availability.date == start_date,
            Availability.status == "available",
            or_(
                # New slot starts during existing slot
                and_(
                    Availability.start_time <= start_time,
                    Availability.end_time > start_time
                ),
                # New slot ends during existing slot
                and_(
                    Availability.start_time < end_time,
                    Availability.end_time >= end_time
                ),
                # New slot completely contains existing slot
                and_(
                    Availability.start_time >= start_time,
                    Availability.end_time <= end_time
                ),
                # Existing slot completely contains new slot
                and_(
                    Availability.start_time <= start_time,
                    Availability.end_time >= end_time
                )
            )
        )
    )
    
    if exclude_availability_id:
        query = query.filter(Availability.id != exclude_availability_id)
    
    conflicting_slots = query.all()
    
    if conflicting_slots:
        conflict_times = [
            f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
            for slot in conflicting_slots
        ]
        raise ValidationError(
            f"Time slot conflicts with existing availability: {', '.join(conflict_times)}"
        )


def validate_availability_time_slot(start_time: time, end_time: time) -> None:
    """
    Validate that the time slot is logical (start < end, reasonable duration).
    
    Args:
        start_time: Start time
        end_time: End time
    
    Raises:
        ValidationError: If time slot is invalid
    """
    if start_time >= end_time:
        raise ValidationError("Start time must be before end time")
    
    # Check for reasonable duration (not more than 24 hours)
    start_datetime = datetime.combine(date.today(), start_time)
    end_datetime = datetime.combine(date.today(), end_time)
    
    # Handle overnight slots
    if end_time <= start_time:
        end_datetime += timedelta(days=1)
    
    duration = end_datetime - start_datetime
    
    if duration > timedelta(hours=24):
        raise ValidationError("Availability slot cannot exceed 24 hours")
    
    if duration < timedelta(minutes=15):
        raise ValidationError("Availability slot must be at least 15 minutes")


# ============================================================================
# BOOKING VALIDATION
# ============================================================================

def validate_booking_time_slot(
    db: Session,
    service_id: str,
    start_date: date,
    start_time: time,
    end_time: time
) -> None:
    """
    Validate that the booking time slot is available and valid.
    
    Args:
        db: Database session
        service_id: Service ID
        start_date: Booking start date
        start_time: Booking start time
        end_time: Booking end time
    
    Raises:
        ValidationError: If booking slot is invalid
    """
    # Get service and provider
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise ValidationError("Service not found")
    
    provider_id = service.provider_id
    
    # Check if provider has availability for this time slot
    availability = db.query(Availability).filter(
        and_(
            Availability.provider_id == provider_id,
            Availability.date == start_date,
            Availability.status == "available",
            Availability.start_time <= start_time,
            Availability.end_time >= end_time
        )
    ).first()
    
    if not availability:
        raise ValidationError("Provider is not available for the requested time slot")
    
    # Check for existing bookings that conflict
    existing_booking = db.query(Booking).filter(
        and_(
            Booking.provider_id == provider_id,
            Booking.service_id == service_id,
            Booking.start_date == start_date,
            Booking.status.in_(["pending", "accepted"]),
            or_(
                # New booking starts during existing booking
                and_(
                    Booking.start_time <= start_time,
                    Booking.end_time > start_time
                ),
                # New booking ends during existing booking
                and_(
                    Booking.start_time < end_time,
                    Booking.end_time >= end_time
                ),
                # New booking completely contains existing booking
                and_(
                    Booking.start_time >= start_time,
                    Booking.end_time <= end_time
                ),
                # Existing booking completely contains new booking
                and_(
                    Booking.start_time <= start_time,
                    Booking.end_time >= end_time
                )
            )
        )
    ).first()
    
    if existing_booking:
        raise ValidationError("Time slot is already booked")


def validate_booking_advance_notice(start_date: date, start_time: time) -> None:
    """
    Validate that booking is made with sufficient advance notice.
    
    Args:
        start_date: Booking start date
        start_time: Booking start time
    
    Raises:
        ValidationError: If advance notice is insufficient
    """
    booking_datetime = datetime.combine(start_date, start_time)
    now = datetime.now()
    
    # Require at least 2 hours advance notice
    if booking_datetime - now < timedelta(hours=2):
        raise ValidationError("Bookings must be made at least 2 hours in advance")
    
    # Don't allow bookings more than 6 months in advance
    if booking_datetime - now > timedelta(days=180):
        raise ValidationError("Bookings cannot be made more than 6 months in advance")


def validate_booking_duration(start_time: time, end_time: time) -> None:
    """
    Validate that booking duration is reasonable.
    
    Args:
        start_time: Booking start time
        end_time: Booking end time
    
    Raises:
        ValidationError: If duration is invalid
    """
    start_datetime = datetime.combine(date.today(), start_time)
    end_datetime = datetime.combine(date.today(), end_time)
    
    if end_time <= start_time:
        end_datetime += timedelta(days=1)
    
    duration = end_datetime - start_datetime
    
    if duration < timedelta(minutes=30):
        raise ValidationError("Booking must be at least 30 minutes")
    
    if duration > timedelta(hours=12):
        raise ValidationError("Booking cannot exceed 12 hours")


# ============================================================================
# GEOGRAPHIC VALIDATION
# ============================================================================

def validate_canadian_province(province_code: str, db: Session) -> None:
    """
    Validate that the province code is a valid Canadian province.
    
    Args:
        province_code: Province code to validate
        db: Database session
    
    Raises:
        ValidationError: If province code is invalid
    """
    if not province_code:
        return
    
    province = db.query(CanadianProvince).filter(
        CanadianProvince.code == province_code.upper()
    ).first()
    
    if not province:
        raise ValidationError(f"Invalid Canadian province code: {province_code}")


def validate_postal_code(postal_code: str) -> None:
    """
    Validate Canadian postal code format.
    
    Args:
        postal_code: Postal code to validate
    
    Raises:
        ValidationError: If postal code format is invalid
    """
    if not postal_code:
        return
    
    # Remove spaces and convert to uppercase
    postal_code = postal_code.replace(" ", "").upper()
    
    # Canadian postal code pattern: A1A 1A1
    import re
    pattern = r"^[A-Z]\d[A-Z]\d[A-Z]\d$"
    
    if not re.match(pattern, postal_code):
        raise ValidationError(
            "Invalid Canadian postal code format. Expected format: A1A 1A1"
        )


def validate_geographic_constraints(
    client_province: str,
    provider_province: str,
    service_type: str
) -> None:
    """
    Validate geographic constraints for service bookings.
    
    Args:
        client_province: Client's province code
        provider_province: Provider's province code
        service_type: Type of service being booked
    
    Raises:
        ValidationError: If geographic constraints are violated
    """
    # Some services may be restricted to same province
    same_province_services = ["house_sitting", "lawn_maintenance", "house_cleaning"]
    
    if service_type in same_province_services and client_province != provider_province:
        raise ValidationError(
            f"Service type '{service_type}' is only available within the same province"
        )


# ============================================================================
# INVENTORY VALIDATION
# ============================================================================

def validate_item_inventory(
    db: Session,
    item_id: str,
    requested_quantity: int
) -> None:
    """
    Validate that sufficient inventory is available for the item.
    
    Args:
        db: Database session
        item_id: Item ID
        requested_quantity: Quantity requested
    
    Raises:
        ValidationError: If inventory is insufficient
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise ValidationError("Item not found")
    
    if item.inventory_quantity < requested_quantity:
        raise ValidationError(
            f"Insufficient inventory. Available: {item.inventory_quantity}, "
            f"Requested: {requested_quantity}"
        )


def validate_item_availability(item_id: str, db: Session) -> None:
    """
    Validate that the item is available for purchase.
    
    Args:
        item_id: Item ID
        db: Database session
    
    Raises:
        ValidationError: If item is not available
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise ValidationError("Item not found")
    
    if item.deleted_at is not None:
        raise ValidationError("Item is no longer available")
    
    if item.inventory_quantity <= 0:
        raise ValidationError("Item is out of stock")


# ============================================================================
# USER VALIDATION
# ============================================================================

def validate_user_verification_status(user_id: str, db: Session) -> None:
    """
    Validate that the user's verification status allows the requested action.
    
    Args:
        user_id: User ID
        db: Database session
    
    Raises:
        ValidationError: If user verification status is invalid
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise ValidationError("User not found")
    
    if user.status != "active":
        raise ValidationError("User account is not active")
    
    if user.role == "provider":
        from app.models.providers import Provider
        provider = db.query(Provider).filter(Provider.user_id == user_id).first()
        
        if provider and provider.verification_status != "approved":
            raise ValidationError(
                "Provider account must be verified before offering services"
            )


# ============================================================================
# COMPREHENSIVE VALIDATION FUNCTIONS
# ============================================================================

def validate_booking_request(
    db: Session,
    client_id: str,
    provider_id: str,
    service_id: str,
    start_date: date,
    start_time: time,
    end_time: time
) -> None:
    """
    Comprehensive validation for booking requests.
    
    Args:
        db: Database session
        client_id: Client user ID
        provider_id: Provider user ID
        service_id: Service ID
        start_date: Booking start date
        start_time: Booking start time
        end_time: Booking end time
    
    Raises:
        ValidationError: If validation fails
    """
    # Validate users
    validate_user_verification_status(client_id, db)
    validate_user_verification_status(provider_id, db)
    
    # Validate time slot
    validate_booking_time_slot(db, service_id, start_date, start_time, end_time)
    validate_booking_advance_notice(start_date, start_time)
    validate_booking_duration(start_time, end_time)
    
    # Validate geographic constraints
    client = db.query(User).filter(User.id == client_id).first()
    provider = db.query(User).filter(User.id == provider_id).first()
    service = db.query(Service).filter(Service.id == service_id).first()
    
    if client and provider and service:
        validate_geographic_constraints(
            client.province_code,
            provider.province_code,
            service.type.value
        )


def validate_order_request(
    db: Session,
    client_id: str,
    items: List[dict]
) -> None:
    """
    Comprehensive validation for order requests.
    
    Args:
        db: Database session
        client_id: Client user ID
        items: List of items with quantities
    
    Raises:
        ValidationError: If validation fails
    """
    # Validate user
    validate_user_verification_status(client_id, db)
    
    # Validate each item
    for item_data in items:
        item_id = item_data.get("item_id")
        quantity = item_data.get("quantity", 1)
        
        if not item_id:
            raise ValidationError("Item ID is required")
        
        validate_item_availability(item_id, db)
        validate_item_inventory(db, item_id, quantity)
