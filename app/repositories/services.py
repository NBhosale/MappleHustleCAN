from uuid import UUID

from sqlalchemy.orm import Session

from app.models.providers import Provider
from app.models.services import Availability, Portfolio, Service


def get_provider(db: Session, user_id: UUID) -> Provider | None:
    return db.query(Provider).filter(Provider.user_id == user_id).first()


def create_service(db: Session, service: Service) -> Service:
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def get_service_by_id(db: Session, service_id: UUID) -> Service | None:
    return db.query(Service).filter(Service.id == service_id).first()


def list_services_by_provider(db: Session, provider_id: UUID):
    return db.query(Service).filter(Service.provider_id == provider_id).all()


def create_availability(
        db: Session,
        availability: Availability) -> Availability:
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return availability


def create_portfolio_entry(db: Session, portfolio: Portfolio) -> Portfolio:
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio
