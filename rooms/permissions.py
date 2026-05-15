from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Admin-only permission.
    Requires the request to be authenticated AND the user to have admin role
    (via Client.role == 'admin' or Django is_staff).
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Check Client profile role
        try:
            if hasattr(user, 'client') and user.client.role == 'admin':
                return True
        except Exception:
            pass
        return bool(user.is_staff)
