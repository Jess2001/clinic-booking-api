import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta, time
from appointments.models import Doctor, Patient, Appointment

pytestmark = pytest.mark.django_db


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
def patient():
    user = User.objects.create_user(
        username="patient1",
        password="testpass123",
        first_name="John",
        last_name="Kamau"
    )
    return Patient.objects.create(user=user)


@pytest.fixture
def slot_time():
    return (timezone.now() + timedelta(days=1)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )


def test_doctor_str(doctor):
    assert str(doctor) == "Dr. Alice Mwangi"


def test_doctor_email_unique(doctor):
    with pytest.raises(IntegrityError):
        Doctor.objects.create(
            full_name="Bob Otieno",
            email="alice@clinic.com",
            specialization="Neurology",
            opening_hours=time(8, 0),
            closing_hours=time(17, 0)
        )


def test_unique_constraint_prevents_double_booking(doctor, patient, slot_time):
    Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        slot_time=slot_time,
        status=Appointment.Status.CONFIRMED
    )
    with pytest.raises(IntegrityError):
        Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            slot_time=slot_time,
            status=Appointment.Status.CONFIRMED
        )


def test_cancelled_slot_can_be_rebooked(doctor, patient, slot_time):
    Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        slot_time=slot_time,
        status=Appointment.Status.CANCELLED
    )
    appointment = Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        slot_time=slot_time,
        status=Appointment.Status.CONFIRMED
    )
    assert appointment.status == Appointment.Status.CONFIRMED