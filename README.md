# CompMS — Competition Management System
## Django project: Event Creation + Student Registration + Payment Verification

---

## Database Schema

```
┌──────────────────────────────────────────────────────────┐
│  auth_user  (Django built-in)                            │
│    id, username, email, first_name, last_name            │
│    is_staff → True = Admin                               │
└──────────────────────┬───────────────────────────────────┘
                       │ OneToOne
           ┌───────────▼──────────────┐
           │  StudentProfile           │
           │    college, phone         │
           └───────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Event                                                   │
│    name, description, date, venue                       │
│    category  (technical/cultural/sports/other)          │
│    event_type  (solo/group/both)                        │
│    registration_fee, max_participants                   │
│    upi_id, is_active                                    │
│    created_by → FK(User)                                │
└──────────────────────┬──────────────────────────────────┘
                       │ FK
           ┌───────────▼──────────────────────────────┐
           │  Registration                              │
           │    student → FK(User)                     │
           │    event   → FK(Event)                    │
           │    participation_type (solo/group)        │
           │    group_name, member_names               │
           │    payment_screenshot (ImageField)        │
           │    payment_status                         │
           │      not_uploaded → pending               │
           │      → verified  OR  → rejected           │
           │    unique_code  (e.g. TEC-8472)           │
           │    verified_by → FK(User/admin)           │
           └───────────────────────────────────────────┘
```

---

## Quick Start

### 1. Prerequisites
```bash
Python 3.10+  must be installed
```

### 2. Install & setup (one command)
```bash
cd compms_project
python setup.py
```
This installs Django, runs migrations, and creates the admin account.

### 3. Start the server
```bash
python manage.py runserver
```
Open → http://127.0.0.1:8000

---

## Login Accounts

| Role    | URL                       | Username | Password  |
|---------|---------------------------|----------|-----------|
| Admin   | /login/                   | admin    | admin123  |
| Student | /signup/ (create your own)| —        | —         |

---

## Feature Walkthrough

### Admin Flow
1. Login as admin → redirected to **Dashboard**
2. Go to **Events** → click **+ New Event**
3. Fill: name, date, venue, fee, UPI ID, participation type → **Create**
4. Go to **Registrations** to see all students
5. When a student uploads a screenshot → badge shows **"Under Review"**
6. Click **Verify** → see screenshot → choose Verify ✓ or Reject ✗
7. On verify → unique code (e.g. `TEC-8472`) is auto-generated

### Student Flow
1. Sign up → redirected to **Browse Events**
2. Click **Register →** on an event
3. Choose Solo or Group (fill team name + members if group)
4. Redirected to **Upload Payment** page
5. Pay the UPI ID shown, take screenshot, upload it
6. Go to **My Registrations** to track status
7. After admin verifies → unique code shown on the page

---

## URL Map

```
/                           → redirect to dashboard or events
/login/                     → login page
/signup/                    → student sign up
/logout/                    → logout

/events/                    → student: browse events
/events/<id>/register/      → student: fill registration form
/payment/<id>/upload/       → student: upload screenshot
/my-registrations/          → student: track status

/admin-panel/               → admin: dashboard
/admin-panel/events/        → admin: list events
/admin-panel/events/new/    → admin: create event
/admin-panel/events/<id>/edit/    → admin: edit event
/admin-panel/events/<id>/toggle/  → admin: activate/deactivate
/admin-panel/registrations/       → admin: all registrations + filter
/admin-panel/verify/<id>/         → admin: verify/reject payment
```

---

## Project Structure
```
compms_project/
├── manage.py
├── setup.py          ← run this first
├── requirements.txt
├── compms/           ← Django project config
│   ├── settings.py
│   └── urls.py
├── events/           ← main app
│   ├── models.py     ← Event, Registration, StudentProfile
│   ├── views.py      ← all logic
│   ├── forms.py      ← all forms
│   └── urls.py
├── templates/
│   ├── base.html
│   ├── registration/ (login, signup)
│   ├── admin_panel/  (dashboard, events, registrations, verify)
│   └── events/       (list, register, upload, my-registrations)
└── media/            ← payment screenshots stored here
```
