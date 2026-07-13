from rest_framework import serializers
from .models import Appointment, Doctor, Patient

class DoctorPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        # Absolute PII Isolation: No phone or internal personal emails exposed.
        fields = ['id', 'full_name', 'work_start', 'work_end']


class PatientPublicSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'full_name']


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_details = DoctorPublicSerializer(source='doctor', read_only=True)
    patient_details = PatientPublicSerializer(source='patient', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_details', 'patient', 'patient_details', 
            'slot_time', 'status', 'cancellation_reason'
        ]
        read_only_fields = ['id', 'status', 'cancellation_reason']