from rest_framework import permissions

class IsAppointmentOwner(permissions.BasePermission):
    """
    Custom permission to only allow patients to access/edit their own appointments.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
            
        try:
            return obj.patient == request.user.patient
        except AttributeError:
            return False