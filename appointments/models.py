from django.db import models
from django.db.models import Q
from django.conf import settings
class AppointmentStatus(models.TextChoices):
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CANCELED = 'CANCELED', 'Canceled'
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'


class Doctor(models.Model):
        full_name = models.CharField(max_length=100)
        email = models.EmailField(unique=True)
        specialization = models.CharField(max_length=100)
        opening_hours = models.TimeField()
        closing_hours = models.TimeField()

        def __str__(self):
                return self.full_name


class Patient(models.Model):
    """
    Acts as a domain-specific profile extension of the core User identity.
    Ensures structural separation between authentication credentials and patient business logic.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_profile',
        help_text="Link to the underlying Django authentication user record."
    )
    # Future clinical extensions (e.g., insurance_policy_number, date_of_birth) belong here.

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"


class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='appointments')
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='appointments')
    slot_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.CONFIRMED)
    cancel_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    class Meta:
        ordering = ['slot_time']
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'slot_time'],condition=Q(status='CONFIRMED'), name='unique_appointment')
        ]

    def __str__(self):
        return f"{self.patient} with Dr. {self.doctor} at {self.slot_time}"