from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.services import Service, Portfolio, Availability
from app.schemas.services import (
    ServiceCreate,
    ServiceResponse,
    PortfolioCreate,
    PortfolioResponse,
    AvailabilityCreate,
    AvailabilityResponse,
)
from app.utils.deps import get_current_user, require_provider

router = APIRouter(prefix="/services", tags=["Services"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Service CRUD ---
@router.post("/", response_model=ServiceResponse)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    new_service = Service(
        provider_id=current_user.id,
        type=service.type,
        title=service.title,
        description=service.description,
        terms=service.terms,
        hourly_rate=service.hourly_rate,
        daily_rate=service.daily_rate,
        is_featured=service.is_featured,
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service

@router.get("/", response_model=list[ServiceResponse])
def list_services(db: Session = Depends(get_db)):
    return db.query(Service).all()

# --- Portfolio ---
@router.post("/portfolio", response_model=PortfolioResponse)
def add_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    new_portfolio = Portfolio(
        provider_id=current_user.id,
        title=portfolio.title,
        description=portfolio.description,
        images=portfolio.images,
    )
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    return new_portfolio

@router.get("/portfolio/me", response_model=list[PortfolioResponse])
def my_portfolio(
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    return db.query(Portfolio).filter(Portfolio.provider_id == current_user.id).all()

# --- Availability ---
@router.post("/availability", response_model=AvailabilityResponse)
def set_availability(
    availability: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    new_availability = Availability(
        provider_id=current_user.id,
        date=availability.date,
        start_time=availability.start_time,
        end_time=availability.end_time,
        status=availability.status,
        recurrence_rule=availability.recurrence_rule,
    )
    db.add(new_availability)
    db.commit()
    db.refresh(new_availability)
    return new_availability

@router.get("/availability/me", response_model=list[AvailabilityResponse])
def my_availability(
    db: Session = Depends(get_db),
    current_user=Depends(require_provider)
):
    return db.query(Availability).filter(Availability.provider_id == current_user.id).all()
