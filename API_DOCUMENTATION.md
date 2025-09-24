# 🍁 MapleHustle API Documentation

## Overview

MapleHustle is a Canadian services & marketplace platform that connects clients with service providers for various services like house sitting, dog walking, and more. The platform also supports buying and selling handmade products.

## 🚀 Quick Start

### Base URL
```
http://localhost:8000
```

### Authentication
Most endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

### Content Type
Most endpoints expect `application/json` content type, except for file uploads which use `multipart/form-data`.

---

## 🔑 Authentication Endpoints

### Register User
**POST** `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePassword123!",
  "role": "client"  // "client", "provider", or "admin"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "client",
  "status": "active",
  "is_email_verified": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Login
**POST** `/auth/login`

Authenticate user and get access tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Refresh Token
**POST** `/auth/refresh`

Refresh access token using refresh token.

**Query Parameters:**
- `refresh_token`: The refresh token string

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Logout
**POST** `/auth/logout`

Revoke refresh token and logout user.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

## 👤 User Management

### Get Current User Profile
**GET** `/users/me`

Get current user's profile information.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "client",
  "status": "active",
  "is_email_verified": true,
  "city": "Toronto",
  "postal_code": "M5V 3A8",
  "profile_image_path": "/uploads/profiles/user123.jpg",
  "preferred_contact_method": "email",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Change Password
**POST** `/users/change-password`

Change user password and revoke all sessions.

**Headers:**
- `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword123!"
}
```

**Response:** `200 OK`
```json
{
  "detail": "Password updated and all sessions revoked. Please log in again."
}
```

### Forgot Password
**POST** `/users/forgot-password`

Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset email sent"
}
```

### Reset Password
**POST** `/users/reset-password`

Reset password using reset token.

