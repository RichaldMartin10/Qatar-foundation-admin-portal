# Qatar Foundation Admin Portal

A full backend implementation for the Qatar Foundation Admin Portal built using Python and Flask. This project integrates the provided Admin UI with a functional backend while keeping the frontend design and layout unchanged.

## Overview

The project implements:

* Admin Authentication System
* Opportunity Management System
* Secure Session Handling
* Database Persistence
* CRUD Operations for Opportunities

The frontend UI was pre-built and remained unchanged. Only backend logic and JavaScript API integration were implemented.

---

## Tech Stack

### Backend

* Python
* Flask
* Flask-SQLAlchemy
* Flask-CORS
* SQLite

### Frontend

* HTML
* CSS
* JavaScript

### Security

* Werkzeug Password Hashing
* Flask Sessions

---

## Features

## Authentication

* Admin Signup
* Admin Login
* Remember Me Functionality
* Forgot Password Token Generation
* Logout
* Session Persistence

---

## Opportunity Management

* Create New Opportunity
* View All Opportunities
* View Opportunity Details
* Edit Opportunity
* Delete Opportunity

---

## Security Features

* Password Hashing
* Protected API Routes
* Ownership-Based Access Control
* Session Validation
* Generic Authentication Error Messages

---

## Database Schema

### Admin Table

Stores admin account information.

Fields:

* id
* full_name
* email
* password_hash
* created_at

---

### Opportunity Table

Stores opportunity details linked to admins.

Fields:

* id
* admin_id
* name
* duration
* start_date
* description
* skills
* category
* future_opportunities
* max_applicants
* created_at

---

### Password Reset Table

Stores reset tokens for forgot password functionality.

Fields:

* id
* admin_id
* token
* expires_at
* used

---

## API Endpoints

### Authentication APIs

```bash
POST /api/signup
POST /api/login
POST /api/logout
POST /api/forgot-password
GET /api/me
```

---

### Opportunity APIs

```bash
GET /api/opportunities
POST /api/opportunities
GET /api/opportunities/<id>
PUT /api/opportunities/<id>
DELETE /api/opportunities/<id>
```

---

## Project Structure

```bash
Qatar-foundation-admin-portal/
│── app.py
│── models.py
│── requirements.txt
│── templates/
│   └── admin.html
│── sky/
│   ├── admin.css
│   └── admin.js
│── instance/
│   └── qf_admin.db
│── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/RichaldMartin10/Qatar-foundation-admin-portal.git
cd Qatar-foundation-admin-portal
```

---

### Create Virtual Environment

```bash
python -m venv venv
```

Activate:

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Run Application

```bash
python app.py
```

---

## Access Application

Open in browser:

```bash
http://localhost:5000
```

---

## Testing Workflow

1. Register a new admin account
2. Login with credentials
3. Create opportunities
4. View created opportunities
5. Edit opportunities
6. Delete opportunities
7. Logout
8. Login again
9. Verify data persistence

---

## Implementation Highlights

* Existing UI preserved without redesign
* Hardcoded opportunity cards removed
* Dynamic opportunity loading from database
* Edit/Delete functionality added
* Data isolation between admin accounts
* Session persistence implemented

---

## Future Improvements

* Complete Reset Password Flow
* Email Integration
* Better Input Validation
* Opportunity Search & Filters
* Admin Profile Settings

---

## Author

Richald Martin,
MCA Student,
Nitte Meenakshi Institute of Technology.
