from django.contrib import admin
from appointments.models import Doctor, Patient, Appointment

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "specialization", "opening_hours", "closing_hours")
    search_fields = ("full_name", "email", "specialization")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "get_username", "get_email", "get_full_name")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")

    # Helper methods to display details from the linked User model cleanly
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = "Username"

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "Full Name"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "patient", "slot_time", "status", "cancel_reason")
    list_filter = ("status", "slot_time", "doctor")
    search_fields = ("doctor__full_name", "patient__user__first_name", "patient__user__last_name")