**Request Body:**
```json
{
  "token": "reset_token_here",
  "new_password": "NewPassword123!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

### User Dashboards

#### Admin Dashboard
**GET** `/users/admin/dashboard`

**Headers:**
- `Authorization: Bearer <admin_access_token>`

**Response:** `200 OK`
```json
{
  "message": "Welcome Admin John Doe 🚀"
}
```

#### Provider Dashboard
**GET** `/users/provider/dashboard`

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Response:** `200 OK`
```json
{
  "message": "Welcome Provider John Doe, here are your bookings"
}
```

#### Client Dashboard
**GET** `/users/client/dashboard`

**Headers:**
- `Authorization: Bearer <client_access_token>`

**Response:** `200 OK`
```json
{
  "message": "Welcome Client John Doe, here are your bookings"
}
```

---

## 🛠️ Services Management

### Create Service
**POST** `/services/`

Create a new service (Provider only).

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Request Body:**
```json
{
  "type": "dog_walking",
  "title": "Professional Dog Walking",
  "description": "Expert dog walking services in Toronto",
  "hourly_rate": 25.0,
  "daily_rate": 200.0,
  "terms": "Standard service terms and conditions",
  "is_featured": true
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "provider_id": "uuid",
  "type": "dog_walking",
  "title": "Professional Dog Walking",
  "description": "Expert dog walking services in Toronto",
  "hourly_rate": 25.0,
  "daily_rate": 200.0,
  "terms": "Standard service terms and conditions",
  "is_featured": true,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### List Services
**GET** `/services/`

Get list of all services with optional filtering.

**Query Parameters:**
- `type`: Filter by service type
- `provider_id`: Filter by provider
- `featured`: Filter featured services (true/false)
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "services": [
    {
      "id": "uuid",
      "provider_id": "uuid",
      "type": "dog_walking",
      "title": "Professional Dog Walking",
      "description": "Expert dog walking services",
      "hourly_rate": 25.0,
      "daily_rate": 200.0,
      "is_featured": true,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### Get Service by ID
**GET** `/services/{service_id}`

Get specific service details.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "provider_id": "uuid",
  "type": "dog_walking",
  "title": "Professional Dog Walking",
  "description": "Expert dog walking services",
  "hourly_rate": 25.0,
  "daily_rate": 200.0,
  "terms": "Standard service terms",
  "is_featured": true,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Update Service
**PUT** `/services/{service_id}`

Update service details (Provider only).

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Request Body:**
```json
{
  "title": "Updated Service Title",
  "description": "Updated description",
  "hourly_rate": 30.0,
  "daily_rate": 240.0
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "title": "Updated Service Title",
  "description": "Updated description",
  "hourly_rate": 30.0,
  "daily_rate": 240.0,
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Delete Service
**DELETE** `/services/{service_id}`

Delete service (Provider only).

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Response:** `200 OK`
```json
{
  "message": "Service deleted successfully"
}
```

### Service Availability

#### Set Availability
**POST** `/services/{service_id}/availability`

Set provider availability for a service.

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Request Body:**
```json
{
  "date": "2024-01-15",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "status": "available"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "service_id": "uuid",
  "date": "2024-01-15",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "status": "available",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get Service Availability
**GET** `/services/{service_id}/availability`

Get availability for a specific service.

**Response:** `200 OK`
```json
{
  "availability": [
    {
      "id": "uuid",
      "date": "2024-01-15",
      "start_time": "09:00:00",
      "end_time": "17:00:00",
      "status": "available"
    }
  ]
}
```

---

## 📅 Bookings Management

### Create Booking
**POST** `/bookings/`

Create a new booking (Client only).

**Headers:**
- `Authorization: Bearer <client_access_token>`

**Request Body:**
```json
{
  "service_id": "uuid",
  "provider_id": "uuid",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T12:00:00Z",
  "notes": "Please walk my dog in the park",
  "total_amount": 50.0
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "client_id": "uuid",
  "provider_id": "uuid",
  "service_id": "uuid",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T12:00:00Z",
  "status": "pending",
  "total_amount": 50.0,
  "notes": "Please walk my dog in the park",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get My Bookings
**GET** `/bookings/me`

Get current user's bookings.

**Headers:**
- `Authorization: Bearer <access_token>`

**Query Parameters:**
- `status`: Filter by booking status
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "bookings": [
    {
      "id": "uuid",
      "service_id": "uuid",
      "provider_id": "uuid",
      "start_time": "2024-01-15T10:00:00Z",
      "end_time": "2024-01-15T12:00:00Z",
      "status": "confirmed",
      "total_amount": 50.0,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Provider Bookings
**GET** `/bookings/provider/me`

Get provider's bookings.

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Response:** `200 OK`
```json
{
  "bookings": [
    {
      "id": "uuid",
      "client_id": "uuid",
      "service_id": "uuid",
      "start_time": "2024-01-15T10:00:00Z",
      "end_time": "2024-01-15T12:00:00Z",
      "status": "pending",
      "total_amount": 50.0,
      "client_name": "John Doe",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Update Booking Status
**PUT** `/bookings/{booking_id}/status`

Update booking status (Provider only).

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Request Body:**
```json
{
  "status": "confirmed"  // "pending", "confirmed", "cancelled", "completed"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "confirmed",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## 🛍️ Items Management

### Create Item Category
**POST** `/items/categories`

Create a new item category (Admin only).

**Headers:**
- `Authorization: Bearer <admin_access_token>`

**Request Body:**
```json
{
  "name": "Handmade Jewelry",
  "description": "Beautiful handmade jewelry items"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "Handmade Jewelry",
  "description": "Beautiful handmade jewelry items",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### List Categories
**GET** `/items/categories`

Get list of all item categories.

**Response:** `200 OK`
```json
{
  "categories": [
    {
      "id": "uuid",
      "name": "Handmade Jewelry",
      "description": "Beautiful handmade jewelry items",
      "item_count": 15
    }
  ]
}
```

### Create Item
**POST** `/items/`

Create a new item for sale (Provider only).

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Request Body:**
```json
{
  "title": "Handmade Wooden Bowl",
  "description": "Beautiful hand-carved wooden bowl",
  "price": 45.99,
  "category_id": "uuid",
  "quantity_available": 5,
  "images": ["image1.jpg", "image2.jpg"]
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "seller_id": "uuid",
  "title": "Handmade Wooden Bowl",
  "description": "Beautiful hand-carved wooden bowl",
  "price": 45.99,
  "category_id": "uuid",
  "quantity_available": 5,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### List Items
**GET** `/items/`

Get list of all items with optional filtering.

**Query Parameters:**
- `category_id`: Filter by category
- `seller_id`: Filter by seller
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `status`: Filter by status
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "seller_id": "uuid",
      "title": "Handmade Wooden Bowl",
      "description": "Beautiful hand-carved wooden bowl",
      "price": 45.99,
      "category_id": "uuid",
      "quantity_available": 5,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### Get Item by ID
**GET** `/items/{item_id}`

Get specific item details.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "seller_id": "uuid",
  "title": "Handmade Wooden Bowl",
  "description": "Beautiful hand-carved wooden bowl",
  "price": 45.99,
  "category_id": "uuid",
  "quantity_available": 5,
  "status": "active",
  "images": ["image1.jpg", "image2.jpg"],
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## 📦 Orders Management

### Create Order
**POST** `/orders/`

Create a new order (Client only).

**Headers:**
- `Authorization: Bearer <client_access_token>`

**Request Body:**
```json
{
  "items": [
    {
      "item_id": "uuid",
      "quantity": 2,
      "price": 45.99
    }
  ],
  "shipping_address": {
    "street": "123 Main St",
    "city": "Toronto",
    "province": "ON",
    "postal_code": "M5V 3A8",
    "country": "Canada"
  },
  "total_amount": 91.98
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "client_id": "uuid",
  "status": "pending",
  "total_amount": 91.98,
  "shipping_address": {
    "street": "123 Main St",
    "city": "Toronto",
    "province": "ON",
    "postal_code": "M5V 3A8",
    "country": "Canada"
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get My Orders
**GET** `/orders/me`

Get current user's orders.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "orders": [
    {
      "id": "uuid",
      "status": "confirmed",
      "total_amount": 91.98,
      "created_at": "2024-01-01T00:00:00Z",
      "items": [
        {
          "item_id": "uuid",
          "quantity": 2,
          "price": 45.99
        }
      ]
    }
  ]
}
```

### Update Order Status
**PUT** `/orders/{order_id}/status`

Update order status (Provider only).

**Headers:**
- `Authorization: Bearer <provider_access_token>`

**Request Body:**
```json
{
  "status": "shipped"  // "pending", "confirmed", "shipped", "delivered", "cancelled"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "shipped",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## 💳 Payments Management

### Create Payment
**POST** `/payments/`

Create a payment for booking or order.

**Headers:**
- `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "booking_id": "uuid",  // Optional - for service payments
  "order_id": "uuid",    // Optional - for item payments
  "amount": 50.0,
  "payment_method": "stripe",
  "currency": "CAD"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "amount": 50.0,
  "currency": "CAD",
  "status": "pending",
  "payment_method": "stripe",
  "stripe_payment_intent_id": "pi_1234567890",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get My Payments
**GET** `/payments/me`

Get current user's payments.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "payments": [
    {
      "id": "uuid",
      "amount": 50.0,
      "currency": "CAD",
      "status": "completed",
      "payment_method": "stripe",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Update Payment Status
**PUT** `/payments/{payment_id}/status`

Update payment status (Admin only).

**Headers:**
- `Authorization: Bearer <admin_access_token>`

**Request Body:**
```json
{
  "status": "completed"  // "pending", "completed", "failed", "refunded"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "completed",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## 💬 Messaging System

### Send Message
**POST** `/messages/`

Send a message to another user.

**Headers:**
- `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "recipient_id": "uuid",
  "subject": "Booking Inquiry",
  "content": "Hi, I'm interested in your dog walking service.",
  "attachments": ["file1.jpg", "file2.pdf"]  // Optional
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "sender_id": "uuid",
  "recipient_id": "uuid",
  "subject": "Booking Inquiry",
  "content": "Hi, I'm interested in your dog walking service.",
  "is_read": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Conversation
**GET** `/messages/conversation/{user_id}`

Get conversation with specific user.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "conversation": [
    {
      "id": "uuid",
      "sender_id": "uuid",
      "recipient_id": "uuid",
      "subject": "Booking Inquiry",
      "content": "Hi, I'm interested in your dog walking service.",
      "is_read": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Mark Message as Read
**PUT** `/messages/{message_id}/read`

Mark a message as read.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "is_read": true,
  "read_at": "2024-01-01T00:00:00Z"
}
```

---

## 🔔 Notifications

### Get My Notifications
**GET** `/notifications/me`

Get current user's notifications.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "booking_confirmed",
      "title": "Booking Confirmed",
      "message": "Your dog walking booking has been confirmed",
      "is_read": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Mark Notification as Read
**PUT** `/notifications/{notification_id}/read`

Mark a notification as read.

**Headers:**
- `Authorization: Bearer <access_token>`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "is_read": true,
  "read_at": "2024-01-01T00:00:00Z"
}
```

### Update Notification Preferences
**PUT** `/notifications/preferences`

Update notification preferences.

**Headers:**
- `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "email_notifications": true,
  "sms_notifications": false,
  "push_notifications": true,
  "booking_updates": true,
  "marketing_emails": false
}
```

**Response:** `200 OK`
```json
{
  "message": "Notification preferences updated successfully"
}
```

---

## 🔍 Search & Discovery

### Search Services
**GET** `/search/services`

Search for services with various filters.

**Query Parameters:**
- `q`: Search query
- `type`: Service type filter
- `location`: Location filter
- `min_price`: Minimum price
- `max_price`: Maximum price
- `rating`: Minimum rating
- `available_date`: Available on specific date
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "services": [
    {
      "id": "uuid",
      "provider_id": "uuid",
      "type": "dog_walking",
      "title": "Professional Dog Walking",
      "description": "Expert dog walking services",
      "hourly_rate": 25.0,
      "rating": 4.8,
      "review_count": 15,
      "is_available": true
    }
  ],
  "total": 1,
  "filters_applied": {
    "type": "dog_walking",
    "location": "Toronto"
  }
}
```

### Search Items
**GET** `/search/items`

Search for items with various filters.

**Query Parameters:**
- `q`: Search query
- `category_id`: Category filter
- `min_price`: Minimum price
- `max_price`: Maximum price
- `seller_id`: Seller filter
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "seller_id": "uuid",
      "title": "Handmade Wooden Bowl",
      "description": "Beautiful hand-carved wooden bowl",
      "price": 45.99,
      "category": "Handmade Jewelry",
      "rating": 4.9,
      "review_count": 8
    }
  ],
  "total": 1
}
```

---

## 🏥 Health Check Endpoints

### Basic Health Check
**GET** `/health/`

Basic application health status.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "environment": "development"
}
```

### Database Health
**GET** `/health/database`

Database connection and performance status.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "response_time": 15.5,
  "connection": {
    "pool_size": 10,
    "checked_in": 8,
    "checked_out": 2,
    "overflow": 0
  },
  "tables": {
    "users": 150,
    "services": 45,
    "bookings": 200,
    "payments": 180
  }
}
```

### Redis Health
**GET** `/health/redis`

Redis cache status and performance.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "response_time": 2.1,
  "connection": {
    "host": "localhost",
    "port": 6379,
    "status": "connected"
  },
  "memory_usage": {
    "used_memory": 1024000,
    "used_memory_human": "1.0M",
    "maxmemory": 0
  }
}
```

### Detailed Health Report
**GET** `/health/detailed`

Comprehensive health report for all systems.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "database": {
    "status": "healthy",
    "response_time": 15.5
  },
  "redis": {
    "status": "healthy",
    "response_time": 2.1
  },
  "services": {
    "status": "healthy",
    "auth_service": "healthy",
    "user_service": "healthy",
    "booking_service": "healthy"
  },
  "summary": {
    "total_checks": 8,
    "healthy": 8,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

---

## 🔒 Security Features

### Rate Limiting
- **Login attempts**: 10 per minute per IP
- **API requests**: 100 per minute per user
- **File uploads**: 5 per minute per user
- **Password reset**: 3 per hour per email

### Authentication
- JWT access tokens (15 minutes expiry)
- Refresh tokens (30 days expiry)
- Password requirements: 8+ chars, uppercase, lowercase, digit, special char
- Account lockout after 5 failed login attempts

### Data Protection
- All passwords hashed with bcrypt
- Sensitive data excluded from API responses
- Input validation and sanitization
- SQL injection protection
- XSS protection headers

### File Upload Security
- File type validation (images only for profiles)
- File size limits (5MB for images)
- Secure file storage with unique names
- Virus scanning (planned)

---

## 📊 Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Common Error Codes
- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_REQUIRED`: Login required
- `INSUFFICIENT_PERMISSIONS`: Access denied
- `RESOURCE_NOT_FOUND`: Item not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_CREDENTIALS`: Wrong email/password
- `TOKEN_EXPIRED`: Access token expired
- `ACCOUNT_LOCKED`: Account temporarily locked

---

## 🚀 Getting Started

### 1. Register an Account
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "SecurePassword123!",
    "role": "client"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

### 3. Use the Access Token
```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Create a Service (Provider)
```bash
curl -X POST "http://localhost:8000/services/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "dog_walking",
    "title": "Professional Dog Walking",
    "description": "Expert dog walking services",
    "hourly_rate": 25.0,
    "daily_rate": 200.0,
    "terms": "Standard service terms"
  }'
```

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- All monetary amounts are in Canadian Dollars (CAD)
- File uploads require `multipart/form-data` content type
- Pagination uses `limit` and `offset` parameters
- Search endpoints support various filtering options
- Health check endpoints don't require authentication
- Rate limiting is applied per IP address and per user
- All endpoints return JSON responses

---

## 🔗 Related Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Security Documentation](docs/SECURITY.md)
- [Deployment Guide](README_DEPLOYMENT.md)
- [API Endpoint Reference](README_API.md)

---

*Last updated: January 2024*
*API Version: 1.0.0*
