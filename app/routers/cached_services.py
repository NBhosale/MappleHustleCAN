"""
Cached service endpoints for improved performance
"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.cache import cache_manager
from app.db import get_db
from app.models.services import Service
from app.schemas.errors import create_success_response
from app.schemas.services import ServiceCreate, ServiceResponse, ServiceUpdate
from app.utils.deps import require_provider

router = APIRouter(prefix="/services", tags=["Cached Services"])


@router.get("/cached", response_model=dict)
async def get_services_cached(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    type: Optional[str] = None,
    min_rate: Optional[float] = None,
    max_rate: Optional[float] = None,
    is_featured: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get services with Redis caching"""

    # Create cache key based on query parameters
    cache_key = f"services:list:{skip}:{limit}:{type}:{min_rate}:{max_rate}:{is_featured}"

    # Try to get from cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # Query database
    query = db.query(Service).filter(Service.status == "active")

    if type:
        query = query.filter(Service.type == type)
    if min_rate is not None:
        query = query.filter(Service.hourly_rate >= min_rate)
    if max_rate is not None:
        query = query.filter(Service.hourly_rate <= max_rate)
    if is_featured is not None:
        query = query.filter(Service.is_featured == is_featured)

    total = query.count()
    services = query.offset(skip).limit(limit).all()

    # Convert to response format
    service_responses = [ServiceResponse.from_orm(
        service) for service in services]

    result = {
        "items": [service.dict() for service in service_responses],
        "total": total,
        "page": (skip // limit) + 1,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

    # Cache for 5 minutes
    await cache_manager.set(cache_key, json.dumps(result), ttl=300)

    return result


@router.get("/cached/{service_id}", response_model=dict)
async def get_service_cached(
    service_id: str,
    db: Session = Depends(get_db)
):
    """Get single service with Redis caching"""

    cache_key = f"service:{service_id}"

    # Try to get from cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # Query database
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Convert to response format
    service_response = ServiceResponse.from_orm(service)
    result = service_response.dict()

    # Cache for 10 minutes
    await cache_manager.set(cache_key, json.dumps(result), ttl=600)

    return result


@router.get("/cached/search", response_model=dict)
async def search_services_cached(
    q: str = Query(..., min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search services with Redis caching"""

    cache_key = f"services:search:{q}:{skip}:{limit}"

    # Try to get from cache first
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # Query database with search
    query = db.query(Service).filter(
        Service.status == "active",
        Service.title.ilike(f"%{q}%")
    )

    total = query.count()
    services = query.offset(skip).limit(limit).all()

    # Convert to response format
    service_responses = [ServiceResponse.from_orm(
        service) for service in services]

    result = {
        "results": [service.dict() for service in service_responses],
        "total": total,
        "query": q,
        "page": (skip // limit) + 1,
        "limit": limit
    }

    # Cache for 2 minutes (shorter for search results)
    await cache_manager.set(cache_key, json.dumps(result), ttl=120)

    return result


@router.post("/cached", response_model=dict)
async def create_service_cached(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    """Create service and invalidate related caches"""

    # Create service
    service = Service(
        provider_id=current_user.id,
        **service_data.dict()
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    # Invalidate related caches
    await cache_manager.delete_pattern("services:list:*")
    await cache_manager.delete_pattern("services:search:*")

    # Cache the new service
    service_response = ServiceResponse.from_orm(service)
    cache_key = f"service:{service.id}"
    await cache_manager.set(cache_key, json.dumps(service_response.dict()), ttl=600)

    return create_success_response(
        message="Service created successfully",
        data=service_response.dict()
    )


@router.put("/cached/{service_id}", response_model=dict)
async def update_service_cached(
    service_id: str,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    """Update service and invalidate related caches"""

    # Get service
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.provider_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Update service
    for field, value in service_data.dict(exclude_unset=True).items():
        setattr(service, field, value)

    service.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(service)

    # Invalidate related caches
    await cache_manager.delete_pattern("services:list:*")
    await cache_manager.delete_pattern("services:search:*")
    await cache_manager.delete(f"service:{service_id}")

    # Cache the updated service
    service_response = ServiceResponse.from_orm(service)
    cache_key = f"service:{service.id}"
    await cache_manager.set(cache_key, json.dumps(service_response.dict()), ttl=600)

    return create_success_response(
        message="Service updated successfully",
        data=service_response.dict()
    )


@router.delete("/cached/{service_id}", response_model=dict)
async def delete_service_cached(
    service_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    """Delete service and invalidate related caches"""

    # Get service
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.provider_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Soft delete
    service.status = "inactive"
    service.updated_at = datetime.utcnow()
    db.commit()

    # Invalidate related caches
    await cache_manager.delete_pattern("services:list:*")
    await cache_manager.delete_pattern("services:search:*")
    await cache_manager.delete(f"service:{service_id}")

    return create_success_response(
        message="Service deleted successfully"
    )


@router.post("/cached/invalidate", response_model=dict)
async def invalidate_service_caches(
    current_user=Depends(require_provider)
):
    """Invalidate all service caches (admin function)"""

    # Invalidate all service-related caches
    await cache_manager.delete_pattern("services:*")

    return create_success_response(
        message="Service caches invalidated successfully"
    )
