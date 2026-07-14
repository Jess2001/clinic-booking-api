import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from appointments.models import Doctor, Patient, Appointment
from appointments.services import BookingService

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def doctor(db):
    return Doctor.objects.create(
        full_name="Alice Mwangi",
        email="alice@clinic.com",
        specialization="Cardiology",
        opening_hours=time(8, 0),
        closing_hours=time(17, 0)
    )


@pytest.fixture
def patient(db):
    user = User.objects.create_user(
        username="patient1",
        password="testpass123"
    )
    return Patient.objects.create(user=user)


def test_concurrent_booking_only_one_succeeds(doctor, patient):
    """
    Simulates 5 simultaneous booking requests for the same slot.
    Only one must succeed — proves select_for_update + UniqueConstraint works.
    """
    slot_time = (timezone.now() + timedelta(hours=3)).replace(
        minute=0, second=0, microsecond=0
    )

    successes = []
    failures = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                BookingService.create_appointment,
                doctor.id,
                patient.id,
                slot_time
            )
            for _ in range(5)
        ]

        for future in as_completed(futures):
            try:
                result = future.result()
                successes.append(result)
            except Exception as e:
                failures.append(e)

    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
    assert len(failures) == 4, f"Expected 4 failures, got {len(failures)}"

    #  only one confirmed appointment  in DB
    confirmed_count = Appointment.objects.filter(
        doctor=doctor,
        slot_time=slot_time,
        status=Appointment.Status.CONFIRMED
    ).count()
    assert confirmed_count == 1