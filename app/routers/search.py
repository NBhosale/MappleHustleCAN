"""
Search and filtering endpoints
"""
import uuid
from datetime import date, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.bookings import Booking
from app.models.items import Item
from app.models.services import Availability, Service
from app.models.users import User
from app.schemas.bookings import BookingResponse
from app.schemas.items import ItemResponse
from app.schemas.services import ServiceResponse
from app.schemas.users import UserResponse
from app.utils.deps import get_current_user

router = APIRouter(prefix="/search", tags=["Search & Filter"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# SERVICE SEARCH & FILTERING
# ============================================================================

@router.get("/services", response_model=List[ServiceResponse])
def search_services(
    q: Optional[str] = Query(None, description="Search query"),
    service_type: Optional[str] = Query(
        None, description="Filter by service type"),
    min_rate: Optional[float] = Query(None, description="Minimum hourly rate"),
    max_rate: Optional[float] = Query(None, description="Maximum hourly rate"),
    city: Optional[str] = Query(None, description="Filter by city"),
    province: Optional[str] = Query(None, description="Filter by province"),
    is_featured: Optional[bool] = Query(
        None, description="Filter featured services"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search and filter services with pagination
    """
    try:
        query = db.query(Service).filter(Service.deleted_at.is_(None))

        # Text search
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Service.title.ilike(search_term),
                    Service.description.ilike(search_term)
                )
            )

        # Service type filter
        if service_type:
            query = query.filter(Service.type == service_type)

        # Rate filters
        if min_rate is not None:
            query = query.filter(Service.hourly_rate >= min_rate)
        if max_rate is not None:
            query = query.filter(Service.hourly_rate <= max_rate)

        # Location filters
        if city or province:
            query = query.join(User, Service.provider_id == User.id)
            if city:
                query = query.filter(User.city.ilike(f"%{city}%"))
            if province:
                query = query.filter(User.province_code == province.upper())

        # Featured filter
        if is_featured is not None:
            query = query.filter(Service.is_featured == is_featured)

        # Sorting
        sort_field = getattr(Service, sort_by, Service.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))

        # Pagination
        offset = (page - 1) * limit
        services = query.offset(offset).limit(limit).all()

        return services

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/services/available")
def search_available_services(
    date: date = Query(..., description="Search date"),
    start_time: time = Query(..., description="Start time"),
    end_time: time = Query(..., description="End time"),
    service_type: Optional[str] = Query(
        None, description="Filter by service type"),
    city: Optional[str] = Query(None, description="Filter by city"),
    province: Optional[str] = Query(None, description="Filter by province"),
    db: Session = Depends(get_db),
):
    """
    Search for services available at specific time slot
    """
    try:
        # Find providers with availability for the time slot
        availability_query = db.query(Availability).filter(
            and_(
                Availability.date == date,
                Availability.status == "available",
                Availability.start_time <= start_time,
                Availability.end_time >= end_time
            )
        )

        if city or province:
            availability_query = availability_query.join(
                User, Availability.provider_id == User.id)
            if city:
                availability_query = availability_query.filter(
                    User.city.ilike(f"%{city}%"))
            if province:
                availability_query = availability_query.filter(
                    User.province_code == province.upper())

        available_providers = availability_query.all()
        provider_ids = [av.provider_id for av in available_providers]

        if not provider_ids:
            return []

        # Get services from available providers
        services_query = db.query(Service).filter(
            and_(
                Service.provider_id.in_(provider_ids),
                Service.deleted_at.is_(None)
            )
        )

        if service_type:
            services_query = services_query.filter(
                Service.type == service_type)

        services = services_query.all()

        return services

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Availability search failed: {str(e)}")


# ============================================================================
# ITEM SEARCH & FILTERING
# ============================================================================

@router.get("/items", response_model=List[ItemResponse])
def search_items(
    q: Optional[str] = Query(None, description="Search query"),
    category_id: Optional[uuid.UUID] = Query(
        None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    city: Optional[str] = Query(None, description="Filter by city"),
    province: Optional[str] = Query(None, description="Filter by province"),
    is_featured: Optional[bool] = Query(
        None, description="Filter featured items"),
    in_stock: Optional[bool] = Query(
        None, description="Filter items in stock"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search and filter marketplace items with pagination
    """
    try:
        query = db.query(Item).filter(Item.deleted_at.is_(None))

        # Text search
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Item.name.ilike(search_term),
                    Item.description.ilike(search_term)
                )
            )

        # Category filter
        if category_id:
            query = query.filter(Item.category_id == category_id)

        # Price filters
        if min_price is not None:
            query = query.filter(Item.price >= min_price)
        if max_price is not None:
            query = query.filter(Item.price <= max_price)

        # Location filters
        if city or province:
            query = query.join(User, Item.provider_id == User.id)
            if city:
                query = query.filter(User.city.ilike(f"%{city}%"))
            if province:
                query = query.filter(User.province_code == province.upper())

        # Featured filter
        if is_featured is not None:
            query = query.filter(Item.is_featured == is_featured)

        # Stock filter
        if in_stock is not None:
            if in_stock:
                query = query.filter(Item.inventory_quantity > 0)
            else:
                query = query.filter(Item.inventory_quantity == 0)

        # Sorting
        sort_field = getattr(Item, sort_by, Item.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))

        # Pagination
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return items

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Item search failed: {str(e)}")


# ============================================================================
# PROVIDER SEARCH & FILTERING
# ============================================================================

@router.get("/providers", response_model=List[UserResponse])
def search_providers(
    q: Optional[str] = Query(None, description="Search query"),
    city: Optional[str] = Query(None, description="Filter by city"),
    province: Optional[str] = Query(None, description="Filter by province"),
    service_type: Optional[str] = Query(
        None, description="Filter by service type"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search and filter service providers
    """
    try:
        query = db.query(User).filter(
            and_(
                User.role == "provider",
                User.status == "active",
                User.deleted_at.is_(None)
            )
        )

        # Text search
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_term),
                    User.city.ilike(search_term)
                )
            )

        # Location filters
        if city:
            query = query.filter(User.city.ilike(f"%{city}%"))
        if province:
            query = query.filter(User.province_code == province.upper())

        # Service type filter (through services)
        if service_type:
            query = query.join(Service, User.id == Service.provider_id).filter(
                Service.type == service_type
            )

        # Rating filter (would need to join with reviews table)
        # This is a placeholder - actual implementation would join with reviews
        if min_rating is not None:
            # query = query.join(Review, User.id == Review.reviewed_id).filter(
            #     Review.rating >= min_rating
            # )
            pass

        # Sorting
        sort_field = getattr(User, sort_by, User.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))

        # Pagination
        offset = (page - 1) * limit
        providers = query.offset(offset).limit(limit).all()

        return providers

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Provider search failed: {str(e)}")


# ============================================================================
# BOOKING SEARCH & FILTERING
# ============================================================================

@router.get("/bookings", response_model=List[BookingResponse])
def search_bookings(
    status: Optional[str] = Query(
        None, description="Filter by booking status"),
    start_date: Optional[date] = Query(
        None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    min_amount: Optional[float] = Query(
        None, description="Minimum booking amount"),
    max_amount: Optional[float] = Query(
        None, description="Maximum booking amount"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query(
        "desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search and filter bookings for current user
    """
    try:
        # Users can only see their own bookings
        query = db.query(Booking).filter(
            or_(
                Booking.client_id == current_user.id,
                Booking.provider_id == current_user.id
            )
        )

        # Status filter
        if status:
            query = query.filter(Booking.status == status)

        # Date filters
        if start_date:
            query = query.filter(Booking.start_date >= start_date)
        if end_date:
            query = query.filter(Booking.end_date <= end_date)

        # Amount filters
        if min_amount is not None:
            query = query.filter(Booking.total_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Booking.total_amount <= max_amount)

        # Sorting
        sort_field = getattr(Booking, sort_by, Booking.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))

        # Pagination
        offset = (page - 1) * limit
        bookings = query.offset(offset).limit(limit).all()

        return bookings

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Booking search failed: {str(e)}")


# ============================================================================
# ADVANCED SEARCH
# ============================================================================

@router.get("/advanced/services")
def advanced_service_search(
    q: Optional[str] = Query(None, description="Search query"),
    filters: Optional[str] = Query(None, description="JSON filters"),
    db: Session = Depends(get_db),
):
    """
    Advanced service search with complex filters
    """
    try:
        query = db.query(Service).filter(Service.deleted_at.is_(None))

        # Text search with ranking
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Service.title.ilike(search_term),
                    Service.description.ilike(search_term)
                )
            )

        # Parse additional filters from JSON
        if filters:
            import json
            try:
                filter_data = json.loads(filters)

                # Apply various filters based on filter_data
                if "tags" in filter_data:
                    # This would require a tags table
                    pass

                if "availability_days" in filter_data:
                    # Filter by available days
                    pass

            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid filters JSON")

        services = query.all()

        return {
            "results": services,
            "total": len(services),
            "query": q,
            "filters": filters
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Advanced search failed: {str(e)}")


# ============================================================================
# SEARCH SUGGESTIONS
# ============================================================================

@router.get("/suggestions")
def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search query"),
    type: str = Query(
        "all", description="Suggestion type (services, items, providers)"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    db: Session = Depends(get_db),
):
    """
    Get search suggestions based on query
    """
    try:
        search_term = f"%{q}%"
        suggestions = []

        if type in ["all", "services"]:
            service_suggestions = db.query(Service.title).filter(
                and_(
                    Service.title.ilike(search_term),
                    Service.deleted_at.is_(None)
                )
            ).limit(limit).all()

            suggestions.extend([{"text": s.title, "type": "service"}
                               for s in service_suggestions])

        if type in ["all", "items"]:
            item_suggestions = db.query(Item.name).filter(
                and_(
                    Item.name.ilike(search_term),
                    Item.deleted_at.is_(None)
                )
            ).limit(limit).all()

            suggestions.extend([{"text": s.name, "type": "item"}
                               for s in item_suggestions])

        if type in ["all", "providers"]:
            provider_suggestions = db.query(User.name).filter(
                and_(
                    User.name.ilike(search_term),
                    User.role == "provider",
                    User.status == "active"
                )
            ).limit(limit).all()

            suggestions.extend([{"text": s.name, "type": "provider"}
                               for s in provider_suggestions])

        return {
            "query": q,
            "suggestions": suggestions[:limit]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Suggestions failed: {str(e)}")
