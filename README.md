# 🍁 MapleHustle

MapleHustle is a Canadian services & marketplace platform built with **FastAPI** (backend) and **Nuxt.js** (frontend).  
It allows clients to book service providers (house sitting, dog walking, etc.) and buy/sell handmade products.  

---

## 🚀 Tech Stack
- **Backend**: FastAPI + SQLAlchemy + Alembic + PostgreSQL (PostGIS enabled)
- **Frontend**: Nuxt.js + TypeScript + Tailwind CSS + shadcn/ui
- **Authentication**: JWT (access + refresh tokens)
- **Infrastructure**: Docker + Docker Compose
- **Notifications**: Email + SMS (Twilio planned)
- **Payments**: Stripe integration

---

## 📂 Project Structure
MapleHustle/
├── app/ # FastAPI backend
│ ├── models/ # SQLAlchemy models
│ ├── schemas/ # Pydantic schemas
│ ├── routers/ # API routes (users, services, bookings, etc.)
│ ├── utils/ # Helpers (auth, hashing, deps)
│ └── db/ # DB session + base
├── alembic/ # Alembic migrations
├── frontend/ # Nuxt.js frontend (planned)
├── tests/ # Unit tests (to be added)
├── Dockerfile # Backend container
├── docker-compose.yml # Local dev setup
├── .env.example # Environment variables template
└── README.md # You are here