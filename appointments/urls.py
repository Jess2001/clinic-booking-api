from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from .views import AppointmentViewSet, DoctorViewSet, PatientViewSet

# Initialize the Router
router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'patients', PatientViewSet, basename='patient')

# Keep your index for convenience
def api_v1_index(request):
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
    path("", api_v1_index, name="api-v1-index"),
    path('', include(router.urls)) ]