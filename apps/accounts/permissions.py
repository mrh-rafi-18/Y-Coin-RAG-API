from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Allows access only to authenticated users who have the 'admin' role.
    """
    message = "You do not have permission to perform this action. Admin access required."

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == "admin"
        )