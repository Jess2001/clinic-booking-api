from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time, timedelta
from appointments.models import Doctor, Patient, Appointment

class Command(BaseCommand):
    help = "Seeds the database with initial doctors, patients, and test slots."

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # 1. Clean up existing test data to avoid unique constraint crashes
        Appointment.objects.all().delete()
        Doctor.objects.all().delete()
        Patient.objects.all().delete()
        User.objects.filter(username__in=["patient_kamau", "patient_atieno"]).delete()

        # 2. Create Doctors
        dr_alice = Doctor.objects.create(
            full_name="Dr. Alice Mwangi",
            email="alice.mwangi@clinic.com",
            specialization="Cardiology",
            opening_hours=time(8, 0),
            closing_hours=time(17, 0)
        )

        dr_bob = Doctor.objects.create(
            full_name="Dr. Bob Otieno",
            email="bob.otieno@clinic.com",
            specialization="Pediatrics",
            opening_hours=time(9, 0),
            closing_hours=time(16, 0)
        )

        # 3. Create Patient Users
        user1 = User.objects.create_user(
            username="patient_kamau",
            first_name="John",
            last_name="Kamau",
            password="securepassword123"
        )
        patient_kamau = Patient.objects.create(user=user1)

        user2 = User.objects.create_user(
            username="patient_atieno",
            first_name="Grace",
            last_name="Atieno",
            password="securepassword123"
        )
        patient_atieno = Patient.objects.create(user=user2)

        # 4. Create an existing booked appointment for tomorrow so we can test "taken" slots
        tomorrow = (timezone.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        
        Appointment.objects.create(
            doctor=dr_alice,
            patient=patient_kamau,
            slot_time=tomorrow,
            status=Appointment.Status.CONFIRMED
        )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
        self.stdout.write(f"Created Doctor: {dr_alice.full_name} (ID: {dr_alice.id})")
        self.stdout.write(f"Created Doctor: {dr_bob.full_name} (ID: {dr_bob.id})")
        self.stdout.write(f"Created Patient: {patient_kamau.user.first_name} (ID: {patient_kamau.id})")
        self.stdout.write(f"Created Patient: {patient_atieno.user.first_name} (ID: {patient_atieno.id})")