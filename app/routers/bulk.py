"""
Bulk operations endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
from datetime import datetime

from app.db import SessionLocal
from app.models.services import Service, Availability
from app.models.items import Item
from app.models.bookings import Booking
from app.models.users import User
from app.schemas.services import ServiceCreate, ServiceResponse
from app.schemas.items import ItemCreate, ItemResponse
from app.schemas.bookings import BookingCreate, BookingResponse
from app.utils.deps import get_current_user, require_provider, require_client
from app.utils.validation import ValidationError

router = APIRouter(prefix="/bulk", tags=["Bulk Operations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# BULK SERVICE OPERATIONS
# ============================================================================

@router.post("/services", response_model=List[ServiceResponse])
def bulk_create_services(
    services: List[ServiceCreate],
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Create multiple services at once
    """
    try:
        if len(services) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 services allowed in bulk creation")
        
        created_services = []
        failed_services = []
        
        for i, service_data in enumerate(services):
            try:
                # Create service
                service = Service(
                    provider_id=current_user.id,
                    type=service_data.type,
                    title=service_data.title,
                    description=service_data.description,
                    terms=service_data.terms,
                    hourly_rate=service_data.hourly_rate,
                    daily_rate=service_data.daily_rate,
                    is_featured=service_data.is_featured,
                )
                
                db.add(service)
                db.flush()  # Get the ID
                
                created_services.append(service)
                
            except Exception as e:
                failed_services.append({
                    "index": i,
                    "error": str(e),
                    "data": service_data.dict()
                })
        
        if created_services:
            db.commit()
        
        return {
            "message": f"Bulk service creation completed. {len(created_services)} successful, {len(failed_services)} failed",
            "created_services": created_services,
            "failed_services": failed_services
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk service creation failed: {str(e)}")


@router.put("/services", response_model=List[ServiceResponse])
def bulk_update_services(
    updates: List[Dict[str, Any]],  # [{"id": "uuid", "data": {...}}, ...]
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Update multiple services at once
    """
    try:
        if len(updates) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 services allowed in bulk update")
        
        updated_services = []
        failed_updates = []
        
        for update_data in updates:
            try:
                service_id = update_data.get("id")
                service_data = update_data.get("data", {})
                
                if not service_id:
                    raise ValueError("Service ID is required")
                
                # Get service and verify ownership
                service = db.query(Service).filter(
                    and_(
                        Service.id == service_id,
                        Service.provider_id == current_user.id,
                        Service.deleted_at.is_(None)
                    )
                ).first()
                
                if not service:
                    raise ValueError("Service not found or not owned by user")
                
                # Update service fields
                for field, value in service_data.items():
                    if hasattr(service, field):
                        setattr(service, field, value)
                
                service.updated_at = datetime.utcnow()
                updated_services.append(service)
                
            except Exception as e:
                failed_updates.append({
                    "service_id": update_data.get("id"),
                    "error": str(e)
                })
        
        if updated_services:
            db.commit()
        
        return {
            "message": f"Bulk service update completed. {len(updated_services)} successful, {len(failed_updates)} failed",
            "updated_services": updated_services,
            "failed_updates": failed_updates
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk service update failed: {str(e)}")


@router.delete("/services")
def bulk_delete_services(
    service_ids: List[str],
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Soft delete multiple services at once
    """
    try:
        if len(service_ids) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 services allowed in bulk delete")
        
        deleted_count = 0
        failed_deletes = []
        
        for service_id in service_ids:
            try:
                service = db.query(Service).filter(
                    and_(
                        Service.id == service_id,
                        Service.provider_id == current_user.id,
                        Service.deleted_at.is_(None)
                    )
                ).first()
                
                if not service:
                    raise ValueError("Service not found or not owned by user")
                
                service.deleted_at = datetime.utcnow()
                deleted_count += 1
                
            except Exception as e:
                failed_deletes.append({
                    "service_id": service_id,
                    "error": str(e)
                })
        
        if deleted_count > 0:
            db.commit()
        
        return {
            "message": f"Bulk service deletion completed. {deleted_count} successful, {len(failed_deletes)} failed",
            "deleted_count": deleted_count,
            "failed_deletes": failed_deletes
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk service deletion failed: {str(e)}")


# ============================================================================
# BULK ITEM OPERATIONS
# ============================================================================

@router.post("/items", response_model=List[ItemResponse])
def bulk_create_items(
    items: List[ItemCreate],
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Create multiple items at once
    """
    try:
        if len(items) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 items allowed in bulk creation")
        
        created_items = []
        failed_items = []
        
        for i, item_data in enumerate(items):
            try:
                # Create item
                item = Item(
                    provider_id=current_user.id,
                    category_id=item_data.category_id,
                    name=item_data.name,
                    description=item_data.description,
                    price=item_data.price,
                    inventory_quantity=item_data.inventory_quantity,
                    images=item_data.images,
                    shipping_options=item_data.shipping_options,
                    is_featured=item_data.is_featured,
                )
                
                db.add(item)
                db.flush()  # Get the ID
                
                created_items.append(item)
                
            except Exception as e:
                failed_items.append({
                    "index": i,
                    "error": str(e),
                    "data": item_data.dict()
                })
        
        if created_items:
            db.commit()
        
        return {
            "message": f"Bulk item creation completed. {len(created_items)} successful, {len(failed_items)} failed",
            "created_items": created_items,
            "failed_items": failed_items
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk item creation failed: {str(e)}")


@router.put("/items/inventory")
def bulk_update_inventory(
    updates: List[Dict[str, Any]],  # [{"item_id": "uuid", "quantity": 10}, ...]
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Update inventory quantities for multiple items
    """
    try:
        if len(updates) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 items allowed in bulk inventory update")
        
        updated_count = 0
        failed_updates = []
        
        for update_data in updates:
            try:
                item_id = update_data.get("item_id")
                quantity = update_data.get("quantity")
                
                if not item_id or quantity is None:
                    raise ValueError("Item ID and quantity are required")
                
                if quantity < 0:
                    raise ValueError("Quantity cannot be negative")
                
                # Get item and verify ownership
                item = db.query(Item).filter(
                    and_(
                        Item.id == item_id,
                        Item.provider_id == current_user.id,
                        Item.deleted_at.is_(None)
                    )
                ).first()
                
                if not item:
                    raise ValueError("Item not found or not owned by user")
                
                item.inventory_quantity = quantity
                item.updated_at = datetime.utcnow()
                updated_count += 1
                
            except Exception as e:
                failed_updates.append({
                    "item_id": update_data.get("item_id"),
                    "error": str(e)
                })
        
        if updated_count > 0:
            db.commit()
        
        return {
            "message": f"Bulk inventory update completed. {updated_count} successful, {len(failed_updates)} failed",
            "updated_count": updated_count,
            "failed_updates": failed_updates
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk inventory update failed: {str(e)}")


# ============================================================================
# BULK AVAILABILITY OPERATIONS
# ============================================================================

@router.post("/availability")
def bulk_create_availability(
    availability_data: List[Dict[str, Any]],  # [{"date": "2025-01-01", "start_time": "09:00", "end_time": "17:00"}, ...]
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Create multiple availability slots at once
    """
    try:
        if len(availability_data) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 availability slots allowed in bulk creation")
        
        created_slots = []
        failed_slots = []
        
        for i, slot_data in enumerate(availability_data):
            try:
                # Validate required fields
                required_fields = ["date", "start_time", "end_time"]
                for field in required_fields:
                    if field not in slot_data:
                        raise ValueError(f"Field '{field}' is required")
                
                # Create availability slot
                availability = Availability(
                    provider_id=current_user.id,
                    date=slot_data["date"],
                    start_time=slot_data["start_time"],
                    end_time=slot_data["end_time"],
                    status=slot_data.get("status", "available"),
                    recurrence_rule=slot_data.get("recurrence_rule")
                )
                
                db.add(availability)
                db.flush()  # Get the ID
                
                created_slots.append(availability)
                
            except Exception as e:
                failed_slots.append({
                    "index": i,
                    "error": str(e),
                    "data": slot_data
                })
        
        if created_slots:
            db.commit()
        
        return {
            "message": f"Bulk availability creation completed. {len(created_slots)} successful, {len(failed_slots)} failed",
            "created_slots": created_slots,
            "failed_slots": failed_slots
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk availability creation failed: {str(e)}")


# ============================================================================
# BULK BOOKING OPERATIONS
# ============================================================================

@router.post("/bookings", response_model=List[BookingResponse])
def bulk_create_bookings(
    bookings: List[BookingCreate],
    current_user=Depends(require_client),
    db: Session = Depends(get_db),
):
    """
    Create multiple bookings at once (for recurring bookings)
    """
    try:
        if len(bookings) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 bookings allowed in bulk creation")
        
        created_bookings = []
        failed_bookings = []
        
        for i, booking_data in enumerate(bookings):
            try:
                # Create booking
                booking = Booking(
                    client_id=current_user.id,
                    provider_id=booking_data.provider_id,
                    service_id=booking_data.service_id,
                    start_date=booking_data.start_date,
                    end_date=booking_data.end_date,
                    total_amount=booking_data.total_amount,
                    platform_fee=booking_data.platform_fee,
                    tip=booking_data.tip,
                    status=booking_data.status,
                )
                
                db.add(booking)
                db.flush()  # Get the ID
                
                created_bookings.append(booking)
                
            except Exception as e:
                failed_bookings.append({
                    "index": i,
                    "error": str(e),
                    "data": booking_data.dict()
                })
        
        if created_bookings:
            db.commit()
        
        return {
            "message": f"Bulk booking creation completed. {len(created_bookings)} successful, {len(failed_bookings)} failed",
            "created_bookings": created_bookings,
            "failed_bookings": failed_bookings
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk booking creation failed: {str(e)}")


# ============================================================================
# BULK STATUS UPDATES
# ============================================================================

@router.put("/bookings/status")
def bulk_update_booking_status(
    updates: List[Dict[str, Any]],  # [{"booking_id": "uuid", "status": "accepted"}, ...]
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Update status of multiple bookings at once
    """
    try:
        if len(updates) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 bookings allowed in bulk status update")
        
        updated_count = 0
        failed_updates = []
        
        for update_data in updates:
            try:
                booking_id = update_data.get("booking_id")
                status = update_data.get("status")
                
                if not booking_id or not status:
                    raise ValueError("Booking ID and status are required")
                
                # Get booking and verify ownership
                booking = db.query(Booking).filter(
                    and_(
                        Booking.id == booking_id,
                        Booking.provider_id == current_user.id
                    )
                ).first()
                
                if not booking:
                    raise ValueError("Booking not found or not owned by user")
                
                booking.status = status
                booking.updated_at = datetime.utcnow()
                updated_count += 1
                
            except Exception as e:
                failed_updates.append({
                    "booking_id": update_data.get("booking_id"),
                    "error": str(e)
                })
        
        if updated_count > 0:
            db.commit()
        
        return {
            "message": f"Bulk booking status update completed. {updated_count} successful, {len(failed_updates)} failed",
            "updated_count": updated_count,
            "failed_updates": failed_updates
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk booking status update failed: {str(e)}")


# ============================================================================
# BULK EXPORT OPERATIONS
# ============================================================================

@router.get("/export/services")
def export_services(
    format: str = "json",  # json, csv, xlsx
    current_user=Depends(require_provider),
    db: Session = Depends(get_db),
):
    """
    Export user's services in various formats
    """
    try:
        services = db.query(Service).filter(
            and_(
                Service.provider_id == current_user.id,
                Service.deleted_at.is_(None)
            )
        ).all()
        
        if format == "json":
            return {
                "services": [service.__dict__ for service in services],
                "exported_at": datetime.utcnow().isoformat(),
                "total_count": len(services)
            }
        elif format == "csv":
            # This would generate CSV content
            return {"message": "CSV export not implemented yet"}
        elif format == "xlsx":
            # This would generate Excel content
            return {"message": "Excel export not implemented yet"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/bookings")
def export_bookings(
    format: str = "json",
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export user's bookings in various formats
    """
    try:
        bookings = db.query(Booking).filter(
            or_(
                Booking.client_id == current_user.id,
                Booking.provider_id == current_user.id
            )
        ).all()
        
        if format == "json":
            return {
                "bookings": [booking.__dict__ for booking in bookings],
                "exported_at": datetime.utcnow().isoformat(),
                "total_count": len(bookings)
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
