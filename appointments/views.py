from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .serializers import AppointmentSerializer
from .services import BookingService
from .selectors import AvailabilitySelector
from .models import Appointment, Patient
from .permissions import IsAppointmentOwner


class AppointmentViewSet(ViewSet):
    """
    Handles booking, cancellation, and rescheduling.
    /api/v1/appointments/ -> POST (create)
    /api/v1/appointments/{id}/cancel/ -> PATCH
    /api/v1/appointments/{id}/reschedule/ -> PATCH
    """
    permission_classes = [IsAuthenticated]

    def create(self, request):
        """POST /appointments/ - Book a new slot."""
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response(
                {"error": "Authenticated user does not have a registered patient profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            appointment = BookingService.create_appointment(
                doctor_id=serializer.validated_data['doctor'].id,
                patient_id=patient.id,
                slot_time=serializer.validated_data['slot_time']
            )
            return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='cancel', permission_classes=[IsAuthenticated, IsAppointmentOwner])
    def cancel(self, request, pk=None):
        """PATCH /appointments/{id}/cancel/ - Cancel an appointment."""
        appointment = get_object_or_404(Appointment, pk=pk)
        self.check_object_permissions(request, appointment)

        reason = request.data.get('reason')
        try:
            cancelled_appointment = BookingService.cancel_appointment(appointment_id=appointment.id, reason=reason)
            return Response(AppointmentSerializer(cancelled_appointment).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='reschedule', permission_classes=[IsAuthenticated, IsAppointmentOwner])
    def reschedule(self, request, pk=None):
        """PATCH /appointments/{id}/reschedule/ - Move appointment to a new slot."""
        appointment = get_object_or_404(Appointment, pk=pk)
        self.check_object_permissions(request, appointment)

        new_slot_time_str = request.data.get('new_slot_time')
        if not new_slot_time_str:
            return Response({"error": "Missing 'new_slot_time' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_slot_time = datetime.fromisoformat(new_slot_time_str.replace('Z', '+00:00'))
            new_appointment = BookingService.reschedule_appointment(appointment_id=appointment.id, new_slot_time=new_slot_time)
            return Response(AppointmentSerializer(new_appointment).data, status=status.HTTP_200_OK)
        except (ValueError, ValidationError) as e:
            msg = str(e.message) if hasattr(e, 'message') else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class DoctorViewSet(ViewSet):
    """
    Handles doctor-specific operations.
    /api/v1/doctors/{id}/availability/ -> GET
    """
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'], url_path='availability')
    def availability(self, request, pk=None):
        """GET /doctors/{id}/availability/?date=YYYY-MM-DD"""
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "Missing 'date' query parameter. Use YYYY-MM-DD format."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slots = AvailabilitySelector.get_available_slots(doctor_id=pk, target_date=target_date)
            return Response({
                "date": date_str,
                "available_slots": [slot.isoformat() for slot in slots]
            }, status=status.HTTP_200_OK)
        except (ValueError, ValidationError) as e:
            msg = str(e.message) if hasattr(e, 'message') else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class PatientViewSet(ViewSet):
    """
    Handles patient-specific operations.
    /api/v1/patients/{id}/appointments/ -> GET
    """
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='appointments')
    def appointments(self, request, pk=None):
        """GET /patients/{id}/appointments/ - Upcoming appointments for the patient."""
        try:
            patient = Patient.objects.get(user=request.user)
            if patient.id != int(pk):
                return Response({"error": "You do not have permission to view other patients' appointments."}, status=status.HTTP_403_FORBIDDEN)
        except Patient.DoesNotExist:
            return Response({"error": "Patient profile not found."}, status=status.HTTP_403_FORBIDDEN)

        appointments = AvailabilitySelector.get_patient_appointments(patient_id=pk)
        return Response(AppointmentSerializer(appointments, many=True).data, status=status.HTTP_200_OK)