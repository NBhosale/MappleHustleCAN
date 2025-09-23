from app.db.base_class import Base

# Import all models here so Alembic sees them
from app.models.users import User  # noqa
from app.models.services import Service, Portfolio, Availability  # noqa
from app.models.bookings import Booking  # noqa
from app.models.reviews import Review # noqa
from app.models.items import Item, ItemCategory, ItemTag  # noqa
from app.models.orders import Order, OrderItem, OrderShipment  # noqa
from app.models.payments import Payment, Refund  # noqa
from app.models.messages import Message, MessageAttachment  # noqa
from app.models.notifications import Notification, NotificationLog, UserNotificationPreference  # noqa
from app.models.subscriptions import Subscription, Referral, LoyaltyPoint  # noqa
from app.models.system import Session, SystemEvent, TaxRule, ProviderMetric  # noqa
from app.models.tokens import RefreshToken  # noqa
from app.models.provinces import CanadianProvince  # noqa