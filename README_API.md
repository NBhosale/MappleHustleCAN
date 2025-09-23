# Maple Hussle API – Endpoint Reference

This document provides a quick reference of available API endpoints, grouped by feature.

---

## 🔑 Authentication (users.py)

- `POST /users/register` → Register a new user
- `POST /users/login` → Login, returns access & refresh tokens
- `POST /users/refresh` → Refresh access token
- `POST /users/logout` → Logout (revoke refresh token)
- `POST /users/change-password` → Change password (revoke all sessions)
- `POST /users/forgot-password` → Request reset link
- `POST /users/reset-password` → Reset password with token
- `GET /users/me` → Get current user profile
- `GET /users/admin/dashboard` → Admin-only dashboard
- `GET /users/provider/dashboard` → Provider-only dashboard
- `GET /users/client/dashboard` → Client-only dashboard
- `POST /users/admin/revoke-tokens/{user_id}` → Admin revokes all user tokens

---

## 🛠️ Services (services.py)

- `POST /services/` → Provider creates a service
- `GET /services/` → List all services
- `POST /services/portfolio` → Add portfolio entry
- `GET /services/portfolio/me` → List my portfolio
- `POST /services/availability` → Set provider availability
- `GET /services/availability/me` → List my availability

---

## 📅 Bookings (bookings.py)

- `POST /bookings/` → Client creates booking
- `GET /bookings/me` → List client bookings
- `GET /bookings/provider/me` → List provider bookings
- `PUT /bookings/{booking_id}/status` → Provider updates booking status

---

## 🛍️ Items (items.py)

- `POST /items/categories` → Create category
- `GET /items/categories` → List categories
- `POST /items/` → Provider creates item
- `GET /items/` → List all items
- `GET /items/provider/me` → List provider items
- `POST /items/{item_id}/tags` → Add tag to item
- `GET /items/{item_id}/tags` → List item tags

---

## 📦 Orders (orders.py)

- `POST /orders/` → Client places order
- `GET /orders/me` → List client orders
- `POST /orders/{order_id}/shipments` → Provider adds shipment
- `PUT /orders/{order_id}/status` → Provider updates status

---

## 💳 Payments (payments.py)

- `POST /payments/` → Create payment (booking/order)
- `GET /payments/me` → List user’s payments
- `PUT /payments/{payment_id}/status` → Admin updates status
- `POST /payments/refunds` → Admin creates refund
- `GET /payments/refunds` → Admin lists refunds

---

## 💬 Messages (messages.py)

- `POST /messages/` → Send a message (with attachments)
- `GET /messages/conversation/{user_id}` → Get conversation
- `PUT /messages/{message_id}/read` → Mark message as read

---

## 🔔 Notifications (notifications.py)

- `POST /notifications/` → Create notification (system/admin use)
- `GET /notifications/me` → List my notifications
- `PUT /notifications/{id}/read` → Mark as read
- `PUT /notifications/preferences` → Update preferences
- `GET /notifications/logs` → View logs (admin)

---

## 📝 Notes
- All endpoints (except `/register` and `/login`) require **JWT access token**.
- Refresh tokens are long-lived and stored in DB for revocation.
