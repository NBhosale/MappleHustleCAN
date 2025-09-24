import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas.services import (
    AvailabilityCreate,
    AvailabilityResponse,
    PortfolioCreate,
    PortfolioResponse,
    ProviderCertificationCreate,
    ProviderCertificationResponse,
    ProviderResponse,
    ServiceCreate,
    ServiceResponse,
)
from app.services import services as service_service
from app.utils.deps import require_provider
from app.utils.validation import (
    ValidationError,
    validate_availability_time_slot,
    validate_service_availability_conflicts,
)

router = APIRouter(prefix="/services", tags=["Services & Providers"])


# --- Dependency: DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Provider Profile ---
@router.get("/provider/me", response_model=ProviderResponse)
def get_my_provider_profile(
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    return service_service.get_provider_profile(db, current_user.id)


# --- Provider Certifications ---
@router.post("/provider/certifications",
             response_model=ProviderCertificationResponse)
def add_certification(
    certification: ProviderCertificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    try:
        return service_service.add_certification(
            db, current_user.id, certification)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/provider/{provider_id}/certifications",
            response_model=List[ProviderCertificationResponse])
def list_certifications(provider_id: uuid.UUID, db: Session = Depends(get_db)):
    return service_service.list_certifications(db, provider_id)


# --- Portfolio ---
@router.post("/provider/portfolio", response_model=PortfolioResponse)
def add_portfolio_item(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    return service_service.add_portfolio_item(db, current_user.id, portfolio)


@router.get("/provider/{provider_id}/portfolio",
            response_model=List[PortfolioResponse])
def list_portfolio(provider_id: uuid.UUID, db: Session = Depends(get_db)):
    return service_service.list_portfolio(db, provider_id)


# --- Services ---
@router.post("/", response_model=ServiceResponse,
             status_code=status.HTTP_201_CREATED)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    return service_service.create_service(db, current_user.id, service)


@router.get("/", response_model=List[ServiceResponse])
def list_services(db: Session = Depends(get_db)):
    return service_service.list_services(db)


@router.get("/provider/{provider_id}", response_model=List[ServiceResponse])
def list_provider_services(
        provider_id: uuid.UUID,
        db: Session = Depends(get_db)):
    return service_service.list_provider_services(db, provider_id)


# --- Availability ---
@router.post("/availability", response_model=AvailabilityResponse)
def add_availability(
    availability: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider),
):
    try:
        # Validate time slot
        validate_availability_time_slot(
            availability.start_time, availability.end_time)

        # Validate availability conflicts
        validate_service_availability_conflicts(
            db,
            str(current_user.id),
            availability.date,
            availability.start_time,
            availability.end_time
        )

        return service_service.add_availability(
            db, current_user.id, availability)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e.detail))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/provider/{provider_id}/availability",
            response_model=List[AvailabilityResponse])
def list_availability(provider_id: uuid.UUID, db: Session = Depends(get_db)):
    return service_service.list_availability(db, provider_id)
