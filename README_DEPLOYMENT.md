# 🚀 Maple Hussle API – Deployment Guide

This guide explains how to set up and run the project locally or in Docker.

---

## 📦 Requirements
- Python 3.9+ (for local dev)
- Docker & Docker Compose
- PostgreSQL 14+
- Poetry (optional, for dependency management)

---

## 🔑 Environment Variables
Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/maplehussle

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Email / SMS (optional integrations)
SMTP_SERVER=smtp.yourhost.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=yourpassword

TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
