from django.urls import path
from .views import (
    AppointmentBookView, 
    DoctorAvailabilityView, 
    AppointmentCancelView, 
    AppointmentRescheduleView,
    PatientAppointmentsListView
)

urlpatterns = [
    path('appointments/', AppointmentBookView.as_view(), name='appointment-book'),
    path('doctors/<int:id>/availability/', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('appointments/<int:id>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    path('appointments/<int:id>/reschedule/', AppointmentRescheduleView.as_view(), name='appointment-reschedule'),
    path('patients/<int:id>/appointments/', PatientAppointmentsListView.as_view(), name='patient-appointments-list'),
]