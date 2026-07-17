# Clinic Booking API

A  Django REST Framework (DRF) clinic booking system built to handle concurrent appointment scheduling, secure role-based access, and automated deployments.


LINKS AND METADATA
Deployed App: https://clinic-booking-api-fxvt.onrender.com

Production branch: main

Development branch: develop





## 1. System Design & Architectural Decisions

When building this clinic booking system, I designed the database models and scheduling logic around a **fixed-grid 30-minute slot architecture** rather than a dynamic, start-anytime calendar system.

### The Core Domain Models

* **Doctor**: Holds core operational data (e.g., name, specialization, email) and enforces availability boundaries via `opening_hours` and `closing_hours` fields.


* **Patient**: Links a user to their patient profile, preventing direct manipulation of client IDs.


* **Appointment**: Tracks the binding of a doctor, patient, a specific `slot_time` (stored in UTC), and the appointment's life cycle `status` (`CONFIRMED` or `CANCELLED`).



### Key Architectural & Design Decisions

* **Fixed-Grid Slots**: By requiring appointments to start exactly on the hour or half-hour.If we let patients choose arbitrary times (like 10:15 to 10:45), it creates weird, un-bookable time gaps in a doctor's day. A fixed grid maximizes the doctor’s schedule and makes checking availability straightforward.
* **Timezone Safety**: The entire system processes, stores, and evaluates timestamps strictly in UTC.Everything is stored in UTC in the database. When the API returns slot times, it uses standard ISO 8601 formatting with UTC offsets. This keeps the database clean and lets the frontend handle converting times to the user's local timezone. Local time representations are handled exclusively at the presentation layer.
* **Database-Level Enforcements: To prevent duplicate bookings under high-concurrency loads, a unique database-level constraint is established on the combination of `(doctor, slot_time)` where status is confirmed.
* **Safe Rescheduling: Rescheduling an appointment runs inside a single @transaction.atomic database block. Before freeing up the old slot, we verify and lock down the new slot. If the new slot is taken or validation fails, the entire transaction rolls back. This ensures the patient never loses their original spot if the reschedule fails mid-way.



### Handling Edge Cases & System Constraints

* **Changing Doctor Working Hours**: If a doctor's working hours shrink, existing bookings outside the new hours remain locked in the database. Any new availability checks or rescheduling attempts, however, will reject slots falling outside the updated window.
* **Atomic Rescheduling**: Rescheduling is performed as an atomic operation (`transaction.atomic`). The previous slot is marked cancelled/released and the new slot is claimed in a single database transaction. If the new slot is taken during the process, the transaction rolls back, and the patient preserves their original appointment.




## 2. API Reference & Implementation Status

The API was built using **Django REST Framework** with a clean service-selector pattern.

### Core Endpoints

#### `POST /api/v1/appointments/`

Books an appointment slot.

* **Payload**:
```json
{
  "doctor": 1,
  "slot_time": "2026-07-20T10:00:00Z"
}

```


* **Status Codes**: `201 Created` on success, `400 Bad Request` if validation fails (e.g., slot taken, past date, outside hours), or `401 Unauthorized`.

#### `GET /api/v1/doctors/{id}/availability/?date=YYYY-MM-DD`

Retrieves free 30-minute slots for a specific doctor on a given date.

* **Status Codes**: `200 OK`, `400 Bad Request` if date parameter is malformed or missing.

#### `PATCH /api/v1/appointments/{id}/cancel/`

Cancels an appointment.

* **Payload**:
```json
{
  "reason": "Family emergency"
}

```


* **Status Codes**: `200 OK` on success, `400 Bad Request` if already cancelled, or `403 Forbidden` if a patient attempts to cancel an appointment they do not own.



#### `PATCH /api/v1/appointments/{id}/reschedule/`

Moves an appointment to a new slot.

* **Payload**:
```json
{
  "new_slot_time": "2026-07-20T11:30:00Z"
}

```


* **Status Codes**: `200 OK` on success, `400 Bad Request` if the slot is taken or the appointment was already cancelled, or `403 Forbidden`.

#### `GET /api/v1/patients/{id}/appointments/` (Bonus)

Retrieves a patient's upcoming, active appointments sorted chronologically.

* **Status Codes**: `200 OK`, `403 Forbidden` if requesting another patient's data.



---

### Testing the Live API (Authentication Flow)

Because the booking, rescheduling, and cancellation endpoints are secured with JSON Web Tokens (JWT) to protect patient privacy, hitting `/api/v1/appointments/` directly in a browser will naturally return a `401 Unauthorized` response. 

To test the secured endpoints on the live server using **Postman**, **Insomnia**, or **cURL**, follow this simple flow:

