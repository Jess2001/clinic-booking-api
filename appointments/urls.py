from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from .views import AppointmentViewSet, DoctorViewSet, PatientViewSet

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'patients', PatientViewSet, basename='patient')

def api_status(request):
    return JsonResponse({
        "status": "active",
        "version": "v1.0.0",
        "description": "Clinic Booking System API Gateway",
        "endpoints": {
            "book_appointment": "/api/v1/appointments/ (POST)",
            "doctor_availability": "/api/v1/doctors/{id}/availability/?date=YYYY-MM-DD (GET)",
            "cancel_appointment": "/api/v1/appointments/{id}/cancel/ (PATCH)",
            "reschedule_appointment": "/api/v1/appointments/{id}/reschedule/ (PATCH)",
            "patient_upcoming_appointments": "/api/v1/patients/{id}/appointments/ (GET)"
        }
    })

urlpatterns = [
    path('', include(router.urls)),
    path('status/', api_status, name='api-status'),
]