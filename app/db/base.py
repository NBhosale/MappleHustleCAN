
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here so Alembic sees them
from app.models.bookings import Booking  # noqa
from app.models.items import Item, ItemCategory, ItemTag  # noqa
from app.models.messages import Message, MessageAttachment  # noqa
from app.models.notifications import (  # noqa
    Notification,
    NotificationLog,
    UserNotificationPreference,
)
from app.models.orders import Order, OrderItem, OrderShipment  # noqa
from app.models.payments import Payment, Refund  # noqa
from app.models.provinces import CanadianProvince  # noqa
from app.models.reviews import Review  # noqa
from app.models.services import Availability, Portfolio, Service  # noqa
from app.models.subscriptions import (  # noqa
    LoyaltyPoint,
    Referral,
    Subscription,
)
from app.models.system import (  # noqa
    ProviderMetric,
    Session,
    SystemEvent,
    TaxRule,
)
# from app.models.tokens import RefreshToken  # noqa - moved to avoid circular import
# from app.models.users import User  # noqa - moved to avoid circular import
