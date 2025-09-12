from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Allow reads for anyone; writes only for admin role or staff."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # If linked Client has role 'admin' or Django is_staff
        try:
            if hasattr(user, 'client') and user.client.role == 'admin':
                return True
        except Exception:
            pass
        return bool(user.is_staff)
