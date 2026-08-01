# 🍔 Café Delivery App

A full-stack food & drink delivery platform built with **Django REST Framework** and **React**. Order your favorites, pay online via Chapa, and track delivery in real time.

---

## ✨ Features

| Customer | Admin |
|---|---|
| Browse food & drink menu | Manage all orders |
| Add to cart & checkout | Update order status live |
| GPS-based delivery fee | Dashboard with revenue stats |
| Pay online (Chapa) or cash | Manage menu items |
| Real-time order tracking | Analytics & user management |
| Order history | Export & filter orders |

---

## 🛠 Tech Stack

**Backend** — Django 5.2 · DRF · SimpleJWT · Chapa API · SQLite / PostgreSQL · WhiteNoise · Gunicorn

**Frontend** — React 19 · Vite · Tailwind CSS · Framer Motion · Axios · React Router

**DevOps** — Docker · Docker Compose · Nginx (production)

---

## 🚀 Quick Start

### Without Docker

```bash
# Backend
cd backend
py -3.12 -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev
```

### With Docker

```bash
docker compose up --build
```

- Frontend → http://localhost:3000  
- Backend API → http://localhost:8000/api

---

## 🔑 Environment Variables

Copy `.env` in `/backend` and fill in:

```env
SECRET_KEY=your-django-secret
CHAPA_SECRET_KEY=your-chapa-key
FRONTEND_URL=http://localhost:3000
```

---

## 💳 Payment Flow

1. Customer places order → chooses **Chapa** or **Cash**
2. Chapa redirects to checkout page
3. On return, backend verifies the transaction
4. Order marked **paid** automatically

---

## 📁 Project Structure

```
delivery-app/
├── backend/          # Django API
│   ├── orders/
│   ├── payments/
│   ├── menu/
│   └── users/
├── frontend/         # React SPA
│   └── src/
│       ├── pages/
│       ├── components/
│       └── api/
├── docker-compose.yml
└── README.md
```

---