#### Step 1: Get an Access Token
You can use the default seeded patient credentials to authenticate. Send a `POST` request to the token endpoint:
* **Endpoint**: `https://clinic-booking-api-fxvt.onrender.com/api/v1/token/` 
* **Payload (JSON)**:
  ```json
  {
    "username": "patient_kamau",
    "password": "securepassword123"
  }


#### Step 2: Authorize Your Requests
For any write operations (booking, cancelling, or rescheduling), add the token to your request headers:
* **Header Key**: `Authorization`
* **Header Value**: `Bearer <YOUR_ACCESS_TOKEN_HERE>`

*(Note: The availability endpoint `GET /api/v1/doctors/{id}/availability/` is entirely public and can be tested directly in your web browser without any authentication tokens!)*

---




## 3. Concurrency, Security, & Implementation Details

To achieve high stability, specific architectural choices were implemented directly into the codebase:

### Solving the 200ms Concurrent Booking Race Condition

A major pitfall of appointment schedulers is when two clients attempt to reserve the same spot within milliseconds of each other. Standard check-then-write code flows will cause double-bookings. We solved this using two mechanisms:

1. **Pessimistic Locking**: `select_for_update()` inside a `transaction.atomic()` block during booking operations. This locks the checked rows, forcing parallel transactions targeting the same resource to queue up sequentially.


2. **Unique Constraints**: A composite database constraint ensures `(doctor_id, slot_time)` is unique for all active appointments, preventing double-write failures at the engine level.



### Secure Authentication 

* **Authentication**: Enforced via JWT (`rest_framework_simplejwt`). Users are authenticated on all write/read operations except for the public doctor availability endpoint.


* **No Client-Side Spoofing**: Instead of relying on a user-submitted `patient_id` body payload, the system extracts the authenticated user from the token context (`request.user`) and resolves their respective `Patient` profile safely.


* **Personal info Protection**: Responses strictly serialize public doctor data and secure patient references, fully withholding private contact details like phone numbers or direct internal keys.

---

## 4. Local Setup & Docker Instructions

### Prerequisites

* Python 3.11+ (if running bare metal)
* Docker & Docker Compose

### Running via Docker Compose (Recommended)

1. Clone this repository and navigate to the root directory.
2. Build and start the container network:
```bash
docker-compose up --build

```


3. Run the migrations:
```bash
docker-compose exec web python manage.py migrate

```


4. Seed mock doctor and patient data for testing:
```bash
docker-compose exec web python manage.py seed_db

```



The application will run locally at `http://localhost:8000`.

### Running Locally without Docker

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```


2. Install the required dependencies:
```bash
pip install -r requirements.txt

```


3. Apply migrations, seed data, and start the server:
```bash
python manage.py migrate
python manage.py seed_db
python manage.py runserver

```



### Running the Test Suite

We use `pytest` with `pytest-django` to execute unit and concurrency tests. Run them via:

```bash
docker-compose exec web pytest
# Or locally:
pytest

```

---

## 5. Deployment & CI/CD Setup

### Deployment

* **Hosting Platform**: The API is deployed to Render.


* **Live Public URL**: ` https://clinic-booking-api-fxvt.onrender.com `


### CI/CD Pipeline

The integration pipeline is powered by **GitHub Actions** (`.github/workflows/ci-cd.yml`):

* **Trigger Branch**: Pull requests to the `main` branch trigger the validation phase.


* **Test Suite execution**: Runs the complete test suite (using PostgreSQL/SQLite) on every pull request. If any test fails, the build is blocked.


* **Auto-Deployment**: Merging into the `main` branch triggers an automated deployment hook to Render, ensuring zero-downtime updates of tested code.



---

## 6. AI Reflection

Consistent with the requirements of Section 4, here is a transparent breakdown of how AI tools were utilized during development:

1. **What did you use AI for?**
AI was utilized as a pairing assistant for:
(Brainstorming Schema Options): Discussing the database layout—specifically, whether to keep things overly simple by just storing an unvalidated patient_id integer versus creating a structured Patient model.

(Boilerplate Generation & File setup): Generating standard configurations like the base .github/workflows/ci.yml syntax and basic pytest import blocks to save time on setup.I used AI to also quickly generate the initial empty class skeletons and imports for services.py and selectors.py. This saved me from typing repetitive CRUD boilerplate.

(Refactoring): I initially used APIView which requires manually defining each HTTP method. AI suggested refactoring to ViewSet with @action decorators because it groups related operations on the same resource together, uses DefaultRouter to auto-generate URLs, and is more idiomatic DRF for resource-based APIs. The tradeoff is slightly less explicit URL control, but for standard REST resources it's cleaner.

2. **An example where AI improved your work:**
* **The Prompt**: I'm building a clinic booking API in Django. For the appointments, I need to associate them with a patient. Should I just use a raw integer patient_id on the Appointment model to keep things simple, or should I import Django's default User model and link to that directly? I want to make sure the database is secure, but I don't want to overcomplicate the architecture early on
* **The Improvement**: When discussing how to model patients, I initially considered either importing the Django User model directly or just storing a raw integer patient_id.  The AI pointed out that importing the User model directly makes the code fragile if we ever swap the user model later. Instead, it suggested creating a dedicated Patient model that links to settings.AUTH_USER_MODEL.
This kept the database relational and secure while following Django best practices for swappable user architectures. 


3. **An example where AI was wrong or incomplete:**
The Issue:
When generating the initial database seeder script and test fixtures, the AI used relative dates based on timezone.now() + timedelta(hours=2) for booking appointments.

How it was caught/fixed: 
If tests were executed late at night, the relative clock calculation shifted the test slot out of the doctor's standard working hours (08:00 - 17:00), 
causing the tests to fail in CI/CD. I caught this by reading the traceback logs in GitHub Actions, realizing the clock was the issue, and manually rewrote the test fixtures and seed script to target a static "tomorrow at 10:00 AM" slot using explicit .replace(hour=10) logic.





4. **Decisions made without AI:**
-Using the Services & Selectors Pattern: I chose not to write heavy models or put business logic inside views.
Separating writes (services.py) from reads (selectors.py) is a clean-code choice I made to keep the business logic highly testable and independent of the web framework.

-Dual-Layer Concurrency Defense:Instead of defaulting to  simple application-level checks, I combined database-level row locks (select_for_update) with a physical SQL UniqueConstraint to make  sure the system cannot double-book, even under massive concurrent load.

-Authentication using JWT : I decided to add authentication even though it was an ambigous requirement.I implemeted authentication to ensure not just anyine can book an appointment and patients can only access their appointments.I settled for JWT with custom permissions instead of session based auth because it is stateless and scales horizontally.





