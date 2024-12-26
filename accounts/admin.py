from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import User, Role, UserRole, UserLocation
from django.utils.html import format_html


class UserLocationAdmin(admin.ModelAdmin):
    """Admin configuration for UserLocation without GIS features."""
    list_display = ('user', 'location_display', 'location_accuracy', 'location_updated_at', 'device_info_summary')
    list_filter = ('location_updated_at',)
    search_fields = ('user__email', 'address')
    ordering = ['-location_updated_at']
    readonly_fields = ('location_display', 'location_updated_at', 'device_info_summary')

    def location_display(self, obj):
        """Display location coordinates."""
        if obj.coordinates:
            return f"Lat: {obj.coordinates[0]}, Lon: {obj.coordinates[1]}"
        return "Location not set"
    location_display.short_description = "Coordinates"

    def device_info_summary(self, obj):
        """Display a summary of the device information."""
        return format_html("<pre>{}</pre>", obj.device_info) if obj.device_info else "No device info available"
    device_info_summary.short_description = "Device Information"

    def get_queryset(self, request):
        """Optimize queryset by selecting related user fields."""
        return super().get_queryset(request).select_related('user')

    fieldsets = (
        (None, {
            'fields': ('user', 'location', 'location_display', 'location_accuracy', 'location_updated_at')
        }),
        ('Device Information', {
            'fields': ('device_info_summary',),
        }),
    )


class UserRoleInline(admin.TabularInline):
    """Inline for managing roles assigned to a user."""
    model = UserRole
    extra = 1
    autocomplete_fields = ['role']
    fk_name = "user"
    fields = ('role', 'is_active', 'assigned_at')
    readonly_fields = ('assigned_at',)
    verbose_name = _('User Role Assignment')
    verbose_name_plural = _('User Role Assignments')


class UserRoleAssignedByInline(admin.TabularInline):
    """Inline for managing roles assigned by a user."""
    model = UserRole
    fk_name = "assigned_by"
    extra = 1
    autocomplete_fields = ['role']
    fields = ('assigned_by', 'role', 'is_active', 'assigned_at')
    readonly_fields = ('assigned_at',)
    verbose_name = _('Role Assigned By')
    verbose_name_plural = _('Roles Assigned By')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin configuration for User model."""
    list_display = ('full_name', 'email', 'is_active', 'is_verified', 'last_active', 'is_online')
    list_filter = ('is_active', 'is_verified')
    search_fields = ('first_name', 'last_name', 'username', 'email')
    ordering = ('email',)
    readonly_fields = ('verification_token', 'last_active', 'is_online')
    fieldsets = (
        (None, {
            'fields': ('email', 'first_name', 'last_name', 'username', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('phone_number', 'date_of_birth', 'bio', 'profile_picture', 'emergency_contact', 'emergency_phone')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_verified', 'last_active', 'is_online')
        }),
        (_('Verification'), {
            'fields': ('verification_token',)
        }),
    )
    inlines = [UserRoleInline, UserRoleAssignedByInline]

    def is_online(self, obj):
        """Display online status based on last_active time."""
        return obj.is_online
    is_online.boolean = True
    is_online.short_description = 'Online Status'

    actions = ['deactivate_users', 'verify_users']

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected users have been deactivated.")

    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, "Selected users have been verified.")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin configuration for Role model."""
    list_display = ('role_type', 'description', 'created_at', 'updated_at')
    search_fields = ('role_type',)
    list_filter = ('created_at',)
    ordering = ('role_type',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin configuration for UserRole model."""
    list_display = ('user', 'role', 'assigned_by', 'is_active', 'assigned_at')
    list_filter = ('role', 'is_active')
    search_fields = ('user__email', 'role__role_type', 'assigned_by__email')
    ordering = ('assigned_at',)
    autocomplete_fields = ['user', 'role', 'assigned_by']

    actions = ['deactivate_roles']

    def deactivate_roles(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected role assignments have been deactivated.")

    def get_queryset(self, request):
        """Optimize queryset for better performance with select_related."""
        return super().get_queryset(request).select_related('user', 'role', 'assigned_by')


# Register the model with custom admin class
admin.site.register(UserLocation, UserLocationAdmin)
