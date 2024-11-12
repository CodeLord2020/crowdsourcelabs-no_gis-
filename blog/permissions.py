from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Custom permission to grant full access to authenticated users
    and read-only access to unauthenticated users.
    """
    def has_permission(self, request, view):
        # Allow all read-only requests
        if request.method in SAFE_METHODS:
            return True

        # Only allow authenticated users for other requests
        return request.user and request.user.is_authenticated
