from django.urls import path
from .views import (
    AppointmentBookView, 
    DoctorAvailabilityView, 
    AppointmentCancelView, 
    AppointmentRescheduleView,
    PatientAppointmentsListView
)
from django.http import JsonResponse
def api_v1_index(request):
    return JsonResponse({
        "status": "active",
        "version": "v1.0.0",
        "description": "Clinic Booking System API Gateway",
        "endpoints": {
            "book_appointment": "/api/v1/appointments/",
            "doctor_availability": "/api/v1/doctors/<id>/availability/?date=YYYY-MM-DD",
            "cancel_appointment": "/api/v1/appointments/<id>/cancel/",
            "reschedule_appointment": "/api/v1/appointments/<id>/reschedule/",
            "patient_upcoming_appointments": "/api/v1/patients/<id>/appointments/"
        }
    })
urlpatterns = [
    path("", api_v1_index, name="api-v1-index"),
    path('appointments/', AppointmentBookView.as_view(), name='appointment-book'),
    path('doctors/<int:id>/availability/', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('appointments/<int:id>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    path('appointments/<int:id>/reschedule/', AppointmentRescheduleView.as_view(), name='appointment-reschedule'),
    path('patients/<int:id>/appointments/', PatientAppointmentsListView.as_view(), name='patient-appointments-list'),
]