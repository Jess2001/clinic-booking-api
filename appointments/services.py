from datetime import datetime, timedelta
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Doctor, Patient, Appointment


class BookingService:
    """
    Handles write-only domain mutations, state changes,
    validates business constraints, and ensures concurrency control.
    """

    @staticmethod
    def validate_slot_constraints(doctor: Doctor, slot_time: datetime):
        """
        Validation logic for appointment slot constraints.
        Ensures proper timezone awareness before comparing.
        """
        # 1. Force slot_time to be timezone-aware 
        if timezone.is_naive(slot_time):
            slot_time = timezone.make_aware(slot_time, timezone.get_current_timezone())
        else:
            slot_time = timezone.localtime(slot_time)

        now = timezone.now()

        # Past and advance booking checks
        if slot_time < now:
            raise ValidationError("Cannot book an appointment slot in the past.")

        if slot_time < now + timedelta(hours=1):
            raise ValidationError("Appointments must be booked at least 1 hour in advance.")

        if slot_time.minute not in [0, 30] or slot_time.second != 0 or slot_time.microsecond != 0:
            raise ValidationError("Appointment slots must align exactly to a 30-minute interval.")

        target_time = slot_time.time()
        if not (doctor.opening_hours <= target_time < doctor.closing_hours):
            raise ValidationError(
                f"The requested slot falls outside Dr. {doctor.full_name}'s "
                f"working hours ({doctor.opening_hours} - {doctor.closing_hours})."
            )

    @classmethod
    @transaction.atomic
    def create_appointment(cls, doctor_id: int, patient_id: int, slot_time: datetime) -> Appointment:
        """
        Locks the doctor row, validates constraints, and commits a confirmed booking atomically.
        """
        try:
            doctor = Doctor.objects.select_for_update().get(id=doctor_id)
        except Doctor.DoesNotExist:
            raise ValidationError("The requested doctor record does not exist.")

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            raise ValidationError("The requested patient record does not exist.")

        # Normalize to aware datetime before running constraints or querying
        if timezone.is_naive(slot_time):
            slot_time = timezone.make_aware(slot_time, timezone.get_current_timezone())

        cls.validate_slot_constraints(doctor, slot_time)

        if Appointment.objects.filter(
            doctor=doctor,
            slot_time=slot_time,
            status=Appointment.Status.CONFIRMED
        ).exists():
            raise ValidationError("This appointment slot is already taken.")

        try:
            return Appointment.objects.create(
                doctor=doctor,
                patient=patient,
                slot_time=slot_time,
                status=Appointment.Status.CONFIRMED
            )
        except IntegrityError:
            raise ValidationError("Concurrency conflict: This slot was just reserved by another user.")

    @classmethod
    @transaction.atomic
    def cancel_appointment(cls, appointment_id: int, reason: str) -> Appointment:
        """
        Cancels an active reservation with a required audit reason.
        """
        if not reason or not reason.strip():
            raise ValidationError("A cancellation reason must be provided.")

        try:
            appointment = Appointment.objects.select_for_update().get(id=appointment_id)
        except Appointment.DoesNotExist:
            raise ValidationError("Appointment record not found.")

        if appointment.status == Appointment.Status.CANCELLED:
            raise ValidationError("This appointment has already been cancelled.")

        appointment.status = Appointment.Status.CANCELLED
        appointment.cancel_reason = reason
        appointment.save()
        return appointment

    @classmethod
    @transaction.atomic
    def reschedule_appointment(cls, appointment_id: int, new_slot_time: datetime) -> Appointment:
        """
        Moves a reservation to a new slot.
        Original slot is freed only if new slot is successfully acquired.
        """
        try:
            appointment = Appointment.objects.select_for_update().get(id=appointment_id)
        except Appointment.DoesNotExist:
            raise ValidationError("Appointment record not found.")

        if appointment.status == Appointment.Status.CANCELLED:
            raise ValidationError("Cannot reschedule a cancelled appointment.")

        doctor = Doctor.objects.select_for_update().get(id=appointment.doctor_id)

        # Normalize the new slot time to be timezone-aware
        if timezone.is_naive(new_slot_time):
            new_slot_time = timezone.make_aware(new_slot_time, timezone.get_current_timezone())

        cls.validate_slot_constraints(doctor, new_slot_time)

        if Appointment.objects.filter(
            doctor=doctor,
            slot_time=new_slot_time,
            status=Appointment.Status.CONFIRMED
        ).exclude(id=appointment.id).exists():
            raise ValidationError("The target slot is already taken.")

        try:
            appointment.status = Appointment.Status.RESCHEDULED
            appointment.save()

            return Appointment.objects.create(
                doctor=doctor,
                patient=appointment.patient,
                slot_time=new_slot_time,
                status=Appointment.Status.CONFIRMED
            )
        except IntegrityError:
            raise ValidationError("Concurrency conflict: The target slot was taken during rescheduling.")