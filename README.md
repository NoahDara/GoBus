# GoBus — Online Bus Ticket Booking System

A Django-powered web application for online bus ticket reservations. Built for Solusi University students to replace the manual, cash-on-bus ticketing system.

**Status:** Development  
**Team:** Noah Dara, [Other Team Members]  
**Institution:** Solusi University  
**Course:** INSY 452 – Systems Analysis and Design 2

---

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Development Workflow](#development-workflow)
- [Deployment](#deployment)
- [Team Roles](#team-roles)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Problem Statement

**Current System Issues:**
- Manual, cash-on-bus booking system is time-consuming
- Long queues at departure times
- No real-time seat availability information
- Lack of flexibility (can't book outside working hours)
- Manual records prone to errors and duplication
- Buses often overloaded; students stand for long distances
- Poor user experience and safety concerns

**Target Users:** Solusi University students and commuters using university bus services.

---

## ✨ Solution Overview

GoBus is a web-based bus ticket reservation system that enables:
- **Students** to book seats online, pay digitally, and receive e-tickets
- **Administrators** to manage routes, schedules, drivers, and view analytics
- **Drivers** to receive trip assignments and manage their schedules
- **Secure, transparent payment** processing via Paynow (Ecocash mobile money)

### Key Benefits
✅ **Convenience** — Book anytime, anywhere (24/7)  
✅ **Transparency** — Real-time seat availability and pricing  
✅ **Safety** — No overloading; proper seat allocation  
✅ **Efficiency** — Automated booking & payment confirmation  
✅ **Accessibility** — Mobile-friendly responsive design  
✅ **Security** — User authentication, encrypted payment data  

---

## 🚀 Features

### For Students/Passengers
- **User Registration** — Google OAuth or email/password signup
- **Route & Schedule Search** — View available buses by date, time, and route
- **Seat Selection** — Visual seat map with real-time availability
- **Flexible Boarding** — Board and alight at any stop along the route
- **Dynamic Pricing** — Pay only for the segment you travel
- **Mobile Payment** — Ecocash via Paynow USSD
- **Booking Management** — View, modify, or cancel bookings
- **E-Tickets** — Digital confirmation and receipt
- **Notifications** — Email confirmations for bookings and payments

### For Administrators
- **Route Management** — Create routes with multiple stops and segment pricing
- **Bus Fleet Management** — Add/edit buses, manage capacity and status
- **Driver Management** — Assign drivers to buses, view driver details
- **Schedule Creation** — Set up trip schedules with departure/arrival times
- **Booking Analytics** — View all bookings, revenue reports, occupancy rates
- **Payment Audit Trail** — Track all payments, check statuses
- **User Management** — View students, manage accounts

### For Drivers
- **Secure Login** — Email/password authentication
- **Trip Details** — View assigned trips and route information
- **Passenger Manifest** — See booked passengers and their stops

---

## 🛠️ Tech Stack

### Backend
- **Framework:** Django 4.x (Python)
- **Database:** PostgreSQL (recommended) / MySQL / SQLite (dev)
- **ORM:** Django ORM
- **Authentication:** Django Auth + Google OAuth (django-allauth)
- **Payments:** Paynow API (Ecocash mobile money)
- **Email:** Django Mail Backend

### Frontend
- **Template Engine:** Django Templates
- **CSS Framework:** Bootstrap 5
- **JavaScript:** Vanilla JS + jQuery (minimal)
- **Icons:** Bootstrap Icons / Tabler Icons

### DevOps
- **Server:** Nginx + Gunicorn (production)
- **Process Manager:** Supervisor or systemd
- **Version Control:** Git
- **Deployment:** Linux Server (Ubuntu)

---

## 📁 Project Structure

```
GoBus/
├── core/                    # Project settings & configuration
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL routes
│   ├── wsgi.py             # WSGI entry point
│   └── asgi.py             # ASGI entry point (async)
│
├── helpers/                # Shared utilities & base models
│   ├── models.py           # BaseModel (UUID, timestamps)
│   ├── context_processors.py
│   ├── middleware.py
│   ├── mixins.py           # View mixins
│   └── emails.py           # Email utilities
│
├── accounts/               # User authentication & authorization
│   ├── models.py           # (Uses Django User model)
│   ├── views.py            # Login, logout, registration
│   └── urls.py
│
├── drivers/                # Driver management
│   ├── models.py           # Driver model
│   ├── views.py            # Driver CRUD
│   ├── signals.py          # Auto-creates User for driver
│   └── helpers.py
│
├── buses/                  # Bus & route management
│   ├── models.py           # Bus, Seat, Route, RouteStop, RouteSegment, Schedule
│   ├── views.py            # Bus, route, schedule views
│   ├── signals.py          # Auto-generates seats, reverse routes
│   ├── helpers.py          # Seat generation, reverse route logic
│   └── urls.py
│
├── bookings/               # Booking & seat reservation
│   ├── models.py           # Booking model
│   ├── views.py            # Booking creation, cancellation
│   ├── signals.py          # Auto-generates booking reference
│   ├── helpers.py          # Seat availability, fare calculation
│   └── urls.py
│
├── payments/               # Payment processing (Paynow)
│   ├── models.py           # Payment model
│   ├── views.py            # Payment initiation, webhooks
│   ├── signals.py          # Payment confirmation logic
│   ├── helpers.py          # Paynow service, payment tracking
│   └── urls.py
│
├── notifications/          # Email notifications
│   ├── models.py           # Notification audit trail
│   ├── views.py            # (Mostly auto-triggered)
│   ├── signals.py          # Triggers on booking/payment
│   ├── helpers.py          # Email sending logic
│   └── urls.py
│
├── dashboard/              # Admin analytics & reporting
│   ├── models.py           # (Uses other apps' models)
│   ├── views.py            # Dashboard, reports, charts
│   └── urls.py
│
├── templates/              # HTML templates
│   ├── layouts/
│   │   ├── base.html       # Base layout
│   │   └── admin_base.html # Admin layout
│   ├── auth/               # Login, registration pages
│   ├── buses/              # Bus/route templates
│   ├── bookings/           # Booking templates
│   ├── payments/           # Payment templates
│   ├── emails/             # Email templates
│   └── dashboard/          # Dashboard templates
│
├── static/                 # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── images/
│
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── reset_migrations.sh     # Utility to reset DB
└── README.md              # This file
```

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- Virtual environment tool (venv)
- PostgreSQL 12+ (recommended) or MySQL 5.7+
- Git

### 1. Clone Repository

```bash
git clone https://github.com/NoahDara/GoBus.git
cd GoBus
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql  # or mysql
DB_NAME=gobus_db
DB_USER=gobus_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Email (Gmail example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@gobus.local

# Paynow (Mobile Payment)
PAYNOW_INTEGRATION_ID=your-integration-id
PAYNOW_INTEGRATION_KEY=your-integration-key
PAYNOW_DOMAIN=localhost:8000  # Change to domain in production

# Google OAuth (Optional)
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
```

### 5. Create Database

```bash
# Using PostgreSQL
createdb gobus_db
createuser gobus_user
# Set password and grant privileges in psql

# Or use SQLite (dev only)
# No setup needed, Django creates it automatically
```

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
# Follow prompts to enter username, email, password
```

### 8. Load Fixtures (Optional Test Data)

```bash
python manage.py loaddata fixtures/test_data.json
```

### 9. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

---

## ⚙️ Configuration

### Django Settings (`core/settings.py`)

Key settings to review:
- `INSTALLED_APPS` — Ensure all apps are registered
- `DATABASES` — Set to your database
- `ALLOWED_HOSTS` — Add your domain
- `STATIC_URL`, `MEDIA_URL` — File upload paths
- `EMAIL_*` — Configure email backend

### Database Configuration

Update `core/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}
```

### Paynow Integration

1. Register at [Paynow Zimbabwe](https://www.paynow.co.zw/)
2. Get your Integration ID and Key
3. Add to `.env`:
```env
PAYNOW_INTEGRATION_ID=xxxx
PAYNOW_INTEGRATION_KEY=xxxx
```

---

## 🗄️ Database Schema

### Core Models

#### **Buses App**
- **Bus** — Physical bus in fleet (driver FK, capacity, status)
- **Seat** — Individual seat on a bus (row, seat_number)
- **Route** — Named route (origin, destination, reverse route link)
- **RouteStop** — Individual stop on a route (order, name)
- **RouteSegment** — Pricing between consecutive stops (price)
- **Schedule** — Specific trip instance (bus, route, departure/arrival times)

#### **Drivers App**
- **Driver** — Bus driver (linked to User via OneToOne, license_number, expiry)

#### **Bookings App**
- **Booking** — Passenger seat reservation
  - `user` FK → User
  - `schedule` FK → Schedule
  - `seat` FK → Seat
  - `boarding_stop`, `alighting_stop` FK → RouteStop
  - `fare` (calculated from RouteSegments)
  - `status` (pending → confirmed)
  - `booking_reference` (auto-generated)

#### **Payments App**
- **Payment** — Payment record for a booking
  - `booking` OneToOne → Booking
  - `user` FK → User
  - `phone_number` (Ecocash)
  - `amount` (from booking.fare)
  - `payment_reference` (from Paynow)
  - `poll_url` (for status checking)
  - `status` (pending → paid)

#### **Notifications App**
- **Notification** — Audit trail of all notifications
  - `user`, `booking`, `payment` FKs
  - `notification_type` (confirmation, failure, etc.)
  - `channel` (email, sms)
  - `status` (pending → sent)

---

## 🔌 API Endpoints

### Authentication
- `POST /accounts/login/` — User login
- `POST /accounts/logout/` — User logout
- `POST /accounts/register/` — User registration
- `GET /accounts/google-oauth/` — Google OAuth callback

### Routes & Schedules
- `GET /buses/routes/` — List all routes
- `GET /buses/routes/<id>/` — Route details with stops
- `GET /buses/schedules/` — List schedules (filtered by date/route)

### Bookings
- `POST /bookings/create/` — Create new booking
- `GET /bookings/` — User's bookings
- `GET /bookings/<id>/` — Booking details
- `POST /bookings/<id>/cancel/` — Cancel booking

### Payments
- `POST /payments/initiate/` — Start mobile payment
- `GET /payments/status/<poll_url>/` — Check payment status
- `POST /payments/webhook/result/` — Paynow callback

### Dashboard (Admin)
- `GET /dashboard/` — Overview
- `GET /dashboard/bookings/` — Booking analytics
- `GET /dashboard/revenue/` — Revenue reports
- `GET /dashboard/buses/` — Bus/driver management

---

## 🔄 Development Workflow

### Adding a New Feature

1. **Create Migration**
   ```bash
   python manage.py makemigrations [app_name]
   ```

2. **Apply Migration**
   ```bash
   python manage.py migrate
   ```

3. **Write Views/Logic**
   ```python
   # In [app_name]/views.py
   class MyView(View):
       def get(self, request):
           # Implementation
   ```

4. **Update URLs**
   ```python
   # In [app_name]/urls.py
   urlpatterns = [
       path('endpoint/', MyView.as_view(), name='endpoint-name'),
   ]
   ```

5. **Create Tests** (Recommended)
   ```python
   # In [app_name]/tests.py
   from django.test import TestCase
   ```

6. **Test Locally**
   ```bash
   python manage.py runserver
   # Visit http://localhost:8000
   ```

### Database Reset (Development Only)

```bash
bash reset_migrations.sh
# Or manually:
python manage.py migrate [app_name] zero  # Rollback
python manage.py makemigrations
python manage.py migrate
```

### Code Style

- Follow PEP 8 (use `black` or `flake8`)
- Use meaningful variable names
- Add docstrings to functions/classes
- Keep views under 150 lines (extract logic to helpers/services)

---

## 🚀 Deployment

### Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Nginx web server
- Gunicorn WSGI server
- PostgreSQL database
- SSL certificate (Let's Encrypt free)

### Steps

1. **Install System Dependencies**
   ```bash
   sudo apt update && sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib
   ```

2. **Clone and Setup**
   ```bash
   git clone https://github.com/NoahDara/GoBus.git /var/www/gobus
   cd /var/www/gobus
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with production values
   ```

4. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Setup Gunicorn**
   ```bash
   # Create gunicorn socket/service file
   sudo nano /etc/systemd/system/gobus.service
   ```
   ```ini
   [Unit]
   Description=GoBus Django Application
   After=network.target
   
   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/gobus
   ExecStart=/var/www/gobus/venv/bin/gunicorn \
       --workers 3 \
       --bind unix:/var/www/gobus/gunicorn.sock \
       core.wsgi:application
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/gobus
   ```
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location /static/ {
           alias /var/www/gobus/static/;
       }
       
       location /media/ {
           alias /var/www/gobus/media/;
       }
       
       location / {
           proxy_pass http://unix:/var/www/gobus/gunicorn.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Enable and Start Services**
   ```bash
   sudo systemctl enable gobus
   sudo systemctl start gobus
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

8. **Setup SSL (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

---

## 👥 Team Roles

| Name | Role | Responsibilities |
|------|------|------------------|
| Noah Dara | Project Lead | Project setup, architecture, deployment |
| [Member 2] | Backend Developer | Models, views, API endpoints |
| [Member 3] | Frontend Developer | Templates, UI/UX, Bootstrap |
| [Member 4] | Database Design | Schema, migrations, optimization |

---

## 🤝 Contributing

### Branch Naming
- Feature: `feature/description`
- Bugfix: `bugfix/description`
- Hotfix: `hotfix/description`

### Commit Messages
```
[TYPE] Brief description

Detailed explanation if needed.
- Related issue: #123
```

### Pull Request Workflow
1. Create feature branch from `develop`
2. Make changes and commit
3. Push to GitHub
4. Create PR with description
5. Code review by team
6. Merge to `develop`
7. Merge `develop` → `main` for releases

---

## 📝 License

This project is part of INSY 452 coursework at Solusi University.  
All rights reserved © 2025 Noah Dara & Team.

---

## 📞 Support & Issues

- **Documentation:** See `docs/` folder
- **Bug Reports:** Create GitHub Issue
- **Questions:** Contact team members via email
- **Meeting:** Every [day] at [time]

---

## 🎓 Academic Notes

This is a **group project** for **INSY 452 — Systems Analysis and Design 2** at Solusi University. The system was designed following proper SDLC methodology including:

- Requirements gathering & analysis
- System design (architecture, database schema)
- Implementation using Django framework
- Testing (unit & integration tests)
- Deployment on production server
- Documentation & maintenance

**Submission Date:** [Course End Date]  
**Status:** In Active Development

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-05-27 | Initial scaffold, app structure |
| 0.2.0 | TBD | Models complete, migrations |
| 0.3.0 | TBD | Views & templates |
| 0.4.0 | TBD | Payment integration |
| 0.5.0 | TBD | Testing & optimization |
| 1.0.0 | TBD | Production release |

---

**Last Updated:** May 27, 2025  
**Maintained By:** Noah Dara