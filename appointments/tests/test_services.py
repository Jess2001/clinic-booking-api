import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, time
from appointments.models import Doctor, Patient, Appointment
from appointments.services import BookingService

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
def valid_slot():
    return (timezone.now() + timedelta(hours=2)).replace(
        minute=0, second=0, microsecond=0
    )


def test_book_valid_appointment(doctor, patient, valid_slot):
    appointment = BookingService.create_appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        slot_time=valid_slot
    )
    assert appointment.id is not None
    assert appointment.status == Appointment.Status.CONFIRMED


def test_book_appointment_in_past_raises_error(doctor, patient):
    past_time = timezone.now() - timedelta(hours=1)
    with pytest.raises(ValidationError, match="Cannot book an appointment slot in the past"):
        BookingService.create_appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            slot_time=past_time
        )


def test_book_within_one_hour_raises_error(doctor, patient):
    invalid_time = (timezone.now() + timedelta(minutes=30)).replace(
        second=0, microsecond=0
    )
    with pytest.raises(ValidationError, match="at least 1 hour in advance"):
        BookingService.create_appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            slot_time=invalid_time
        )


def test_book_outside_working_hours_raises_error(doctor, patient):
    late_slot = (timezone.now() + timedelta(days=1)).replace(
        hour=20, minute=0, second=0, microsecond=0
    )
    with pytest.raises(ValidationError, match="working hours"):
        BookingService.create_appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            slot_time=late_slot
        )


def test_book_misaligned_slot_raises_error(doctor, patient):
    bad_slot = (timezone.now() + timedelta(hours=2)).replace(
        minute=15, second=0, microsecond=0
    )
    with pytest.raises(ValidationError, match="30-minute interval"):
        BookingService.create_appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            slot_time=bad_slot
        )


def test_double_booking_raises_error(doctor, patient, valid_slot):
    BookingService.create_appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        slot_time=valid_slot
    )
    with pytest.raises(ValidationError, match="already taken"):
        BookingService.create_appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            slot_time=valid_slot
        )


def test_cancel_appointment(doctor, patient, valid_slot):
    appointment = BookingService.create_appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        slot_time=valid_slot
    )
    cancelled = BookingService.cancel_appointment(
        appointment_id=appointment.id,
        reason="Patient request"
    )
    assert cancelled.status == Appointment.Status.CANCELLED
    assert cancelled.cancel_reason == "Patient request"


def test_cancel_already_cancelled_raises_error(doctor, patient, valid_slot):
    appointment = BookingService.create_appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        slot_time=valid_slot
    )
    BookingService.cancel_appointment(
        appointment_id=appointment.id,
        reason="First cancellation"
    )
    with pytest.raises(ValidationError, match="already been cancelled"):
        BookingService.cancel_appointment(
            appointment_id=appointment.id,
            reason="Second cancellation"
        )


def test_reschedule_appointment(doctor, patient, valid_slot):
    appointment = BookingService.create_appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        slot_time=valid_slot
    )
    new_slot = valid_slot + timedelta(hours=1)
    new_appointment = BookingService.reschedule_appointment(
        appointment_id=appointment.id,
        new_slot_time=new_slot
    )
    assert new_appointment.status == Appointment.Status.CONFIRMED
    assert new_appointment.slot_time == new_slot

    # Original appointment should be RESCHEDULED
    original = Appointment.objects.get(id=appointment.id)
    assert original.status == Appointment.Status.RESCHEDULED