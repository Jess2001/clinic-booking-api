import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from appointments.models import Doctor, Patient, Appointment

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def doctor():
    return Doctor.objects.create(
        full_name="Alice Mwangi",
        email="alice@clinic.com",
        specialization="Cardiology",
        opening_hours=time(8, 0),
        closing_hours=time(17, 0)
    )


@pytest.fixture
def patient_user():
    user = User.objects.create_user(username="patient_user", password="securepassword123")
    Patient.objects.create(user=user)
    return user


@pytest.fixture
def other_patient_user():
    user = User.objects.create_user(username="other_user", password="securepassword123")
    Patient.objects.create(user=user)
    return user


@pytest.fixture
def authenticated_client(api_client, patient_user):
    token = AccessToken.for_user(patient_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def valid_slot():
    tomorrow = timezone.now() + timedelta(days=1)
    return tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)


# 1. BOOKING ENDPOINT TESTS 

def test_booking_anonymous_user_is_unauthorized(api_client, doctor, valid_slot):
    """Anonymous requests must be blocked by JWT middleware."""
    response = api_client.post("/api/v1/appointments/", {
        "doctor": doctor.id,
        "slot_time": valid_slot.isoformat()
    })
    assert response.status_code == 401


def test_booking_authenticated_user_succeeds(authenticated_client, doctor, valid_slot):
    """Authenticated request successfully infers patient identity from JWT token."""
    response = authenticated_client.post("/api/v1/appointments/", {
        "doctor": doctor.id,
        "slot_time": valid_slot.isoformat()
    })
    assert response.status_code == 201
    assert response.data["patient_details"]["full_name"] == ""  


# 2. CANCEL ENDPOINT TESTS 

def test_cancel_other_patient_appointment_forbidden(api_client, patient_user, other_patient_user, doctor, valid_slot):
    """A patient must not be allowed to cancel someone else's appointment."""
    owner_profile = Patient.objects.get(user=patient_user)
    
    appointment = Appointment.objects.create(
        doctor=doctor,
        patient=owner_profile,
        slot_time=valid_slot,
        status=Appointment.Status.CONFIRMED
    )

    token = AccessToken.for_user(other_patient_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.patch(f"/api/v1/appointments/{appointment.id}/cancel/", {
        "reason": "Intruder request"
    })
    assert response.status_code == 403


# 3. AVAILABILITY ENDPOINT (PUBLIC) 

def test_get_availability_anonymous_allowed(api_client, doctor, valid_slot):
    """Checking schedule availability does not require credentials."""
    date_str = valid_slot.date().isoformat()
    response = api_client.get(f"/api/v1/doctors/{doctor.id}/availability/?date={date_str}")
    assert response.status_code == 200
    assert "available_slots" in response.data