from rest_framework import permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from typing import Any



class BaseRolePermission(permissions.BasePermission):
    """Base class for role-based permissions"""
    required_role = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_role(self.required_role)
    


class SuperAdminPermission(BaseRolePermission):
    required_role = 'SUPERADMIN'



class AdminPermission(BaseRolePermission):
    required_role = 'ADMIN'
    
    def has_permission(self, request, view):
        return (super().has_permission(request, view) or 
                request.user.has_role('SUPERADMIN'))
    


class ResponderPermission(BaseRolePermission):
    required_role = 'RESPONDER'
    
    def has_object_permission(self, request, view, obj: Any) -> bool:
        if request.user.has_role('ADMIN') or request.user.has_role('SUPERADMIN'):
            return True
        if hasattr(obj, 'responder'):
            return obj.responder.user == request.user
        return False



class VolunteerPermission(BaseRolePermission):
    required_role = 'VOLUNTEER'
    
    def has_object_permission(self, request, view, obj: Any) -> bool:
        if request.user.has_role('ADMIN') or request.user.has_role('SUPERADMIN'):
            return True
        if hasattr(obj, 'volunteer'):
            return obj.volunteer.user == request.user
        return False
    


class ReporterPermission(BaseRolePermission):
    required_role = 'REPORTER'
    
    def has_object_permission(self, request, view, obj: Any) -> bool:
        if request.user.has_role('ADMIN') or request.user.has_role('SUPERADMIN'):
            return True
        if hasattr(obj, 'reporter'):
            return obj.reporter.user == request.user
        return False
    

# class CustomModelPermissions:
#     """Helper class to create custom model permissions"""
#     @staticmethod
#     def create_custom_permissions():
#         """Create custom permissions for all roles"""
#         content_type = ContentType.objects.get_for_model(Permission)
        
#         custom_permissions = [
#             # Volunteer permissions
#             ('can_view_emergency_contacts', 'Can view emergency contacts'),
#             ('can_update_availability', 'Can update availability status'),
#             ('can_join_mission', 'Can join rescue mission'),
            
#             # Responder permissions
#             ('can_create_incident_report', 'Can create incident report'),
#             ('can_update_incident_status', 'Can update incident status'),
#             ('can_coordinate_volunteers', 'Can coordinate volunteers'),
            
#             # Reporter permissions
#             ('can_submit_report', 'Can submit incident report'),
#             ('can_update_report', 'Can update submitted report'),
#             ('can_view_report_status', 'Can view report status'),
            
#             # Admin permissions
#             ('can_manage_users', 'Can manage user accounts'),
#             ('can_assign_roles', 'Can assign roles to users'),
#             ('can_verify_skills', 'Can verify volunteer skills'),
            
#             # Super Admin permissions
#             ('can_manage_system', 'Can manage system settings'),
#             ('can_view_analytics', 'Can view system analytics'),
#             ('can_manage_permissions', 'Can manage user permissions'),
#         ]
        
#         for codename, name in custom_permissions:
#             Permission.objects.get_or_create(
#                 codename=codename,
#                 name=name,
#                 content_type=content_type,
#             )

# # Decorator for view-level permission checks
# def role_required(roles):
#     """
#     Decorator to check if user has any of the required roles
    
#     Usage:
#     @role_required(['ADMIN', 'SUPERADMIN'])
#     def my_view(request):
#         pass
#     """
#     def decorator(view_func):
#         def _wrapped_view(request, *args, **kwargs):
#             if not request.user.is_authenticated:
#                 return redirect('login')
            
#             user_roles = request.user.get_roles()
#             if not any(role in user_roles for role in roles):
#                 raise PermissionDenied
                
#             return view_func(request, *args, **kwargs)
#         return _wrapped_view
#     return decorator