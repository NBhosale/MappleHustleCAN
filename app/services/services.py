from sqlalchemy.orm import Session
from app.models.services import Service, Availability, Portfolio
from app.repositories import services as service_repo


def create_service(db: Session, provider_id, type, title, description, hourly_rate, daily_rate, terms=None, is_featured=False):
    service = Service(
        provider_id=provider_id,
        type=type,
        title=title,
        description=description,
        hourly_rate=hourly_rate,
        daily_rate=daily_rate,
        terms=terms,
        is_featured=is_featured,
    )
    return service_repo.create_service(db, service)


def create_availability(db: Session, provider_id, date, start_time, end_time, recurrence_rule=None):
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
