-- ============================================================
-- Extensions
-- ============================================================
CREATE EXTENSION IF NOT EXISTS postgis;   -- Spatial queries for provider/client locations
CREATE EXTENSION IF NOT EXISTS citext;    -- Case-insensitive text (emails, usernames)
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- Encryption functions (e.g., encrypted chat content)

-- ============================================================
-- ENUM Types
-- ============================================================
CREATE TYPE user_role AS ENUM ('client','provider','admin'); -- Role-based access
CREATE TYPE user_status AS ENUM ('active','suspended','deleted'); -- Lifecycle of a user
CREATE TYPE verification_status AS ENUM ('pending','approved','rejected'); -- Provider vetting
CREATE TYPE service_type AS ENUM ('dog_sitting','dog_walking','house_sitting','lawn_maintenance','house_cleaning','errands');
CREATE TYPE availability_status AS ENUM ('available','booked');
CREATE TYPE booking_status AS ENUM ('pending','accepted','completed','canceled');
CREATE TYPE payment_status AS ENUM ('pending','held','released','refunded');
CREATE TYPE order_status AS ENUM ('pending','paid','processing','shipped','delivered','canceled');
CREATE TYPE notification_type AS ENUM ('booking_request','booking_accepted','booking_completed','message_received','payment_released','review_reminder');
CREATE TYPE notification_status AS ENUM ('unread','read');
CREATE TYPE notification_channel AS ENUM ('in_app','email','sms');
CREATE TYPE contact_method AS ENUM ('email','phone','in_app');
CREATE TYPE review_direction AS ENUM ('client_to_provider','provider_to_client');
CREATE TYPE favorite_type AS ENUM ('provider','item');
CREATE TYPE subscription_plan AS ENUM ('basic','pro','premium');
CREATE TYPE severity_level AS ENUM ('info','warning','error');

-- ============================================================
-- Provinces Reference
-- ============================================================
CREATE TABLE canadian_provinces (
    code CHAR(2) PRIMARY KEY,           -- Province code (ON, BC, etc.)
    name VARCHAR(100) NOT NULL UNIQUE   -- Province name
);

-- ============================================================
-- Users
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email CITEXT NOT NULL UNIQUE,       -- Unique login
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,            -- client | provider | admin
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    is_phone_verified BOOLEAN DEFAULT FALSE,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    province_code CHAR(2) REFERENCES canadian_provinces(code), -- Used for tax/shipping
    location GEOGRAPHY(POINT),          -- Lat/long for search
    profile_image_path VARCHAR(255),
    status user_status NOT NULL DEFAULT 'active',
    is_email_verified BOOLEAN DEFAULT FALSE,
    preferred_contact_method contact_method DEFAULT 'in_app',
    last_login_at TIMESTAMP WITH TIME ZONE,
    password_reset_token UUID,
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    verification_token UUID,
    verification_expires TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Providers & Certifications
-- ============================================================
CREATE TABLE providers (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    verification_status verification_status NOT NULL DEFAULT 'pending',
    id_uploads JSONB NOT NULL DEFAULT '[]',     -- Uploaded ID docs
    background_check_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE provider_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    issuer VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    document_path VARCHAR(255),
    verified BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Shipping Policies
-- ============================================================
CREATE TABLE shipping_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    max_distance_km DECIMAL(6,2),
    ships_to_all_canada BOOLEAN DEFAULT FALSE,
    base_cost DECIMAL(10,2) DEFAULT 0,
    per_km_cost DECIMAL(10,2) DEFAULT 0,
    free_shipping_threshold DECIMAL(10,2),
    is_pickup_available BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shipping_policy_provinces (
    policy_id UUID NOT NULL REFERENCES shipping_policies(id) ON DELETE CASCADE,
    province_code CHAR(2) NOT NULL REFERENCES canadian_provinces(code) ON DELETE CASCADE,
    PRIMARY KEY (policy_id, province_code)
);

-- ============================================================
-- Portfolio & Services
-- ============================================================
CREATE TABLE portfolio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    images JSONB NOT NULL DEFAULT '[]',
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type service_type NOT NULL,
    title VARCHAR(255),
    description TEXT,
    terms TEXT,
    hourly_rate DECIMAL(10,2),
    daily_rate DECIMAL(10,2),
    is_featured BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL
);

