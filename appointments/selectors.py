from datetime import datetime, date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Doctor, Appointment


class AvailabilitySelector:
    """
    Handles read-only domain queries.
    Generates free 30-minute slots by comparing doctor's schedule against existing bookings.
    """

    @staticmethod
    def get_available_slots(doctor_id: int, target_date: date) -> list[datetime]:
        """
        Returns list of available UTC datetimes for a doctor on a given date.
        """
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            raise ValidationError("The requested doctor does not exist.")

        start_dt = datetime.combine(target_date, doctor.opening_hours, tzinfo=timezone.utc)
        end_dt = datetime.combine(target_date, doctor.closing_hours, tzinfo=timezone.utc)

        booked_slots = set(
            Appointment.objects.filter(
                doctor=doctor,
                slot_time__date=target_date,
                status=Appointment.Status.CONFIRMED
            ).values_list('slot_time', flat=True)
        )

        available_slots = []
        current_cursor = start_dt

        while current_cursor < end_dt:
            if current_cursor not in booked_slots:
                available_slots.append(current_cursor)
            current_cursor += timedelta(minutes=30)

        return available_slots

    @staticmethod
    def get_patient_appointments(patient_id: int):
        """
        Returns upcoming confirmed appointments for a patient, sorted chronologically.
        """
        return Appointment.objects.filter(
            patient_id=patient_id,
            status=Appointment.Status.CONFIRMED,
            slot_time__gte=timezone.now()
        ).order_by('slot_time').select_related('doctor', 'patient')