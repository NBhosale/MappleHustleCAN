from sqlalchemy.orm import Session

from app.models.services import Availability, Portfolio, Service
from app.repositories import services as service_repo


def create_service(db: Session, provider_id, service_data):
    """Create a new service for a provider"""
    service = Service(
        provider_id=provider_id,
        type=service_data.type,
        title=service_data.title,
        description=service_data.description,
        hourly_rate=service_data.hourly_rate,
        daily_rate=service_data.daily_rate,
        terms=service_data.terms,
        is_featured=service_data.is_featured,
    )
    return service_repo.create_service(db, service)


def create_availability(
        db: Session,
        provider_id,
        date,
        start_time,
        end_time,
        recurrence_rule=None):
    availability = Availability(
        provider_id=provider_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        recurrence_rule=recurrence_rule,
    )
    return service_repo.create_availability(db, availability)


def add_portfolio_entry(db: Session, provider_id, title, description, images):
    portfolio = Portfolio(
        provider_id=provider_id,
        title=title,
        description=description,
        images=images,
    )
    return service_repo.create_portfolio_entry(db, portfolio)
