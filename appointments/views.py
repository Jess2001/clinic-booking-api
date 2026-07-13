from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AppointmentSerializer
from .services import BookingService
from .selectors import AvailabilitySelector
from .models import Appointment

class AppointmentBookView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            appointment = BookingService.create_appointment(
                doctor_id=serializer.validated_data['doctor'].id,
                patient_id=serializer.validated_data['patient'].id,
                slot_time=serializer.validated_data['slot_time']
            )
            return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"error": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)


class DoctorAvailabilityView(APIView):
    def get(self, request, id, *args, **kwargs):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "Missing 'date' query parameter. Use YYYY-MM-DD format."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            slots = AvailabilitySelector.get_available_slots(doctor_id=id, target_date=target_date)
            return Response({
                "date": date_str,
                "available_slots": [slot.isoformat() for slot in slots]
            }, status=status.HTTP_200_OK)
        except (ValueError, ValidationError) as e:
            msg = str(e.message) if hasattr(e, 'message') else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class AppointmentCancelView(APIView):
    def patch(self, request, id, *args, **kwargs):
        reason = request.data.get('reason')
        try:
            appointment = BookingService.cancel_appointment(appointment_id=id, reason=reason)
            return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)


class AppointmentRescheduleView(APIView):
    def patch(self, request, id, *args, **kwargs):
        new_slot_time_str = request.data.get('new_slot_time')
        if not new_slot_time_str:
            return Response({"error": "Missing 'new_slot_time' parameter."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Standardize string representations containing absolute 'Z' layouts to standard offsets
            new_slot_time = datetime.fromisoformat(new_slot_time_str.replace('Z', '+00:00'))
            new_appointment = BookingService.reschedule_appointment(appointment_id=id, new_slot_time=new_slot_time)
            return Response(AppointmentSerializer(new_appointment).data, status=status.HTTP_200_OK)
        except (ValueError, ValidationError) as e:
            msg = str(e.message) if hasattr(e, 'message') else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)


class PatientAppointmentsListView(APIView):
    """
    Return upcoming appointments sorted chronologically for a patient.
    """
    def get(self, request, id, *args, **kwargs):
        appointments = Appointment.objects.filter(
            patient_id=id,
            status=Appointment.Status.CONFIRMED,
            slot_time__gte=timezone.now()
        ).order_by('slot_time')
        return Response(AppointmentSerializer(appointments, many=True).data, status=status.HTTP_200_OK)