📘 Marketplace Platform Database Schema – Overview

This schema powers a two-sided marketplace for service providers and clients in Canada, with an additional e-commerce marketplace for handmade products. It supports bookings, payments, reviews, disputes, notifications, and subscriptions, while remaining flexible and compliant.

🧑‍🤝‍🧑 Core Entities
Users

Stores all clients, providers, and admins.

Includes email, phone, address, geolocation, verification tokens, and soft delete support.

Province is stored for tax and shipping calculations.

Email and phone verification ensure account trustworthiness.

Providers

Extends users with verification status and ID/background checks.

Providers can upload certifications (e.g., Pet First Aid), which may be verified by admins.

🛠 Services & Availability
Services

Providers can list services (dog walking, house sitting, etc.).

Each service can have terms, hourly/daily rates, tags, and featured promotion options.

Availability

Providers set schedules using time ranges and optional recurrence rules (e.g., “every Monday 9-5”).

The system prevents overlapping availabilities.

📅 Bookings & Reviews
Bookings

Clients book providers’ services.

Includes total amount, platform fee, tips, and cancellation reasons.

Partitioned by year for scalability.

Reviews

Mutual reviews: clients rate providers (public, after admin approval), providers can rate clients (private).

Ratings (1–5 stars) and comments are stored with admin moderation.

Concerns (Disputes)

Clients and providers can raise disputes about bookings or reviews.

Includes description, status, refund amount, and admin resolution.

🛒 Marketplace (E-commerce)
Items

Providers can sell handmade products.

Items have categories, tags, inventory, pricing, and images.

Supports featured listings and soft deletes.

Orders

Clients purchase items; orders contain items, tax, and shipping details.

Supports multi-item orders with shipments and tracking numbers.

Discounts

Promo codes for services or items with limits, expiry dates, and usage tracking.

💳 Payments & Refunds

Payments track Stripe transactions for bookings and orders.

Refunds link back to payments for full or partial reimbursements.

Platform fees are included to track marketplace commission.

💬 Messaging & Notifications
Messages

Real-time chat between clients and providers, tied to bookings.

Supports text, encryption, and file attachments (images, PDFs).

Partitioned by year for scalability.

Notifications

Covers booking requests, messages, reviews, and payments.

Can be delivered via in-app, email, or SMS (Twilio/AWS SNS).

Preferences and logs track user settings and delivery status.

🌟 Engagement Features

Favorites: Clients can bookmark providers or items.

Referrals: Users invite friends and earn rewards.

Loyalty Points: Clients earn points for purchases/bookings.

Subscriptions: Providers can pay for premium plans with perks (featured listings, unlimited services).

📊 Provider Metrics

Tracks response rate, average response time, repeat clients, and completed bookings.

Useful for building trust signals (e.g., “90% response rate within 1 hour”).

🧾 Taxes & Compliance

Tax Rules: Stores Canadian GST/PST/HST per province with effective dates (historical tracking).

Tax View: Summarizes total tax paid per client.

Soft delete fields for auditing across key entities.

🔒 Security & Audit

Row-Level Security (RLS):

Providers can only view their own portfolio, services, and items.

Providers can only see client profiles if a booking exists.

Admins bypass all RLS rules.

Sessions: Tracks login sessions with hashed tokens and metadata (IP, user agent).

System Events: Logs errors, warnings, and info with context.

📈 Scalability Features

Partitioning: Bookings and messages split by year for performance.

Indexes: Composite indexes on high-traffic queries (e.g., bookings by client/status).

Soft Deletes: All major entities (users, services, items, orders) support recoverability.