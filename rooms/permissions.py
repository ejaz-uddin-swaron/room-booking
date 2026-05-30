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


class IsTenant(BasePermission):
    """
    Tenant-only permission.
    Requires authenticated user with Client.role == 'tenant'.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return hasattr(user, 'client') and user.client.role == 'tenant'
        except Exception:
            return False


class IsAdminOrTenant(BasePermission):
    """
    Admin or Tenant permission.
    Allows access to authenticated users with either admin or tenant role.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        try:
            return hasattr(user, 'client') and user.client.role in ('admin', 'tenant')
        except Exception:
            return False


class IsPublicReadOnly(BasePermission):
    """
    Allow unauthenticated GET/HEAD/OPTIONS requests (public read).
    Write operations require authentication.
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        if request.method in self.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)