-- ============================================================
-- Availability (with recurrence)
-- ============================================================
CREATE TABLE availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    daterange TSRANGE NOT NULL,
    recurrence_rule TEXT CHECK (recurrence_rule IS NULL OR recurrence_rule ~ '^FREQ='), -- iCal format
    status availability_status NOT NULL DEFAULT 'available',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_range CHECK (upper(daterange) > lower(daterange)),
    EXCLUDE USING gist (provider_id WITH =, daterange WITH &&)
);

-- ============================================================
-- Bookings
-- ============================================================
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE SET NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    platform_fee DECIMAL(10,2) DEFAULT 0,
    status booking_status NOT NULL DEFAULT 'pending',
    tip DECIMAL(10,2),
    cancellation_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

CREATE TABLE bookings_2025 PARTITION OF bookings FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE bookings_2026 PARTITION OF bookings FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- ============================================================
-- Reviews (mutual, requires admin approval)
-- ============================================================
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    reviewed_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    direction review_direction NOT NULL, -- client_to_provider | provider_to_client
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    approval_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (approval_status IN ('pending','approved','rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_review_per_booking UNIQUE (booking_id, reviewer_id, direction)
);

-- ============================================================
-- Concerns / Disputes
-- ============================================================
CREATE TABLE concerns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    booking_id UUID REFERENCES bookings(id) ON DELETE SET NULL,
    review_id UUID REFERENCES reviews(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open','in_review','resolved','dismissed')),
    refund_amount DECIMAL(10,2),
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Marketplace Items (handmade products)
-- ============================================================
CREATE TABLE item_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,        -- e.g., Candles, Art, Crafts
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES item_categories(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    inventory_quantity INTEGER NOT NULL DEFAULT 1,
    images JSONB NOT NULL DEFAULT '[]',
    shipping_options JSONB NOT NULL DEFAULT '{}',  -- Per-item overrides
    is_featured BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,           -- Soft delete
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL
);

-- ============================================================
-- Orders (e-commerce)
-- ============================================================
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    platform_fee DECIMAL(10,2) DEFAULT 0,         -- Marketplace commission
    status order_status NOT NULL DEFAULT 'pending',
    tracking_number VARCHAR(255),
    shipped_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,          -- Soft delete
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE order_shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    carrier VARCHAR(100),                         -- e.g., Canada Post
    tracking_number VARCHAR(255),
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================
-- Discounts & Promotions
-- ============================================================
CREATE TABLE discounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID REFERENCES services(id) ON DELETE SET NULL,
    item_id UUID REFERENCES items(id) ON DELETE SET NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_percentage INTEGER NOT NULL CHECK (discount_percentage>0 AND discount_percentage<=100),
    usage_limit INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Payments & Refunds
-- ============================================================
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID REFERENCES bookings(id) ON DELETE SET NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    stripe_transaction_id VARCHAR(255) NOT NULL,   -- Stripe charge ID
    refund_id UUID REFERENCES refunds(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'CAD',
    status payment_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    stripe_refund_id VARCHAR(255) NOT NULL,        -- Stripe refund ID
    amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Messages (real-time chat)
-- ============================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID REFERENCES bookings(id) ON DELETE SET NULL, -- Link to booking if tied
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    receiver_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    encrypted_content BYTEA,                       -- Optional encrypted payload
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

CREATE TABLE messages_2025 PARTITION OF messages FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE messages_2026 PARTITION OF messages FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- File attachments in chat (images, PDFs)
CREATE TABLE message_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_path VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) CHECK (file_type IN ('image/jpeg','image/png','application/pdf')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Favorites / Bookmarks
-- ============================================================
CREATE TABLE favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_id UUID NOT NULL,                       -- Could be provider_id or item_id
    target_type favorite_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, target_id, target_type)
);

-- ============================================================
-- Referrals & Loyalty
-- ============================================================
CREATE TABLE referrals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referred_id UUID REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL UNIQUE,
    redeemed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loyalty_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Subscriptions (monetization for providers)
-- ============================================================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan subscription_plan NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly','yearly')),
    features JSONB NOT NULL DEFAULT '{}',          -- Feature flags (unlimited listings, featured boost)
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','canceled','expired')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ends_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================
-- Provider Metrics (performance stats)
-- ============================================================
CREATE TABLE provider_metrics (
    provider_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    response_rate DECIMAL(5,2) DEFAULT 100,
    avg_response_time INTERVAL,
    repeat_clients INTEGER DEFAULT 0,
    completed_bookings INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Notifications & Preferences
-- ============================================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    content TEXT NOT NULL,
    status notification_status NOT NULL DEFAULT 'unread',
    channel notification_channel DEFAULT 'in_app',
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Per-user notification settings
CREATE TABLE user_notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    notify_on_new_message BOOLEAN DEFAULT TRUE,
    notify_on_booking_update BOOLEAN DEFAULT TRUE,
    notify_on_payment BOOLEAN DEFAULT FALSE,
    notify_on_review_reminder BOOLEAN DEFAULT FALSE,
    notify_by_sms BOOLEAN DEFAULT FALSE,
    notify_by_email BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Log of each attempted notification (useful for Twilio/AWS SNS responses)
CREATE TABLE notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel notification_channel NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending','sent','failed','delivered')),
    provider_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- System Events & Sessions (audit trail + auth)
-- ============================================================
CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    severity severity_level NOT NULL DEFAULT 'info',
    event_data JSONB NOT NULL DEFAULT '{}',       -- Details of event
    context JSONB DEFAULT '{}'::jsonb,            -- IP, user agent, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires TIMESTAMP WITH TIME ZONE NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,            -- IP/device info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Tax Rules (for Canadian sales tax)
-- ============================================================
CREATE TABLE tax_rules (
    province_code CHAR(2) REFERENCES canadian_provinces(code) ON DELETE CASCADE,
    gst DECIMAL(5,2) DEFAULT 0,
    pst DECIMAL(5,2) DEFAULT 0,
    hst DECIMAL(5,2) DEFAULT 0,
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (province_code, effective_date)
);

-- ============================================================
-- Views
-- ============================================================
CREATE OR REPLACE VIEW provider_ratings AS
    SELECT reviewed_id AS provider_id,
           AVG(rating) AS average_rating,
           COUNT(*) AS review_count
    FROM reviews
    WHERE direction='client_to_provider' AND approval_status='approved'
    GROUP BY reviewed_id;

CREATE OR REPLACE VIEW client_bookings_view AS
    SELECT b.client_id,
           COUNT(*) AS total_bookings,
           SUM(b.total_amount + b.platform_fee) AS total_spent
    FROM bookings b GROUP BY b.client_id;

CREATE OR REPLACE VIEW tax_calculation_view AS
    SELECT u.id AS user_id, u.province_code,
           SUM(o.tax_amount) AS total_tax_paid
    FROM users u
    JOIN orders o ON o.client_id=u.id
    GROUP BY u.id, u.province_code;

-- ============================================================
-- Functions & Triggers
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION expire_verification_token()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.verification_expires < NOW() THEN
    NEW.verification_token = NULL;
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION enforce_review_time_limit()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT end_date FROM bookings WHERE id=NEW.booking_id) < NOW() - INTERVAL '14 days' THEN
    RAISE EXCEPTION 'Review period expired';
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION notify_on_new_message()
RETURNS TRIGGER AS $$
DECLARE use_sms BOOLEAN;
BEGIN
  SELECT COALESCE(notify_by_sms,FALSE) INTO use_sms
  FROM user_notification_preferences WHERE user_id=NEW.receiver_id;
  INSERT INTO notifications (user_id,type,content,channel,created_at)
  VALUES (NEW.receiver_id,'message_received','You have a new message',
          CASE WHEN use_sms THEN 'sms' ELSE 'in_app' END,
          CURRENT_TIMESTAMP);
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- Attach triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_services_updated_at BEFORE UPDATE ON services
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER expire_verification BEFORE INSERT OR UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION expire_verification_token();
CREATE TRIGGER enforce_review_time BEFORE INSERT ON reviews
FOR EACH ROW EXECUTE FUNCTION enforce_review_time_limit();
CREATE TRIGGER trigger_notify_on_new_message AFTER INSERT ON messages
FOR EACH ROW EXECUTE FUNCTION notify_on_new_message();

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX idx_availability_provider_id ON availability(provider_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_messages_booking_id ON messages(booking_id);
CREATE INDEX idx_bookings_client_status ON bookings(client_id,status);
CREATE INDEX idx_orders_client_status ON orders(client_id,status);

-- ============================================================
-- Row-Level Security (RLS)
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE concerns ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;

-- Admin bypass policy (allows admins to see everything)
DO $$
DECLARE t RECORD;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='public'
  LOOP
    EXECUTE format(
      'CREATE POLICY admin_bypass ON %I USING (current_setting(''app.current_role'',''t'') = ''admin'')',
      t.tablename
    );
  END LOOP;
END $$;
